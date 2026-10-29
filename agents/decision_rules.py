"""Provenance-carrying facts and conservative deterministic V3 decisions."""
from __future__ import annotations
import ast
import difflib
import re
from ingestion.models import DecisionV3,FactSource,FactsV3,SourcedFact,digest

MARKERS=re.compile(r'\b(?:must|always|never|precondition|invariant|default|returns|raises|deprecated)\b',re.I)

def _source(a, revision, method):
    from rag.evidence import evidence
    e=evidence(a,method)
    return FactSource(revision=revision,commit_id=a.commit_id,path=a.file_path,
        start_line=e['start_line'],end_line=e['end_line'],content_hash=a.content_hash,
        extraction_method=method,artifact_role=('requirement' if a.artifact_type=='requirement'
        else 'test' if a.artifact_type in {'test','test_method'} else 'consumer'
        if a.artifact_type=='api_caller' else 'implementation'),evidence_id=e['evidence_id'])


def _known(value, sources):
    unique={s.evidence_id:s for s in sources};return SourcedFact(value=value,sources=list(unique.values()),unknown_reason=None)

def _unknown(reason):
    return SourcedFact.unknown(reason)

def _value(facts,name):
    return getattr(facts,name).value

def _literal_equal(a,b):
    if a is None or b is None:
        return None
    if type(a) is type(b) and a==b:
        return True
    def literal(value):
        if isinstance(value,str):
            try:return ast.literal_eval(value)
            except (ValueError,SyntaxError):return None
        return value
    left,right=literal(a),literal(b)
    return None if left is None or right is None else left==right

def _deleted_file_source(file_row,head_commit):
    if not file_row or not str(file_row.get('status','')).startswith('D') or not file_row.get('old_path'):
        return None
    patch=file_row.get('patch') or ''
    content_hash=digest('git-diff-deletion',file_row.get('status'),file_row['old_path'],patch)
    method='git_diff_deleted_file'
    return FactSource(revision='HEAD',commit_id=head_commit,path=file_row['old_path'],start_line=1,
        end_line=max(1,len(patch.splitlines())),content_hash=content_hash,extraction_method=method,
        artifact_role='implementation',evidence_id=digest(method,head_commit,file_row['old_path'],content_hash))

def _head_references(target,module_stem,after,own_path=None):
    hits=[];complete=True
    for item in after:
        if item.symbol or not item.file_path.endswith('.py'):
            continue
        if item.metadata.get('parse_error') or item.metadata.get('parse_has_error'):
            complete=False
            continue
        try:tree=ast.parse(item.content)
        except (SyntaxError,ValueError):
            complete=False
            continue
        imported=False
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.module and node.module.split('.')[-1]==module_stem:
                if any(alias.name==target for alias in node.names):
                    imported=True
            elif isinstance(node,ast.Import) and any(alias.name.split('.')[-1]==module_stem for alias in node.names):
                if item.file_path==own_path:
                    imported=True
        if imported:
            hits.append(item)
            continue
        if item.file_path!=own_path:
            continue
        rebound=any((isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and node.name==target)
            or (isinstance(node,ast.Name) and isinstance(node.ctx,ast.Store) and node.id==target)
            or (isinstance(node,ast.arg) and node.arg==target) for node in ast.walk(tree))
        if not rebound and any(isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id==target
                               for node in ast.walk(tree)):
            hits.append(item)
    return list({x.artifact_id:x for x in hits}.values()),complete

def _ids(*facts):
    return list(dict.fromkeys(s.evidence_id for f in facts for s in f.sources))

def _full_head(fact):
    return fact.value is True and {s.artifact_role for s in fact.sources if s.revision=='HEAD'} >= {'requirement','implementation','test'}

