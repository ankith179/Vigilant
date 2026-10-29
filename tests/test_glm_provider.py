"""Mocked GLM transport tests; these do not measure model quality or call Z.ai."""
import json

import httpx
import pytest

from llm.glm import GLMProvider
from llm.providers import provider


def evidence():
    return [{'evidence_id': 'ev-1', 'artifact_id': 'art-1', 'file': 'src/app.py',
             'commit': 'head', 'retrieval_method': 'test', 'start_line': 1, 'end_line': 2,
             'content_hash': 'hash-1', 'quote': 'def check(): return True'}]


def configure(monkeypatch):
    monkeypatch.setenv('GLM_API_KEY', 'test-only-key')
    monkeypatch.setenv('GLM_MODEL', 'glm-5.3')
    monkeypatch.setenv('VIGILANT_FREE_ONLY', '0')


def mock_response(monkeypatch, status, payload):
    calls = []
    original = httpx.Client

    def handle(request):
        calls.append(request)
        return httpx.Response(status, json=payload)

    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: original(
        transport=httpx.MockTransport(handle), **kwargs))
    return calls


def test_glm_is_blocked_by_default_cost_policy(monkeypatch):
    monkeypatch.delenv('VIGILANT_FREE_ONLY', raising=False)
    with pytest.raises(ValueError, match='free-only'):
        provider('glm')


def test_missing_api_key_fails_before_request(monkeypatch):
    monkeypatch.delenv('GLM_API_KEY', raising=False)
    monkeypatch.setenv('GLM_MODEL', 'glm-5.3')
    with pytest.raises(ValueError, match='GLM_API_KEY'):
        GLMProvider().preflight()


def test_analysis_api_accepts_glm_selection_but_stops_before_queue_without_key(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from backend.app import create_app
    from database.store import Store

    monkeypatch.setenv('VIGILANT_FREE_ONLY', '0')
    monkeypatch.setenv('GLM_MODEL', 'glm-5.3')
    monkeypatch.delenv('GLM_API_KEY', raising=False)
    store = Store('sqlite:///' + str(tmp_path / 'glm-api.sqlite'))
    store.put('repositories', 'r', {'repository': 'r', 'project_id': 'p', 'path': str(tmp_path)})
    with TestClient(create_app(store)) as client:
        response = client.post('/api/analysis/run', json={'repository': 'r', 'model': 'glm'})
    assert response.status_code == 400
    assert 'GLM_API_KEY' in response.json()['detail']
    assert store.rows('analysis_runs') == []


def test_transport_maps_valid_citations_and_records_model(monkeypatch):
    configure(monkeypatch)
    output = {'schema_version': 2, 'decision': 'AFFECTED', 'consistency': 'UNCERTAIN',
              'confidence': 0.8, 'evidence_ids': ['E1'], 'affected_artifacts': ['A1'],
              'reason': 'Evidence identifies the changed artifact.', 'uncertainty': ''}
    calls = mock_response(monkeypatch, 200, {'id': 'glm-run-1', 'model': 'glm-5.3',
        'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(output)}}],
        'usage': {'prompt_tokens': 30, 'completion_tokens': 20}})
    result = provider('glm').investigate('Inspect this change', evidence())
    assert result['validation_error'] is None
    assert result['decision']['evidence_ids'] == ['ev-1']
    assert result['usage']['requested_model'] == result['usage']['reported_model'] == 'glm-5.3'
    assert result['usage']['api_cost_usd'] is None
    req = calls[0]
    assert str(req.url) == 'https://api.z.ai/api/paas/v4/chat/completions'
    assert req.headers['Authorization'] == 'Bearer test-only-key'
    body = json.loads(req.content)
    assert body['temperature'] == 0 and body['response_format'] == {'type': 'json_object'}


@pytest.mark.parametrize('status', [302, 429, 500])
def test_http_failure_has_no_retry_or_redirect(monkeypatch, status):
    configure(monkeypatch)
    calls = mock_response(monkeypatch, status, {'error': 'test failure'})
    result = provider('glm').investigate('Inspect this change', evidence())
    assert len(calls) == 1
    assert result['validation_error'] is not None
    assert result['decision']['decision'] == 'UNCERTAIN'


def test_incomplete_generation_is_not_scored(monkeypatch):
    configure(monkeypatch)
    mock_response(monkeypatch, 200, {'choices': [{'finish_reason': 'length',
        'message': {'content': '{"schema_version":2}'}}]})
    result = provider('glm').investigate('Inspect this change', evidence())
    assert 'incomplete' in result['validation_error']
    assert result['decision']['decision'] == 'UNCERTAIN'
