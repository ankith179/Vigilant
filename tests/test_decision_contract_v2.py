"""Decision contract regressions; synthetic responses do not measure model quality."""
import json

import pytest

from agents.evidence_first import InterpretationProvider
from ingestion.models import Decision, artifact
from llm.context import request
from llm.ollama import OllamaProvider
from llm.providers import LLMProvider


def response(**changes):
    return dict(schema_version=2, decision='UNCERTAIN', consistency='UNCERTAIN',
                confidence=0.95, evidence_ids=[], affected_artifacts=[],
                reason='The supplied contract needs review.', uncertainty='Scope is incomplete.') | changes


@pytest.mark.parametrize('consistency', ['CONSISTENT', 'INCONSISTENT', 'POTENTIAL_INCONSISTENCY'])
@pytest.mark.parametrize('confidence,evidence_ids', [(0.95, []), (0.0, ['E1']), (0.0, [])])
def test_decisive_consistency_needs_evidence_and_positive_confidence(consistency, confidence, evidence_ids):
    with pytest.raises(ValueError, match='Conclusion without confidence/evidence'):
        Decision.model_validate(response(consistency=consistency, confidence=confidence,
                                         evidence_ids=evidence_ids))


def test_decisive_consistency_can_differ_when_evidence_is_supplied():
    value = Decision.model_validate(response(consistency='INCONSISTENT', evidence_ids=['E1']))
    assert value.decision == 'UNCERTAIN' and value.consistency == 'INCONSISTENT'
    assert value.confidence == 0.95


def test_high_confidence_direct_inconsistency_is_not_downgraded():
    value = Decision.model_validate(response(
        decision='INCONSISTENT', consistency='INCONSISTENT', evidence_ids=['E1']))
    assert value.decision == value.consistency == 'INCONSISTENT'
    assert value.confidence == 0.95


def test_generation_schema_matches_the_modern_output_contract():
    messages = request('Inspect the supplied evidence.', [evidence()])[0]
    schema = OllamaProvider.citation_schema(messages)
    assert schema['properties']['schema_version'].get('const') == 2
    assert 'schema_version' in schema['required']
    assert set(schema['properties']['consistency']['enum']) == {
        'CONSISTENT', 'INCONSISTENT', 'POTENTIAL_INCONSISTENCY', 'UNCERTAIN'}
    assert 'default' not in schema['properties']['confidence']
    assert schema['properties']['evidence_ids']['items']['enum'] == ['E1']


def evidence():
    return dict(evidence_id='source-head', artifact_id='artifact-head', file='api.py',
                commit='head', quote='return 307', start_line=1, end_line=1)


class Stub(LLMProvider):
    name = 'synthetic-contract-test'

    def __init__(self, value):
        self.raw = json.dumps(value)

    def complete(self, messages):
        return self.raw, {}


def wrapped(engine):
    return InterpretationProvider(engine, dict(base_commit='base', head_commit='head',
        verified_change_facts=[], review_candidates=[], evidence_gaps=[]))


@pytest.mark.parametrize('with_wrapper', [False, True])
def test_provider_retains_raw_confidence_and_maps_valid_orthogonal_output(with_wrapper):
    engine = Stub(response(decision='AFFECTED', evidence_ids=['E1'], affected_artifacts=['A1']))
    result = (wrapped(engine) if with_wrapper else engine).investigate('Inspect change', [evidence()])
    assert result['validation_error'] is None
    assert result['decision']['schema_version'] == 2
    assert result['decision']['decision'] == 'AFFECTED'
    assert result['decision']['consistency'] == 'UNCERTAIN'
    assert result['decision']['evidence_ids'] == ['source-head']
    assert result['decision']['confidence'] == 0.95
    assert result['raw_output'] == engine.raw
    assert result['semantic_entailment_verified'] is False


@pytest.mark.parametrize('with_wrapper', [False, True])
def test_modern_request_rejects_missing_version_and_retains_raw_prediction(with_wrapper):
    value = response()
    del value['schema_version']
    engine = Stub(value)
    result = (wrapped(engine) if with_wrapper else engine).investigate('Inspect change', [evidence()])
    assert 'Expected schema_version 2' in result['validation_error']
    assert result['raw_output'] == engine.raw
    assert json.loads(result['raw_output'])['confidence'] == 0.95
    assert result['decision']['schema_version'] == 2
    assert result['decision']['decision'] == result['decision']['consistency'] == 'UNCERTAIN'


def test_legacy_prompt_still_accepts_the_unversioned_legacy_response():
    class Legacy(Stub):
        investigation_request = LLMProvider.legacy_investigation_request
    value = response(decision='AFFECTED', consistency='AFFECTED', evidence_ids=['E1'])
    del value['schema_version']
    result = Legacy(value).investigate('Inspect change', [evidence()])
    assert result['validation_error'] is None
    assert result['decision']['schema_version'] == 1
    assert result['decision']['confidence'] == 0.95