def extract_facts(changes, before, after, *, declared_links=(), obligation_registry=(),
                  authority_registry=(), subject_id=None):
    """Extract one change scope. No registry or parser evidence means unknown."""
    import ast
    import io
    import textwrap
    import tokenize
    from urllib.parse import urlsplit, parse_qs
    old = {a.artifact_id: a for a in before}
    head = {a.artifact_id: a for a in after}
    rows = changes.get('artifacts', [])
    row = next((r for r in rows if r['artifact_id'] == subject_id), None) if subject_id else None
    if row is None and len(rows) == 1:
        row = rows[0]
    if row is None:
        return FactsV3(evidence_sufficient=_unknown('A single artifact change scope is required'))
    a = old.get(row['artifact_id'])
    b = head.get(row.get('new_artifact_id') or row['artifact_id'])
    base_sources = [_source(a, 'BASE', 'snapshot_artifact')] if a else []
    head_sources = [_source(b, 'HEAD', 'snapshot_artifact')] if b else []
    base_file = next((x for x in before if a and x.file_path == a.file_path and not x.symbol), None)
    head_file = next((x for x in after if x.file_path == (b.file_path if b else row['file']) and not x.symbol), None)
    file_row = next((x for x in changes.get('files', []) if x.get('old_path') == row['file']), None)
    deletion_source = _deleted_file_source(file_row, changes.get('head_commit'))
    def parsed(x):
        return bool(x and not x.metadata.get('parse_error') and not x.metadata.get('parse_has_error'))
    scope_sources = base_sources + head_sources
    if head_file and not head_sources:
        scope_sources.append(_source(head_file, 'HEAD', 'head_snapshot_scope'))
    if deletion_source:
        scope_sources.append(deletion_source)
    refs = scope_sources
    head_scope_ok=bool(head_file and parsed(head_file))
    deleted_file_scope=bool(deletion_source and parsed(base_file))
    f = FactsV3(evidence_sufficient=_known(True, refs) if refs and (head_scope_ok or deleted_file_scope) else
                _unknown('Revision-correct HEAD source scope or deletion receipt is unavailable'))
    if not head_scope_ok and not deleted_file_scope:
        f.evidence_sufficient = _unknown('HEAD source scope is missing or parser status is incomplete')
        return f
    if base_file and not parsed(base_file):
        f.evidence_sufficient = _unknown('Parser failure in the applicable BASE file')
        return f
    if file_row and a and b:
        paired = [_source(a, 'BASE', 'diff'), _source(b, 'HEAD', 'diff')]
        comment_only = file_row.get('change_semantics') == 'COMMENT_ONLY'
        syntax_changed = bool(a.metadata.get('syntax_hash') and b.metadata.get('syntax_hash')
                              and a.metadata['syntax_hash'] != b.metadata['syntax_hash'])
        f.change_kind = _known('COMMENT_ONLY' if comment_only else 'AST' if syntax_changed else 'TEXT', paired)
        if comment_only:
            try:
                changed_comments = []
                for line in file_row.get('patch', '').splitlines():
                    if not line.startswith(('+', '-')) or line.startswith(('+++', '---')):
                        continue
                    source_line = line[1:]
                    changed_comments.extend(t.string for t in tokenize.generate_tokens(io.StringIO(source_line).readline)
                                            if t.type == tokenize.COMMENT)
                if file_row.get('patch') is None or not file_row.get('patch'):
                    f.comment_has_contract_markers = _unknown('Changed comment diff was not supplied')
                else:
                    f.comment_has_contract_markers = _known(bool(MARKERS.search('\n'.join(changed_comments))), paired)
            except (tokenize.TokenError, IndentationError):
                f.comment_has_contract_markers = _unknown('Changed-comment tokenization failed')
    if row['kind'] == 'renamed' and a and b:
        f.renamed_to = _known({'path': b.file_path, 'symbol': b.symbol}, refs)
    if row['kind'] == 'deleted' and a and a.artifact_type in {'function', 'method', 'test_method'}:
        def body_key(x):
            if x.metadata.get('language') != 'python':
                return None
            try:
                node = ast.parse(textwrap.dedent(x.content)).body[0]
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    return None
                node.name = '__rename_candidate__'
                return ast.dump(node, include_attributes=False)
            except (SyntaxError, IndexError):
                return None
        def similarity(x,y):
            left,right=body_key(x),body_key(y)
            return difflib.SequenceMatcher(None,left,right).ratio() if left and right else 0.0
        key = body_key(a)
        added = [head[r['artifact_id']] for r in rows if r['kind'] == 'added' and r['artifact_id'] in head
                 and head[r['artifact_id']].artifact_type == a.artifact_type]
        twins = [x for x in added if key and body_key(x) == key]
        if len(twins) == 1:
            f.renamed_to = _known({'path': twins[0].file_path, 'symbol': twins[0].symbol},
                                  base_sources + [_source(twins[0], 'HEAD', 'unique_ast_rename_candidate')])
        elif len(twins) > 1:
            f.renamed_to = _unknown('Multiple possible rename targets')
        elif any(similarity(a,x) >= 0.6 for x in added):
            f.renamed_to = _unknown('Similar added symbol may be a rename with edits')
        elif head_file:
            f.renamed_to = _known(False, base_sources + [_source(head_file, 'HEAD', 'changed_symbol_inventory_rename_search')])
        elif deletion_source:
            f.renamed_to = _known(False, base_sources + [deletion_source])
        else:
            f.renamed_to = _unknown('No complete HEAD rename search receipt')
        if head_file:
            deleted_source=_source(head_file, 'HEAD', 'parsed_symbol_absence')
        else:
            deleted_source=deletion_source
        if deleted_source:
            f.symbol_deleted_at_head = _known(True, base_sources + [deleted_source])
        hits,complete=_head_references(a.symbol,a.file_path.rsplit('/',1)[-1].rsplit('.',1)[0],after,
                                       head_file.file_path if head_file else None)
        if hits:
            f.head_refs_symbol = _known(True, [_source(x, 'HEAD', 'import_or_call_reference') for x in hits])
        elif complete and changes.get('head_reference_inventory_complete') is True:
            f.head_refs_symbol = _known(False, [_source(x, 'HEAD', 'complete_head_reference_inventory') for x in after if not x.symbol and x.file_path.endswith('.py')])
        else:
            f.head_refs_symbol = _unknown('No HEAD reference found; repository-wide reference inventory is not certified complete')
    if row['kind'] == 'deleted' and a and a.artifact_type in {'test', 'test_method'}:
        f.test_deleted = _known(True, base_sources)
    # Requirements/coverage are accepted only from an explicit reviewed, revision-bound registry.
    applicable = [r for r in obligation_registry if r.get('status') == 'APPROVED'
                  and r.get('subject_id') == row['artifact_id']
                  and r.get('head_commit') == changes['head_commit']
                  and r.get('basis') in {'NORMATIVE_REQUIREMENT', 'APPROVED_VERIFICATION_REGISTRY', 'APPROVED_ACCEPTANCE_CRITERION'}
                  and r.get('review_id') and r.get('source_artifact_id') in head]
    for r in applicable:
        source = head[r['source_artifact_id']]
        f.obligation_explicit = _known(True, [_source(source, 'HEAD', 'approved_obligation_registry')])
        tests = [head[t] for t in r.get('covering_test_ids', []) if t in head and head[t].artifact_type in {'test', 'test_method'}]
        if tests and len(tests) == len(r.get('covering_test_ids', [])) and r.get('assertions_reviewed') is True:
            f.other_test_covers_path = _known(True, [_source(t, 'HEAD', 'reviewed_assertion_coverage') for t in tests])
        elif r.get('search_complete') is True and r.get('assertions_reviewed') is True and r.get('covering_test_ids') == []:
            f.other_test_covers_path = _known(False, [_source(source, 'HEAD', 'reviewed_complete_coverage_search')])
    # Exact declared links are trace evidence; similarity links are never promoted.
    links = [r for r in declared_links if r.get('target_artifact') == (b.artifact_id if b else row['artifact_id'])
             and r.get('method') == 'declared' and r.get('source_artifact') in head]
    if links:
        sources = [_source(head[r['source_artifact']], 'HEAD', 'declared_trace_link') for r in links]
        f.link_present = _known(True, sources + head_sources)
        if row['kind'] == 'deleted':
            f.declared_link_to_symbol = _known(True, sources + base_sources)
    if row.get('artifact_type') == 'requirement' and row['kind'] == 'modified' and b:
        validations = [r for r in declared_links
                       if r.get('source_artifact') == b.artifact_id
                       and r.get('relation_type') == 'VALIDATES'
                       and r.get('method') in {'declared', 'upstream-rtmx-module-declaration'}]
        for link in validations:
            target = head.get(link.get('target_artifact'))
            if not target or target.artifact_type not in {'test', 'test_method'}:
                continue
            prior = [x for x in before if x.artifact_type == target.artifact_type
                     and x.file_path == target.file_path and x.symbol == target.symbol]
            if len(prior) == 1:
                f.linked_verification_unchanged = _known(
                    prior[0].content_hash == target.content_hash,
                    [_source(b, 'HEAD', 'changed_requirement_with_validation_link'),
                     _source(prior[0], 'BASE', 'linked_test_baseline'),
                     _source(target, 'HEAD', 'linked_test_head')])
                break
    # A literal client link is broken only when the same client operation resolved at BASE
    # and its changed HEAD request no longer matches a parsed HEAD route.
    if a and a.artifact_type == 'api_caller' and row['kind'] == 'deleted':
        def operation(x):
            return x.symbol.rsplit('::', 1)[-1] if '::' in x.symbol else None
        replacements = [x for x in after if x.artifact_type == 'api_caller'
                        and x.file_path == a.file_path and operation(x) == operation(a)]
        base_routes = [x for x in before if x.artifact_type == 'api']
        current_routes = [x for x in after if x.artifact_type == 'api']
        def matches_route(caller, routes):
            method, path = caller.metadata.get('method'), urlsplit(caller.metadata.get('route', '')).path
            return bool(method and path and any(r.metadata.get('method') == method
                and urlsplit(r.metadata.get('route', '')).path == path for r in routes))
        if len(replacements) == 1 and matches_route(a, base_routes) and not matches_route(replacements[0], current_routes):
            route_sources = [_source(r, 'HEAD', 'literal_route_inventory') for r in current_routes]
            f.stale_consumer = _known(True, [_source(a, 'BASE', 'resolved_literal_client_request'),
                _source(replacements[0], 'HEAD', 'unresolved_changed_client_request'), *route_sources])
    # Default expressions are preserved verbatim; prose extraction is deliberately narrow.
    if b and b.metadata.get('language') == 'python' and b.symbol:
        values = b.metadata.get('parameter_defaults', [])
        previous = a.metadata.get('parameter_defaults', []) if a else []
        if a and previous != values:
            f.default_changed_base_to_head = _known(True, refs)
        if len(values) == 1:
            f.sig_default = _known(values[0]['expression'], head_sources)
            try:
                node = ast.parse(textwrap.dedent(b.content)).body[0]
                doc = ast.get_docstring(node, clean=False) or ''
                matches = re.findall(r'\bdefaults?\s+(?:to\s+)?([0-9]+)\b', doc, re.I)
                if len(set(matches)) == 1:
                    f.doc_default = _known(matches[0], [_source(b, 'HEAD', 'literal_docstring_default')])
            except (SyntaxError, TypeError, IndexError):
                pass
    ranks = {'NORMATIVE_REQUIREMENT': 0, 'APPROVED_API_SCHEMA': 1, 'DESIGNATED_SPEC': 2,
             'BINDING_TEST': 3, 'NORMATIVE_DOCUMENTATION': 4, 'IMPLEMENTATION': 5, 'INFERENCE': 6}
    reviews = [r for r in authority_registry if r.get('status') == 'APPROVED' and r.get('review_id')
               and r.get('subject_id') == row['artifact_id'] and r.get('head_commit') == changes['head_commit']
               and r.get('basis') in ranks and r.get('source_artifact_id') in head]
    if reviews:
        rank = min(ranks[r['basis']] for r in reviews)
        selected = [r for r in reviews if ranks[r['basis']] == rank]
        sources = [_source(head[r['source_artifact_id']], 'HEAD', 'approved_authority_registry') for r in selected]
        values = {(r.get('authority'), r.get('required_default')) for r in selected}
        if len(values) == 1:
            authority, default = next(iter(values))
            if authority in {'NORMATIVE', 'INFORMATIONAL'} and (authority != 'NORMATIVE' or rank < 5):
                f.contract_authority = _known(authority, sources)
                if authority == 'NORMATIVE' and default is not None:
                    f.requirement_default = _known(default, sources)
        else:
            f.contract_authority = _unknown('Conflicting approved sources at the same authority level')
    # Literal route comparison is a bounded candidate check, including method and known params.
    if a and a.artifact_type == 'api':
        head_routes = [x for x in after if x.artifact_type == 'api' and parsed(next(
            (y for y in after if not y.symbol and y.file_path == x.file_path), None))]
        def handler_name(x):
            return x.symbol.rsplit('::', 1)[-1] if '::' in x.symbol else None
        same_handler = [x for x in head_routes if x.file_path == a.file_path
                        and (x.metadata.get('handler_id') == a.metadata.get('handler_id')
                             or (handler_name(a) is not None and handler_name(x) == handler_name(a)))]
        def route_key(x):
            parsed = urlsplit(x.metadata.get('route', ''))
            declared = x.metadata.get('params') or ()
            if isinstance(declared, dict):
                declared = declared.keys()
            if isinstance(declared, str):
                declared = (declared,)
            params = tuple(sorted(set(parse_qs(parsed.query).keys()) | {str(p) for p in declared}))
            return x.metadata.get('method'), parsed.path, params
        if same_handler and not any(route_key(x) == route_key(a) for x in same_handler):
            sources = base_sources + [_source(x, 'HEAD', 'literal_route_registry') for x in same_handler]
            f.route_changed = _known(True, sources)
            alias = any(route_key(x) == route_key(a) for x in head_routes)
            f.route_alias_kept = _known(alias, sources + [_source(x, 'HEAD', 'literal_route_registry') for x in head_routes])
            consumers = [x for x in after if x.artifact_type == 'api_caller'
                         and urlsplit(x.metadata.get('route', '')).path in {route_key(a)[1], *(route_key(x)[1] for x in same_handler)}]
            if consumers:
                csrc = [_source(x, 'HEAD', 'literal_client_request') for x in consumers]
                f.consumer_exists = _known(True, csrc)
                outcomes = []
                for caller in consumers:
                    method, path, _ = route_key(caller)
                    if not method:
                        outcomes.append(None);continue
                    candidates = [r for r in head_routes if route_key(r)[:2] == (method, path)]
                    if not candidates:
                        outcomes.append(False);continue
                    known = [r for r in candidates if 'required_parameters' in r.metadata]
                    if not known:
                        outcomes.append(None);continue
                    params = set(parse_qs(urlsplit(caller.metadata['route']).query))
                    outcomes.append(any(set(r.metadata['required_parameters']) <= params for r in known))
                if False in outcomes:
                    f.consumer_matches_new_route = _known(False, csrc + sources)
                elif outcomes and all(x is True for x in outcomes):
                    f.consumer_matches_new_route = _known(True, csrc + sources)
    return f

