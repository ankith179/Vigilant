"""Authored report-integration fixtures, not independent research labels."""
import copy
import json
import pytest
from agents.workflow import analyze
from agents.obligation_report import attach_obligations
from backend.report_chat import explain, ReportChatInput
from backend.exports import export
from database.store import Store
from ingestion.models import digest
from tests.test_integration import repository
from tests.test_obligations import registry_fixture


@pytest.fixture
def integration(tmp_path):
    repo = tmp_path / 'repo'; git = repository(repo)
    base = git('rev-parse', 'HEAD')
    (repo/'app.py').write_text('def value():\n    return 2\n\ndef test_value():\n    assert value() == 1\n')
    git('commit', '-am', 'authored drift fixture')
    store = Store('sqlite:///:memory:')
    parent = analyze(store, repo, base, project='separate-parser-fixture')
    a = next(a for a in store.artifacts(parent['repository'], parent['commit_id']) if not a.symbol)
    ref = dict(artifact_id=a.artifact_id, commit_id=a.commit_id, file=a.file_path,
               content_hash=a.content_hash, start_line=a.start_line, end_line=a.end_line)
    _, payload = registry_fixture()
    payload.update(repository=parent['repository'], parser_identity=parent['project_id'])
    r = payload['histories'][0][0]; r['commit_id'] = a.commit_id
    r['obligation'].update(source=ref, evidence=[ref], applicable_artifact_ids=[a.artifact_id])
    r['search_scope'].update(evidence=[ref], applicable_artifact_ids=[a.artifact_id])
    return store, parent, payload


def chat(store, report):
    return explain(store, ReportChatInput(project_id=report['project_id'], repository=report['repository'],
        run_id=report['run_id'], base_commit=report['base_commit'], head_commit=report['commit_id'],
        question='Explain test obligations', intent='TEST_OBLIGATIONS'))


def test_derived_report_is_immutable_idempotent_and_source_linked(integration):
    store, parent, payload = integration
    original = copy.deepcopy(store.get('analysis_runs', parent['run_id']))
    graph = copy.deepcopy(store.rows('graph_edges'))
    report = attach_obligations(store, parent['run_id'], payload)
    assert report['run_id'] != parent['run_id']
    assert report == attach_obligations(store, parent['run_id'], payload)
    assert store.get('analysis_runs', parent['run_id']) == original
    assert store.rows('graph_edges') == graph
    assert report['derivation']['new_model_calls'] == 0
    assert report['parent_investigation_metrics'] == parent['metrics']
    added = [f for f in report['findings'] if f['method'] == 'reviewed-obligation-registry-v1']
    assert len(added) == 1 and added[0]['evidence_ids']
    assert set(added[0]['evidence_ids']) <= {e['evidence_id'] for e in report['evidence']}
    answer = chat(store, report)
    assert answer['state'] == 'NOT_ESTABLISHED'
    assert 'recorded MISSING_TEST' in answer['answer']
    assert 'No complete verification-obligation registry' not in answer['answer']
    for fmt in ['json', 'csv', 'html']:
        body, _ = export(report, fmt)
        assert 'reviewed-unmet-test-obligation' in body
    with pytest.raises(ValueError, match='original investigation'):
        attach_obligations(store, report['run_id'], payload)


def test_empty_or_counterevidence_registry_preserves_abstention(integration):
    store, parent, payload = integration
    empty = copy.deepcopy(payload); empty['histories'] = []
    first = attach_obligations(store, parent['run_id'], empty)
    assert not first['obligation_review']['findings']
    assert not any(f['status'] == 'MISSING_TEST' for f in first['findings'])
    counter = copy.deepcopy(payload)
    counter['histories'][0][0]['counterevidence'] = [counter['histories'][0][0]['obligation']['source']]
    second = attach_obligations(store, parent['run_id'], counter)
    assert second['run_id'] != first['run_id']
    assert not second['obligation_review']['findings']
    assert 'COUNTEREVIDENCE_REQUIRES_REVIEW' in chat(store, second)['answer']
    assert 'No complete verification-obligation registry' in chat(store, parent)['answer']


def test_wrong_identity_or_forged_registry_fails_without_saving_report(integration):
    store, parent, payload = integration
    count = len(store.rows('analysis_runs'))
    for field in ['repository', 'parser_identity']:
        bad = copy.deepcopy(payload); bad[field] = 'foreign'
        with pytest.raises(ValueError): attach_obligations(store, parent['run_id'], bad)
    bad = copy.deepcopy(payload); bad['histories'][0][0]['obligation']['source']['content_hash'] = 'forged'
    with pytest.raises(ValueError): attach_obligations(store, parent['run_id'], bad)
    assert len(store.rows('analysis_runs')) == count


def test_parent_source_is_reverified_before_attachment(integration):
    store, parent, payload = integration
    corrupted = copy.deepcopy(store.get('analysis_runs', parent['run_id']))
    corrupted['evidence'][0]['quote'] += 'forged'
    store.put('analysis_runs', parent['run_id'], corrupted, replace=True)
    with pytest.raises(ValueError, match='source verification'):
        attach_obligations(store, parent['run_id'], payload)


def test_api_serves_derived_report_and_exports_without_new_investigation(integration):
    from fastapi.testclient import TestClient
    from backend.app import create_app
    store, parent, payload = integration
    report = attach_obligations(store, parent['run_id'], payload)
    with TestClient(create_app(store)) as client:
        assert client.get('/api/reports/'+report['run_id']).json()['derivation']['parent_run_id'] == parent['run_id']
        response = client.get('/api/reports/'+report['run_id']+'/export', params={'format':'json'})
        assert response.status_code == 200
        assert response.json()['obligation_review']['quality_target_91'] == 'NOT_EVALUATED'
