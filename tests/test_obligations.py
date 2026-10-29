"""Authored engineering fixtures only; these do not create independent gold labels."""
import copy
import pytest
from consistency.obligations import assess_registry, ObligationRegistry, revision_fingerprint
from database.store import Store
from ingestion.models import artifact, digest


def registry_fixture():
    store = Store('sqlite:///:memory:')
    a = artifact('parser-v4-fixture', 'repo-fixture', 'head', 'req.md', 'requirement', '', 'Return one; require a test.')
    store.put('artifacts', digest(a.artifact_id, a.commit_id), a.model_dump())
    ref = {k: getattr(a, k) for k in ('artifact_id', 'commit_id', 'content_hash', 'start_line', 'end_line')}
    ref['file'] = a.file_path
    o = dict(obligation_id='one', requirement='Return one', acceptance_criterion='value()==1',
             lifecycle='ACTIVE', applicable_artifact_ids=[a.artifact_id], source=ref,
             verification_kind='TEST', satisfaction='UNMET', evidence=[ref], test_search_coverage='REVIEWED_COMPLETE')
    scope = dict(reviewer_id='fixture-reviewer', rationale='Authored fixture boundary only',
                 completeness='REVIEWED_COMPLETE', applicable_artifact_ids=[a.artifact_id],
                 searched_artifact_ids=[], unknown_regions=[], evidence=[ref])
    revision = dict(sequence=1, previous_fingerprint=None, commit_id='head', reviewer_id='fixture-reviewer',
                    rationale='Authored unmet-obligation fixture', obligation=o, search_scope=scope, counterevidence=[],
                    root_cause_id=None, root_cause_evidence=[])
    registry = dict(repository=a.repository, parser_identity=a.project_id, inventory='REVIEWED', histories=[[revision]])
    return store, registry


def assess(store, registry, commit='head'):
    return assess_registry(store, registry, commit, check_git=False)


def test_no_obligation_no_missing_test_and_explicit_reviewed_unmet_gate():
    store, registry = registry_fixture()
    empty = copy.deepcopy(registry); empty['histories'] = []
    assert assess(store, empty)['findings'] == []
    result = assess(store, registry)
    assert len(result['findings']) == 1 and result['findings'][0]['status'] == 'MISSING_TEST'
    assert result['quality_target_91'] == 'NOT_EVALUATED'
    assert result['findings'][0]['test_execution'] == 'NOT_RUN'


@pytest.mark.parametrize('mode', ['unknown_inventory', 'retired', 'unknown_lifecycle', 'unknown_satisfaction',
                                 'satisfied', 'no_scope', 'scope_mismatch', 'counterevidence', 'stale'])
def test_unknown_retired_stale_or_counterevidence_never_establishes_missing_test(mode):
    store, registry = registry_fixture(); r = registry['histories'][0][0]; o = r['obligation']
    commit = 'head'
    if mode == 'unknown_inventory': registry['inventory'] = 'UNKNOWN'
    elif mode == 'retired': o['lifecycle'] = 'RETIRED'
    elif mode == 'unknown_lifecycle': o['lifecycle'] = 'UNKNOWN'
    elif mode == 'unknown_satisfaction': o['satisfaction'] = 'UNKNOWN'
    elif mode == 'satisfied': o['satisfaction'] = 'SATISFIED'
    elif mode == 'no_scope': r['search_scope'] = None
    elif mode == 'scope_mismatch': r['search_scope']['applicable_artifact_ids'] = ['outside']
    elif mode == 'counterevidence': r['counterevidence'] = [o['source']]
    elif mode == 'stale': commit = 'later'
    result = assess(store, registry, commit)
    assert not result['findings'] and result['assessments'][0]['blockers']