def decide(facts:FactsV3)->DecisionV3:
    """Rule decisions are immutable; unknown parser/review facts never become favorable."""
    authority=_value(facts,'contract_authority')
    authority=authority if authority in {'NORMATIVE','INFORMATIONAL','NOT_ESTABLISHED'} else 'NOT_ESTABLISHED'
    state=dict(trace='UNCERTAIN',consistency='UNCERTAIN',test_obligation='NOT_APPLICABLE',
        contract_authority=authority,evidence_ids=[],
        rationale='',rule_id='R7_LLM_SEMANTIC_RESIDUE',needs_review=True,needs_llm=True,blockers=[])
    # Evidence source IDs are collected from all known facts.
    all_fact_values=[getattr(facts,n) for n in FactsV3.model_fields]
    state['evidence_ids']=_ids(*all_fact_values)
    if _value(facts,'evidence_sufficient') is not True:
        state.update(trace='UNCERTAIN',consistency='UNCERTAIN',test_obligation='UNVERIFIED',
            rationale='Required revision-scoped evidence is absent, incomplete, or unverified.',
            rule_id='R0_INSUFFICIENT_EVIDENCE',needs_review=True,needs_llm=False,blockers=['insufficient_evidence'])
        return DecisionV3(**state)
    if _value(facts,'link_present') is True:
        state['trace']='LINKED'
    elif _value(facts,'expected_link') is True and _value(facts,'link_present') is False:
        state['trace']='MISSING_TRACE';state['blockers'].append('missing_required_link')
    if _value(facts,'symbol_deleted_at_head') is True and _value(facts,'renamed_to') is False and (_value(facts,'declared_link_to_symbol') is True or _value(facts,'head_refs_symbol') is True):
        state.update(trace='BROKEN_TRACE',consistency='INCONSISTENT',rationale='Symbol is absent from parsed HEAD while an applicable link/reference remains.',
            rule_id='R1_DELETED_STILL_REFERENCED',needs_review=False,needs_llm=False,blockers=['deleted_symbol_still_referenced'])
        return DecisionV3(**state)
    if _value(facts,'linked_verification_unchanged') is True:
        state.update(trace='LINKED',consistency='POTENTIAL_INCONSISTENCY',
            rationale='A changed requirement retains a VALIDATES link to an unchanged test artifact; semantic coverage still requires review.',
            rule_id='R8_CHANGED_REQUIREMENT_LINKED_TEST_UNCHANGED',needs_review=True,needs_llm=False,
            blockers=['linked_test_not_updated_for_requirement_change'])
        return DecisionV3(**state)
    if _value(facts,'renamed_to') is not None and _value(facts,'renamed_to') is not False:
        state.update(trace='LINKED',rationale='Git/parser rename candidate exists; trace should be re-pointed and reviewed.',
            rule_id='R_RENAME_CANDIDATE',needs_review=True,needs_llm=False,blockers=['rename_mapping_requires_review'])
    deleted=_value(facts,'test_deleted')
    if deleted is True:
        if _value(facts,'obligation_explicit') is not True:
            state['test_obligation']='UNVERIFIED';state['blockers'].append('test_obligation_unverified')
        elif _value(facts,'other_test_covers_path') is True:
            state['test_obligation']='SATISFIED'
        elif _value(facts,'other_test_covers_path') is False:
            state['test_obligation']='UNSATISFIED';state['blockers'].append('test_obligation_unsatisfied')
    kind=_value(facts,'change_kind')
    if kind=='COMMENT_ONLY':
        markers=_value(facts,'comment_has_contract_markers')
        if markers is False:
            state.update(consistency='NO_ASSURANCE_IMPACT',rationale='Verified Python COMMENT_ONLY syntax change; no configured contract marker found. Behavioral equivalence is not inferred.',
                rule_id='R2A_COMMENT_ONLY',needs_review=False,needs_llm=False)
            return DecisionV3(**state)
        if markers is True:
            state.update(rule_id='R2B_COMMENT_CONTRACT_TEXT',rationale='Comment text contains a contract-bearing marker; authority and effect require review.',
                needs_review=True,needs_llm=True);state['blockers'].append('comment_may_carry_contract')
    doc,sig=_value(facts,'doc_default'),_value(facts,'sig_default')
    req=_value(facts,'requirement_default')
    doc_sig=_literal_equal(doc,sig)
    if doc_sig is False:
        req_sig=_literal_equal(req,sig) if req is not None else None
        if authority=='NORMATIVE' and req_sig is True:
            state.update(consistency='POTENTIAL_INCONSISTENCY',rationale=f'Signature default {sig!r} matches the normative requirement; documentation default {doc!r} appears stale.',
                rule_id='R3_STALE_DOC_AGAINST_NORMATIVE',needs_review=True,needs_llm=False)
            state['blockers'].append('documentation_stale_vs_requirement')
            return DecisionV3(**state)
        consistency='INCONSISTENT' if authority=='NORMATIVE' else 'POTENTIAL_INCONSISTENCY'
        state.update(consistency=consistency,rationale=f'Documentation default {doc!r} differs from parsed signature default {sig!r}; authority={authority}.',
            rule_id='R3_DOC_SIGNATURE_DEFAULT_CONFLICT',needs_review=consistency!='INCONSISTENT',needs_llm=False)
        if authority!='NORMATIVE':state['blockers'].append('contract_authority_not_normative')
        return DecisionV3(**state)
    if _value(facts,'default_changed_base_to_head') is True:
        if authority=='NORMATIVE' and req is not None:
            matches=_literal_equal(req,sig)
            if matches is True and _full_head(facts.has_head_evidence_for_req_impl_test) and not state['blockers']:
                state.update(consistency='CONSISTENT',rationale='Normative required default matches the parsed HEAD signature, with complete HEAD evidence.',
                    rule_id='R4_DEFAULT_CHANGED_MATCH',needs_review=False,needs_llm=False)
            elif matches is True:
                state.update(consistency='UNCERTAIN',rationale='Default matches, but complete positive HEAD evidence for applicable requirement, implementation, and test is absent.',
                    rule_id='R4_DEFAULT_MATCH_EVIDENCE_GAP',needs_review=True,needs_llm=False);state['blockers'].append('head_evidence_incomplete')
            elif matches is False:
                state.update(consistency='INCONSISTENT',rationale='Parsed HEAD default contradicts the normative requirement default.',
                    rule_id='R4_DEFAULT_CHANGED_CONFLICT',needs_review=False,needs_llm=False)
            else:
                state.update(consistency='UNCERTAIN',rationale='Default values are symbolic or missing and cannot be compared as literals.',
                    rule_id='R4_DEFAULT_NONLITERAL',needs_review=True,needs_llm=False);state['blockers'].append('default_not_comparable')
        else:
            state.update(consistency='POTENTIAL_INCONSISTENCY',rationale='Default changed across BASE and HEAD; no normative required value is established.',
                rule_id='R4_DEFAULT_CHANGED_UNRESOLVED',needs_review=True,needs_llm=False);state['blockers'].append('contract_authority_not_normative')
        return DecisionV3(**state)
    if _value(facts,'route_changed') is True and _value(facts,'route_alias_kept') is False:
        consumer=_value(facts,'consumer_exists');matches=_value(facts,'consumer_matches_new_route')
        if consumer is True and matches is False:
            state.update(consistency='POTENTIAL_INCONSISTENCY',rationale='Changed route has a statically identified consumer that does not match a HEAD route; runtime compatibility is unverified.',
                rule_id='R5_ROUTE_CONSUMER_MISMATCH',needs_review=True,needs_llm=False);state['blockers'].append('route_compatibility_unverified')
            return DecisionV3(**state)
        if consumer is not True or matches is None:
            state['blockers'].append('route_consumer_unverified')
            state.update(rule_id='R5_ROUTE_CONSUMER_UNKNOWN',rationale='Route changed without an alias; consumer inventory or route comparison is incomplete.',
                needs_review=True,needs_llm=True)
    if _value(facts,'stale_consumer') is True:
        state.update(trace='BROKEN_TRACE',consistency='POTENTIAL_INCONSISTENCY',rationale='A stale HEAD consumer reference was detected; compatibility and contractual effect remain review-required.',
            rule_id='R6_STALE_CONSUMER',needs_review=True,needs_llm=False);state['blockers'].append('stale_consumer')
        return DecisionV3(**state)
    if not _full_head(facts.has_head_evidence_for_req_impl_test):
        state['blockers'].append('head_evidence_incomplete')
    return DecisionV3(**state)

