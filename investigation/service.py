"""Bounded snapshot tools. Source correspondence never establishes semantic truth."""
from collections import Counter, deque
from copy import deepcopy
import json
import hashlib
import os
from pathlib import Path
import re
import subprocess
from typing import Annotated
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select,func
from ingestion.models import digest, now
from ingestion.git import revision, inventory
from rag.evidence import evidence, verify_git, retrieve

POLICY = 'vigilant-investigation-tools-v1'
MAX_OUTPUT_BYTES = 750_000
SECRET = re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?:gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16})|(?:api[_-]?key|password|secret|access[_-]?token)\s*[=:]\s*[\"\x27]?[A-Za-z0-9_+/=-]{16,}', re.I)
RELATIONS = {'CALLS','TESTS','IMPORTS','DEPENDS_ON','IMPLEMENTS','VALIDATES','CONSUMES_API','EXPOSES_API'}


class Scope(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    repository: str = Field(min_length=1, max_length=128)
    commit_id: str = Field(pattern=r'^[0-9a-f]{40}(?:[0-9a-f]{24})?$')


class Explore(Scope):
    query: str = Field(default='', max_length=200)
    artifact_type: str | None = Field(default=None, max_length=60)
    offset: int = Field(default=0, ge=0, le=100_000)
    limit: int = Field(default=40, ge=1, le=100)


class Inspect(Scope):
    artifact_id: str = Field(min_length=1, max_length=128)
    start_line: int | None = Field(default=None, ge=1)
    max_lines: int = Field(default=40, ge=1, le=80)


class Lineage(Scope):
    base_commit: str = Field(pattern=r'^[0-9a-f]{40}(?:[0-9a-f]{24})?$')
    paths: list[Annotated[str, Field(min_length=1, max_length=1024)]] = Field(min_length=1, max_length=16)


class Relationships(Scope):
    artifact_id: str = Field(min_length=1, max_length=128)
    direction: Literal['incoming', 'outgoing', 'both'] = 'both'
    relation_type: str | None = Field(default=None, max_length=60)
    offset: int = Field(default=0, ge=0, le=100_000)
    limit: int = Field(default=40, ge=1, le=100)


class Trace(Scope):
    artifact_id: str = Field(min_length=1, max_length=128)
    depth: int = Field(default=2, ge=1, le=4)
    limit: int = Field(default=40, ge=1, le=100)


class Search(Scope):
    query: str = Field(min_length=1, max_length=1200)
    limit: int = Field(default=8, ge=1, le=20)


class Report(Scope):
    run_id: str = Field(min_length=1, max_length=128)


class Retained(Scope):
    result_id: str = Field(min_length=1, max_length=128)


class Unknowns(Scope):
    offset: int = Field(default=0, ge=0, le=100_000)
    limit: int = Field(default=40, ge=1, le=100)
    status: Literal['OPEN', 'RESOLVED', 'ALL'] = 'OPEN'


class UnknownUpdate(Scope):
    unknown_id: str = Field(min_length=1, max_length=128)
    expected_revision: int = Field(ge=1)
    status: Literal['OPEN', 'RESOLVED']
    note: str = Field(min_length=1, max_length=1200)
    resolution_result_id: str | None = Field(default=None, max_length=128)


class Recipe(Scope):
    recipe: Literal['understand_repository','trace_feature','review_tests','explain_dependencies','review_investigation']
    query: str = Field(default='', max_length=1200)
    artifact_id: str | None = Field(default=None, max_length=128)
    run_id: str | None = Field(default=None, max_length=128)
    max_steps: int = Field(default=3, ge=1, le=4)


class ToolResult(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    result_id: str
    policy: str
    tool: str
    scope: dict
    arguments: dict
    data: dict
    evidence: list[dict]
    unknowns: list[dict]
    limitations: list[str]
    source_verification: Literal['PINNED_GIT_AND_STORED_ARTIFACTS']
    semantic_support: Literal['NOT_ESTABLISHED']
    created_at: str


TOOLS = {
    'inspect_lineage': (Lineage, 'Opt-in paired-revision source observations; unreviewed candidates and unknowns, no relationship transfer.'),
    'explore_repository': (Explore, 'Page snapshot files/symbols with Git inventory coverage.'),
    'inspect_artifact': (Inspect, 'Read a bounded exact-source excerpt at an immutable revision.'),
    'find_relationships': (Relationships, 'Inspect typed relationships, endpoint provenance and unresolved candidates.'),
    'trace_impact': (Trace, 'Follow reverse dependencies within one revision; return candidate paths.'),
    'retrieve_evidence': (Search, 'Retrieve BM25 source excerpts without a model call.'),
    'inspect_investigation': (Report, 'Inspect saved changes, findings, uncertainty and coverage.'),
    'inspect_retained_result': (Retained, 'Reuse a retained tool result after identity and Git-source checks.'),
    'list_unknowns': (Unknowns, 'Page current unknown heads; absent relationships do not mean negatives.'),
    'update_unknown': (UnknownUpdate, 'Append a local unknown revision with optimistic concurrency; no repository writes.'),
    'run_recipe': (Recipe, 'Run a bounded deterministic investigation recipe using shared tools.'),
}


def lineage_enabled():
    return os.environ.get('VIGILANT_LINEAGE_TOOLS') == '1'


def catalog():
    return [{'name': name, 'description': description, 'inputSchema': model.model_json_schema(),
             'outputSchema': ToolResult.model_json_schema(),
             'annotations': {'readOnlyHint': False, 'destructiveHint': False,
                             'idempotentHint': name != 'update_unknown', 'openWorldHint': False}}
            for name, (model, description) in TOOLS.items() if name != 'inspect_lineage' or lineage_enabled()]


def result_identity(row):
    return digest(POLICY, {k: v for k, v in row.items() if k not in {'id','result_id','created_at'}})


class InvestigationService:
    def __init__(self, store):
        self.store = store

    def scope(self, args):
        repo = self.store.get('repositories', args.repository)
        if not repo:
            raise ValueError('Repository scope not found')
        try: available = revision(repo['path'], args.commit_id)
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError('Immutable revision unavailable') from exc
        if available != args.commit_id:
            raise ValueError('Immutable revision unavailable')
        table=self.store.tables['artifacts']
        query=select(func.count(),func.sum(func.length(table.c.payload['content'].as_string()))).where(
            table.c.repository==args.repository,table.c.commit_id==args.commit_id)
        with self.store.connection() as connection:
            count,characters=connection.execute(query).one()
        if count>20_000 or (characters or 0)>20_000_000:
            raise ValueError('Snapshot exceeds 20,000-artifact / 20-million-character investigation budget')
        artifacts = self.store.artifacts(args.repository, args.commit_id)
        if not artifacts:
            raise ValueError('Snapshot not indexed; import this revision first')
        projects = {a.project_id for a in artifacts}
        if len(projects) != 1:
            raise ValueError('Snapshot parser identity is ambiguous')
        return repo, artifacts, {'repository': args.repository, 'commit_id': args.commit_id,
                                 'project_id': next(iter(projects))}

    def _verify(self, items, artifacts, repo):
        if verify_git(items, artifacts, repo['path']):
            raise ValueError('Evidence failed pinned Git source verification')
        if any(SECRET.search(e['quote']) for e in items):
            raise ValueError('Sensitive source is withheld from investigation tools')

    def _lineage_guard(self, args):
        if not lineage_enabled():
            raise ValueError('Lineage investigation tools are not enabled')
        for commit in (args.base_commit, args.commit_id):
            row = self.store.get('commits', digest(args.repository, commit))
            if not row or 'review_source_map' in row:
                raise ValueError('Lineage tool requires canonical indexed commits; partial staged sources use their separate workflow')

    def _lineage_data(self, args, repo, head_artifacts, scope):
        from change_analysis.lineage import observe
        self._lineage_guard(args)
        if args.repository != scope['repository'] or args.commit_id != scope['commit_id']:
            raise ValueError('Lineage arguments outside retained scope')
        _, base_artifacts, base_scope = self.scope(Scope(repository=args.repository, commit_id=args.base_commit))
        if base_scope['project_id'] != scope['project_id'] or repo.get('project_id') != scope['project_id']:
            raise ValueError('Lineage repository/parser project scope mismatch')
        try:
            record = observe(repo['path'], project=scope['project_id'], repository=args.repository,
                             base=args.base_commit, head=args.commit_id, paths=args.paths)
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError('Pinned lineage source unavailable') from exc
        excerpts=[]
        for role, artifacts in [('base',base_artifacts),('head',head_artifacts)]:
            parents={a.file_path:a for a in artifacts if not a.symbol}
            observed={endpoint['path']:endpoint for row in record['observations']
                      if (endpoint:=row[role]) and not endpoint['symbol']}
            full=[]
            for path, receipt in record['sources'][role]['selected_sources'].items():
                if receipt['status'] != 'SOURCE_VERIFIED':continue
                a=parents.get(path);expected=observed.get(path)
                if a is None or expected is None or any(getattr(a,k)!=expected[v] for k,v in
                    [('artifact_type','artifact_type'),('content_hash','content_hash'),('start_line','start_line'),('end_line','end_line')]):
                    raise ValueError('Selected full source is not indexed faithfully at both lineage revisions')
                if (a.project_id != scope['project_id'] or a.repository != args.repository or
                    a.commit_id != record['sources'][role]['commit'] or
                    a.artifact_id != digest(scope['project_id'],args.repository,path,a.artifact_type,'')):
                    raise ValueError('Indexed lineage source identity mismatch')
                full.append(evidence(a, 'lineage-indexed-source'))
                excerpts.append(evidence(a, 'lineage-indexed-source', max_lines=12))
            self._verify(full, artifacts, repo)
        data={'lineage_record':record,'canonical_relationships_transferred':False,
              'adapter_policy':'lineage-investigation-adapter-v1',
              'adapter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        excerpts=list({e['evidence_id']:e for e in excerpts}.values())
        return data, excerpts, head_artifacts+base_artifacts

    def retained(self, args):
        repo, artifacts, scope = self.scope(args)
        row = self.store.get('tool_results', args.result_id)
        if not row or row.get('scope') != scope:
            raise ValueError('Retained result outside selected scope')
        result = ToolResult.model_validate({k: row[k] for k in ToolResult.model_fields}).model_dump()
        if result_identity(result) != result['result_id']:
            raise ValueError('Retained result integrity mismatch')
        if result['tool'] == 'inspect_lineage':
            data, expected_excerpts, artifacts = self._lineage_data(Lineage.model_validate(result['arguments']), repo, artifacts, scope)
            if data != result['data'] or expected_excerpts != result['evidence']:
                raise ValueError('Retained lineage source/policy revalidation failed')
        self._verify(result['evidence'], artifacts, repo)
        return result

    def call(self, name, payload):
        if name not in TOOLS:
            raise ValueError('Unknown tool; inspect the tool catalog')
        args = TOOLS[name][0].model_validate(payload)
        if name == 'inspect_lineage':self._lineage_guard(args)
        if SECRET.search(json.dumps(args.model_dump())):
            raise ValueError('Sensitive arguments are withheld')
        if name == 'inspect_retained_result':
            return self.retained(args)
        repo, artifacts, scope = self.scope(args)
        verification_artifacts = artifacts
        by = {a.artifact_id: a for a in artifacts}
        data, excerpts, unknowns = {}, [], []
        limits = ['Static relationships are candidates, not behavioral or requirement-satisfaction proof.',
                  'Source correspondence is verified; semantic support is not independently established.']

        def unknown(code, question):
            unknowns.append({'code': code, 'question': question})

        def select(aid):
            if aid not in by:
                raise ValueError('Artifact outside selected snapshot')
            return by[aid]

        def quote(aid, lines=20, start=None):
            a = select(aid)
            first = start if start is not None else a.start_line
            if first < a.start_line or first > a.end_line:
                raise ValueError('Excerpt start outside artifact range')
            text = '\n'.join(a.content.splitlines()[first-a.start_line:first-a.start_line+lines])
            end = first + max(1, len(text.splitlines())) - 1
            item = evidence(a, POLICY)
            item.update(start_line=first, end_line=end, quote=text,
                        evidence_id=digest(a.artifact_id,a.commit_id,str(first),str(end),text))
            if SECRET.search(text):
                unknown('SENSITIVE_SOURCE_WITHHELD','A selected excerpt contains a possible secret and was withheld.')
                return None
            excerpts.append(item)
            return item['evidence_id']

        def summary(a):
            return {k: getattr(a, k) for k in ('artifact_id','artifact_type','file_path','symbol','start_line','end_line','content_hash')}

        def edges():
            rows = self.store.graph_edges(args.repository, args.commit_id, 20_001)
            if len(rows) > 20_000:
                raise ValueError('Graph exceeds 20,000-edge budget; use narrower stored investigations')
            out = []
            for e in rows:
                if e.get('edge_policy') != 'typed-v2':
                    continue
                if e['source_artifact'] not in by or e['target_artifact'] not in by:
                    raise ValueError('Graph contains unindexed endpoints')
                if e.get('project_id') != scope['project_id']:
                    raise ValueError('Graph parser scope mismatch')
                spans = e.get('evidence_spans', [])
                if {s['artifact_id'] for s in spans} != {e['source_artifact'],e['target_artifact']}:
                    raise ValueError('Graph endpoint evidence missing')
                for s in spans:
                    a = select(s['artifact_id'])
                    if any(s[k] != v for k, v in {'commit': args.commit_id,'file': a.file_path,'content_hash': a.content_hash,
                                                  'start_line': a.start_line,'end_line': a.end_line}.items()):
                        raise ValueError('Graph endpoint evidence mismatch')
                out.append(e)
            if not out:
                unknown('RELATIONSHIPS_UNAVAILABLE','No typed graph records are indexed; absence of links is not a negative result.')
            return out

        if name == 'inspect_lineage':
            data, excerpts, verification_artifacts = self._lineage_data(args, repo, artifacts, scope)
            limits.extend(data['lineage_record']['limitations'])
            unknown('LINEAGE_UNREVIEWED','Endpoint correspondence candidates do not establish logical identity or permit relationship transfer.')
            counts=data['lineage_record']['denominators']
            if counts['unknown_observations'] or counts['unavailable_file_sides']:
                unknown('LINEAGE_SCOPE_GAPS',f"{counts['unknown_observations']} unknown observations; {counts['unavailable_file_sides']} unavailable selected file sides remain in scope.")
        elif name == 'explore_repository':
            found = [a for a in artifacts if (not args.artifact_type or a.artifact_type == args.artifact_type)
                     and args.query.casefold() in (a.file_path+' '+a.symbol).casefold()]
            found.sort(key=lambda a: (a.file_path,a.start_line,a.artifact_id))
            git_files = inventory(repo['path'],args.commit_id)
            files = {a.file_path: a for a in artifacts if not a.symbol}
            absent = [r['file'] for r in git_files if r['eligible'] and r['file'] not in files]
            failures = [a.file_path for a in files.values() if a.metadata.get('parse_error') or a.metadata.get('parse_has_error')]
            data = {'items':[summary(a) for a in found[args.offset:args.offset+args.limit]],'total':len(found),
                    'next_offset':args.offset+args.limit if args.offset+args.limit<len(found) else None,
                    'artifact_roles':dict(Counter(a.artifact_type for a in artifacts)),
                    'coverage':{'git_files':len(git_files),'imported_files':len(files),'eligible_not_extracted':absent,
                                'parse_failures':failures,'excluded_files':sum(not r['eligible'] for r in git_files)}}
            if absent or failures:
                unknown('EXTRACTION_GAPS',f'{len(absent)} eligible files unextracted; {len(failures)} parse failures.')
            unknown('SEMANTIC_COVERAGE','Whole-program behavior and complete test coverage are not established.')
        elif name == 'inspect_artifact':
            a = select(args.artifact_id)
            data = {'artifact':summary(a),'evidence_id':quote(a.artifact_id,args.max_lines,args.start_line),
                    'parser_policy':a.metadata.get('parser_policy','historical-unversioned')}
        elif name == 'find_relationships':
            select(args.artifact_id)
            found = [e for e in edges() if (not args.relation_type or e['relation_type']==args.relation_type)
                     and ((args.direction in {'outgoing','both'} and e['source_artifact']==args.artifact_id)
                          or (args.direction in {'incoming','both'} and e['target_artifact']==args.artifact_id))]
            page = found[args.offset:args.offset+args.limit]
            data = {'items':page,'total':len(found),'next_offset':args.offset+args.limit if args.offset+args.limit<len(found) else None}
            endpoints = sorted({e[k] for e in page for k in ('source_artifact','target_artifact')})
            for aid in endpoints[:24]: quote(aid,8)
            if len(endpoints)>24: unknown('ENDPOINT_EXCERPT_BUDGET','Page has more endpoints than the 24-excerpt budget; inspect endpoints individually.')
            if any(e.get('provenance_type')=='HEURISTIC' for e in page):
                unknown('HEURISTIC_RELATIONSHIPS','Some relationships are unresolved heuristic candidates.')
        elif name == 'trace_impact':
            select(args.artifact_id)
            reverse = {}
            for e in edges():
                if e['relation_type'] in RELATIONS: reverse.setdefault(e['target_artifact'],[]).append(e)
            queue=deque([(args.artifact_id,[],[args.artifact_id])]);seen={args.artifact_id};paths=[];truncated=False
            while queue:
                node,steps,path=queue.popleft()
                if len(steps)>=args.depth: continue
                for e in reverse.get(node,[]):
                    target=e['source_artifact']
                    if target in seen: continue
                    if len(paths)>=args.limit: truncated=True; break
                    seen.add(target);new_steps=steps+[e];new_path=path+[target]
                    paths.append({'artifact_id':target,'path':new_path,'steps':new_steps,'classification':'IMPACT_CANDIDATE',
                                  'causal_impact_verified':False,'commit_id':args.commit_id})
                    queue.append((target,new_steps,new_path))
                if truncated: break
            data={'paths':paths,'truncated':truncated,'depth':args.depth,'direction':'reverse-dependency',
                  'path_selection':'first deterministic shortest node path; alternative paths not enumerated'}
            for aid in sorted(seen)[:24]: quote(aid,8)
            unknown('BEHAVIORAL_IMPACT','Static paths do not verify causal impact; dynamic dispatch and external dependencies may be unobserved.')
            if truncated or len(seen)>24: unknown('TRAVERSAL_BUDGET','Traversal or endpoint excerpts reached the requested resource budget.')
        elif name == 'retrieve_evidence':
            items=retrieve(args.query,artifacts,k=args.limit)
            for e in items:
                if SECRET.search(e['quote']): unknown('SENSITIVE_SOURCE_WITHHELD','A retrieved excerpt was withheld.')
                else: excerpts.append(e)
            data={'query':args.query,'retrieved':len(excerpts),'method':'bm25','ranking_is_semantic_verification':False}
            if not excerpts: unknown('NO_RETRIEVED_EVIDENCE','No admissible source excerpt matched; this does not prove absence.')
        elif name == 'inspect_investigation':
            report=self.store.get('analysis_runs',args.run_id)
            if not report or report.get('status')!='COMPLETED' or not report.get('changes') or any(report.get(k)!=scope[k] for k in scope):
                raise ValueError('Completed investigation outside selected snapshot')
            base_artifacts=self.store.artifacts(args.repository,report['base_commit'])
            self._verify(report.get('evidence',[]),artifacts+base_artifacts,repo)
            # Keep this single-revision envelope self-contained; the base report owns paired source.
            excerpts=[e for e in report.get('evidence',[]) if e['commit']==args.commit_id][:20]
            data={'run_id':args.run_id,'base_commit':report['base_commit'],'head_commit':report['commit_id'],
                  'changed_files':len(report['changes']['files']),'findings':report['findings'],
                  'impact_candidates':len(report.get('affected_artifacts',[])),
                  'coverage':{role:{k:v for k,v in cov.items() if k!='inventory'} for role,cov in report.get('coverage',{}).items()},
                  'obligation_review':report.get('obligation_review'),'source_report_reference':args.run_id}
            for text in report.get('limitations',[]): unknown('REPORT_LIMITATION',text)
        elif name == 'list_unknowns':
            histories=self.store.rows('unknown_revisions',repository=args.repository,commit_id=args.commit_id)
            heads={}
            for row in histories:
                if row['sequence']>heads.get(row['unknown_id'],{}).get('sequence',0): heads[row['unknown_id']]=row
            found=sorted((h for h in heads.values() if args.status=='ALL' or h['status']==args.status),key=lambda h:h['unknown_id'])
            data={'items':found[args.offset:args.offset+args.limit],'total':len(found),
                  'next_offset':args.offset+args.limit if args.offset+args.limit<len(found) else None}
        elif name == 'update_unknown':
            key=digest(args.unknown_id,str(args.expected_revision))
            previous=self.store.get('unknown_revisions',key)
            if not previous or any(previous.get(k)!=scope[k] for k in scope): raise ValueError('Unknown outside selected scope')
            if self.store.get('unknown_revisions',digest(args.unknown_id,str(args.expected_revision+1))):
                raise ValueError('Unknown revision conflict; read current head before updating')
            if args.status=='RESOLVED':
                if not args.resolution_result_id: raise ValueError('Resolution requires retained source evidence')
                resolved=self.retained(Retained(**scope_without_project(scope),result_id=args.resolution_result_id))
                if not resolved['evidence']: raise ValueError('Resolution requires source excerpts, not an empty result')
            elif args.resolution_result_id:
                self.retained(Retained(**scope_without_project(scope),result_id=args.resolution_result_id))
            row={k:v for k,v in previous.items() if k not in {'id','created_at'}}
            row.update(sequence=args.expected_revision+1,status=args.status,note=args.note,
                       previous_fingerprint=digest({k:v for k,v in previous.items() if k!='id'}),
                       resolution_result_id=args.resolution_result_id,created_at=now(),
                       resolution_basis='CALLER_ATTESTATION_SOURCE_LINKED' if args.status=='RESOLVED' else None)
            self.store.put('unknown_revisions',digest(args.unknown_id,str(row['sequence'])),row)
            data={'unknown':row,'semantic_resolution_independently_verified':False}
        elif name == 'run_recipe':
            base=scope_without_project(scope)
            if args.recipe=='understand_repository': plan=[('explore_repository',base)]
            elif args.recipe in {'trace_feature','review_tests'}:
                if not args.query.strip(): raise ValueError('Feature/test recipe requires a query')
                plan=[('retrieve_evidence',{**base,'query':args.query,'limit':6})]
            elif args.recipe=='explain_dependencies':
                if not args.artifact_id: raise ValueError('Dependency recipe requires an artifact')
                plan=[('inspect_artifact',{**base,'artifact_id':args.artifact_id}),
                      ('find_relationships',{**base,'artifact_id':args.artifact_id}),
                      ('trace_impact',{**base,'artifact_id':args.artifact_id})]
            else:
                if not args.run_id: raise ValueError('Investigation recipe requires a run ID')
                plan=[('inspect_investigation',{**base,'run_id':args.run_id})]
            steps=[]
            for tool,arguments in plan[:args.max_steps]:
                r=self.call(tool,arguments);steps.append({'tool':tool,'result_id':r['result_id'],'data':r['data']})
                excerpts.extend(r['evidence']);unknowns.extend(r['unknowns'])
            data={'recipe':args.recipe,'steps':steps,'completion':'BUDGET_EXHAUSTED' if len(plan)>args.max_steps else 'COMPLETED_WITH_UNKNOWNS',
                  'budget':{'max_steps':args.max_steps,'steps_used':len(steps)},'inference_calls':0,'subject_code_executed':False}
            if len(plan)>args.max_steps: unknown('STEP_BUDGET','Recipe stopped before all planned tools completed.')

        excerpts=list({e['evidence_id']:e for e in excerpts}.values())
        self._verify(excerpts,verification_artifacts,repo)
        unique={digest(u['code'],u['question']):{'code':u['code'],'question':u['question']} for u in unknowns}
        unknowns=[{**u,'unknown_id':digest(POLICY,scope,u['code'],u['question'])} for u in unique.values()]
        row={'policy':POLICY,'tool':name,'scope':scope,'arguments':args.model_dump(),'data':data,
             'evidence':excerpts,'unknowns':unknowns,'limitations':limits,
             'source_verification':'PINNED_GIT_AND_STORED_ARTIFACTS','semantic_support':'NOT_ESTABLISHED','created_at':now()}
        row['result_id']=result_identity(row)
        result=ToolResult.model_validate(row).model_dump()
        if SECRET.search(json.dumps(data,ensure_ascii=False)):
            raise ValueError('Sensitive result data is withheld')
        if len(json.dumps(result,ensure_ascii=False).encode())>MAX_OUTPUT_BYTES:
            raise ValueError('Tool output exceeds budget; request a smaller page or scope')
        stored=self.store.put('tool_results',row['result_id'],{**row,**scope})
        for u in unknowns:
            key=digest(u['unknown_id'],'1')
            if not self.store.get('unknown_revisions',key):
                self.store.put('unknown_revisions',key,{**scope,**u,'sequence':1,'status':'OPEN',
                    'source_result_id':row['result_id'],'previous_fingerprint':None,'created_at':now()})
        return ToolResult.model_validate({k:stored[k] for k in ToolResult.model_fields}).model_dump()


def scope_without_project(scope):
    return {k:scope[k] for k in ('repository','commit_id')}