def test_partial_search_unknown_regions_and_forged_sources_fail_closed():
    store, registry = registry_fixture()
    for edit in ('partial', 'unknown_region', 'hash', 'range', 'foreign', 'identity', 'missing_searched'):
        bad = copy.deepcopy(registry); r = bad['histories'][0][0]
        if edit == 'partial': r['search_scope']['completeness'] = 'PARTIAL'
        elif edit == 'unknown_region': r['search_scope']['unknown_regions'] = ['external tests']
        elif edit == 'hash': r['obligation']['source']['content_hash'] = 'forged'
        elif edit == 'range': r['obligation']['source']['end_line'] = 100
        elif edit == 'foreign': r['obligation']['source']['commit_id'] = 'other'
        elif edit == 'identity': bad['parser_identity'] = 'rewritten-frozen-identity'
        elif edit == 'missing_searched': r['search_scope']['searched_artifact_ids'] = ['unavailable']
        with pytest.raises(ValueError): assess(store, bad)


def test_lifecycle_append_history_and_explicit_cause_grouping_preserve_all_obligations():
    store, registry = registry_fixture(); original = registry['histories'][0][0]
    second = copy.deepcopy(original); second['sequence'] = 2
    second['previous_fingerprint'] = revision_fingerprint(ObligationRegistry.model_validate(registry).histories[0][0])
    second['obligation']['lifecycle'] = 'RETIRED'
    registry['histories'][0].append(second)
    assert not assess(store, registry)['findings']
    broken = copy.deepcopy(registry); broken['histories'][0][0]['rationale'] += ' modified'
    with pytest.raises(ValueError, match='history chain'): assess(store, broken)
    registry['histories'][0] = [original]
    other = copy.deepcopy(original); other['obligation']['obligation_id'] = 'two'
    registry['histories'].append([other])
    assert len(assess(store, registry)['findings']) == 2
    for history in registry['histories']:
        history[0]['root_cause_id'] = 'reviewed-cause-fixture'
        history[0]['root_cause_evidence'] = [history[0]['obligation']['source']]
    grouped = assess(store, registry)
    assert len(grouped['findings']) == 1
    assert grouped['findings'][0]['obligation_ids'] == ['one', 'two']
    assert len(grouped['assessments']) == 2
    registry['histories'][1][0]['counterevidence'] = [original['obligation']['source']]
    assert assess(store, registry)['findings'][0]['obligation_ids'] == ['one']


def test_registry_rechecks_git_even_if_store_is_self_consistently_forged(tmp_path):
    from tests.test_integration import repository
    from ingestion.service import import_repository
    from tests.test_review_intake import fixture_forms
    repo = tmp_path / 'repo'; repository(repo)
    store = Store('sqlite:///:memory:'); imported = import_repository(store, repo)
    a = next(a for a in store.artifacts(imported['repository'], imported['commit_id']) if not a.symbol)
    case, _ = fixture_forms(a); ref = case['evidence'][0]
    _, registry = registry_fixture(); registry.update(repository=a.repository, parser_identity=a.project_id)
    r = registry['histories'][0][0]; r['commit_id'] = a.commit_id
    o = r['obligation']; o.update(source=ref, evidence=[ref], applicable_artifact_ids=[a.artifact_id])
    r['search_scope'].update(evidence=[ref], applicable_artifact_ids=[a.artifact_id])
    assert assess_registry(store, registry, a.commit_id)['findings']
    a.content += '\nforged'; a.end_line += 1; a.content_hash = digest(a.content)
    store.put('artifacts', digest(a.artifact_id, a.commit_id), a.model_dump(), replace=True)
    ref.update(content_hash=a.content_hash, end_line=a.end_line)
    with pytest.raises(ValueError, match='Git blob'):
        assess_registry(store, registry, a.commit_id)


@pytest.mark.parametrize('field',['artifact_id','commit_id'])
def test_registry_rejects_stored_identity_rebinding(field):
    store,registry=registry_fixture()
    source=registry['histories'][0][0]['obligation']['source']
    key=digest(source['artifact_id'],source['commit_id'])
    row=store.get('artifacts',key);row[field]='rebound'
    store.put('artifacts',key,{k:v for k,v in row.items() if k!='id'},replace=True)
    with pytest.raises(ValueError,match='identity/revision mismatch'):
        assess(store,registry)