def apply_llm_guard(rule_decision:DecisionV3,facts:FactsV3,llm_decision:DecisionV3,*,votes_agree=True,valid_head_citations=(),valid_citations=(),verified_head_evidence=()):
    """Semantic-only consistency update; never overwrites a rule-established axis."""
    if not rule_decision.needs_llm:return rule_decision
    if not votes_agree:
        return rule_decision.model_copy(update={'consistency':'UNCERTAIN','needs_review':True,
            'needs_llm':False,'rule_id':rule_decision.rule_id+'_LLM_DISAGREEMENT',
            'rationale':rule_decision.rationale+' LLM samples disagreed; abstained.'})
    head_sources={s.evidence_id:s for name in FactsV3.model_fields for s in getattr(facts,name).sources if s.revision=='HEAD'}
    head_ids=set(head_sources)
    head_roles={eid:source.artifact_role for eid,source in head_sources.items()}
    # The caller passes only excerpts verified against the exact immutable HEAD snapshot.
    for source in verified_head_evidence:
        eid=source.get('evidence_id')
        role=source.get('artifact_role')
        if eid and role:
            head_ids.add(eid)
            head_roles[eid]=role
    citations=set(valid_head_citations)
    cited_roles={head_roles[e] for e in citations if e in head_roles}
    if llm_decision.consistency=='CONSISTENT' and (rule_decision.blockers or not _full_head(facts.has_head_evidence_for_req_impl_test) or not citations or not citations<=head_ids or not {'requirement','implementation','test'}<=cited_roles):
        blockers=list(dict.fromkeys([*rule_decision.blockers,'consistent_requires_complete_head_evidence']))
        return rule_decision.model_copy(update={'consistency':'UNCERTAIN','raw_confidence':llm_decision.raw_confidence,'blockers':blockers,'needs_review':True,
            'needs_llm':False,'rule_id':rule_decision.rule_id+'_CONSISTENT_REJECTED',
            'rationale':rule_decision.rationale+' LLM CONSISTENT claim rejected: blocker or verified HEAD evidence gap.'})
    if llm_decision.consistency in {'CONSISTENT','INCONSISTENT','POTENTIAL_INCONSISTENCY','NO_ASSURANCE_IMPACT'}:
        all_valid=set(valid_citations) | citations
        if not llm_decision.evidence_ids or not set(llm_decision.evidence_ids)<=all_valid or not (set(llm_decision.evidence_ids)&citations):
            return rule_decision.model_copy(update={'consistency':'UNCERTAIN','raw_confidence':llm_decision.raw_confidence,
                'needs_review':True,'needs_llm':False,'rule_id':rule_decision.rule_id+'_UNCITED_VERDICT',
                'rationale':rule_decision.rationale+' Decisive model verdict lacked valid, supported HEAD evidence.',
                'blockers':list(dict.fromkeys([*rule_decision.blockers,'decisive_verdict_without_valid_citation']))})
    if llm_decision.consistency=='INCONSISTENT' and rule_decision.contract_authority!='NORMATIVE':
        return rule_decision.model_copy(update={'consistency':'POTENTIAL_INCONSISTENCY',
            'raw_confidence':llm_decision.raw_confidence,'needs_review':True,'needs_llm':False,
            'rationale':'Semantic conflict proposed; normative authority remains unestablished.',
            'rule_id':'R7_AUTHORITY_REVIEW_REQUIRED',
            'blockers':list(dict.fromkeys([*rule_decision.blockers,'contract_authority_not_normative']))})
    return rule_decision.model_copy(update={'consistency':llm_decision.consistency,'raw_confidence':llm_decision.raw_confidence,
        'evidence_ids':list(dict.fromkeys([*rule_decision.evidence_ids,*llm_decision.evidence_ids])),
        'needs_review':llm_decision.consistency in {'UNCERTAIN','POTENTIAL_INCONSISTENCY'},
        'needs_llm':False,'rule_id':rule_decision.rule_id+'_LLM_SEMANTIC_RESIDUE',
        'rationale':llm_decision.rationale})