def test_deleted_change_keeps_revision_scoped_presence_facts_in_model_context():
    from agents.evidence_first import analysis_packet

    base = artifact('p', 'r', 'base', 'src/helpers.py', 'function', 'redirect',
                    'def redirect(): pass')
    head_file = artifact('p', 'r', 'head', 'src/helpers.py', 'source_file', '',
                         'def abort(): pass')
    change = {'artifact_id': base.artifact_id, 'new_artifact_id': None,
              'kind': 'deleted', 'artifact_type': 'function', 'file': base.file_path,
              'symbol': base.symbol, 'base_hash': base.content_hash, 'head_hash': None}
    packet = analysis_packet(
        {'base_commit': 'base', 'head_commit': 'head', 'files': [], 'artifacts': [change]},
        [base], [head_file], [])
    engine = Stub(response())
    provider = InterpretationProvider(engine, packet)
    messages, *_ = provider.investigation_request('Inspect deleted function', [evidence()])
    scope = json.loads(messages[-1]['content'])['analysis_scope']
    fact = next(row for row in scope['static_observations'] if row['symbol'] == 'redirect')
    assert fact['kind'] == 'deleted'
    assert [(row['revision_role'], row['commit'], row['content_hash'])
            for row in fact['versions']] == [('base', 'base', base.content_hash)]
    assert scope['base'] == 'base' and scope['head'] == 'head'


def test_model_context_receives_impact_candidates_without_claiming_causality():
    from agents.evidence_first import analysis_packet

    source = artifact('p', 'r', 'head', 'api.py', 'api', 'GET /items', 'route = "/items"')
    client = artifact('p', 'r', 'head', 'client.py', 'function', 'get_items',
                      'return get("/items")')
    path = {'artifact_id': client.artifact_id, 'path': [source.artifact_id, client.artifact_id],
            'path_details': [{'revision_role': 'head', 'path': [source.artifact_id, client.artifact_id],
                              'steps': [{'edge_options': [{'relation_type': 'CONSUMES_API'}]}]}]}
    packet = analysis_packet(
        {'base_commit': 'base', 'head_commit': 'head', 'files': [], 'artifacts': []},
        [source], [source, client], [], [path])
    provider = InterpretationProvider(Stub(response()), packet)
    messages, *_ = provider.investigation_request('Inspect changed endpoint', [evidence()])
    item = json.loads(messages[-1]['content'])['analysis_scope']['impact_candidates'][0]
    assert item['artifact_id'] == client.artifact_id
    assert item['paths'][0]['relations'] == [['CONSUMES_API']]
    assert item['causal_impact_verified'] is False


@pytest.mark.parametrize(('disposition', 'consistency'), [
    ('AFFECTED', 'CONSISTENT'),
    ('AFFECTED', 'INCONSISTENT'),
    ('BROKEN_TRACE', 'UNCERTAIN'),
    ('BROKEN_TRACE', 'INCONSISTENT'),
    ('UNCERTAIN', 'UNCERTAIN'),
    ('UNCERTAIN', 'INCONSISTENT'),
])
def test_v042_v2_cases_round_trip_through_persistence_and_rendered_report(disposition, consistency):
    from backend.exports import export
    from database.store import Store

    value = Decision.model_validate(response(
        decision=disposition, consistency=consistency, evidence_ids=['E1']))
    report = {'run_id': 'v042-fixture', 'commit_id': 'head', 'findings': [], 'evidence': [],
              'model': {'decision': value.model_dump(), 'raw_output': json.dumps(value.model_dump())}}
    store = Store('sqlite:///:memory:')
    store.put('analysis_runs', report['run_id'], report)
    saved = store.get('analysis_runs', report['run_id'])['model']['decision']
    rendered, media = export(store.get('analysis_runs', report['run_id']), 'html')
    assert saved['decision'] == disposition and saved['consistency'] == consistency
    assert saved['confidence'] == 0.95 and saved['schema_version'] == 2
    assert media == 'text/html'
    assert f'Model decision: {disposition}' in rendered
    import html
    assert all(token in html.unescape(rendered) for token in [chr(34)+'decision'+chr(34)+': '+chr(34)+disposition, chr(34)+'consistency'+chr(34)+': '+chr(34)+consistency, chr(34)+'confidence'+chr(34)+': 0.95', chr(34)+'schema_version'+chr(34)+': 2'])

def test_v042_legacy_v1_record_remains_unchanged_through_persistence_and_report():
    from backend.exports import export
    from database.store import Store

    legacy = Decision.model_validate(response(
        schema_version=1, decision='INCONSISTENT', consistency='INCONSISTENT',
        evidence_ids=['E1']))
    store = Store('sqlite:///:memory:')
    store.put('analysis_runs', 'legacy-v1', {'run_id': 'legacy-v1', 'findings': [],
        'evidence': [], 'model': {'decision': legacy.model_dump()}})
    saved = store.get('analysis_runs', 'legacy-v1')['model']['decision']
    rendered, media = export(store.get('analysis_runs', 'legacy-v1'), 'html')
    assert saved['schema_version'] == 1
    assert saved['decision'] == saved['consistency'] == 'INCONSISTENT'
    assert saved['confidence'] == 0.95
    assert media == 'text/html' and 'Model decision: INCONSISTENT' in rendered
