"""Contract tests use synthetic HTTP replies, not model-accuracy observations."""
import json
import httpx
import pytest
from llm.omniroute import OmniRouteProvider
from llm.providers import provider


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv('OMNIROUTE_MODEL', 'groq/example-free-model')
    monkeypatch.setenv('OMNIROUTE_FREE_MODELS', 'groq/example-free-model')
    monkeypatch.setenv('OMNIROUTE_API_KEY', 'test-key')
    monkeypatch.setenv('OMNIROUTE_BASE_URL', 'http://127.0.0.1:20128/v1')


def reply_transport(monkeypatch, status, body):
    seen = []
    original = httpx.Client
    def handle(request):
        seen.append(request)
        return httpx.Response(status, json=body)
    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: original(
        transport=httpx.MockTransport(handle), **kwargs))
    return seen


def evidence(n=1):
    return [{'evidence_id':f'id-{i}', 'artifact_id':f'art-{i}', 'file':f'app-{i}.py',
             'commit':'head' if i % 2 else 'base', 'retrieval_method':'changed',
             'start_line':1, 'end_line':30, 'content_hash':f'hash-{i}',
             'quote':'x'*600+' relevant_tail'} for i in range(n)]


@pytest.mark.parametrize('model', ['', 'auto', 'auto/free', 'combo/my-best', 'other/unapproved'])
def test_reject_unpinned_or_unapproved_before_network(monkeypatch, configured, model):
    monkeypatch.setenv('OMNIROUTE_MODEL', model)
    with pytest.raises(ValueError):
        OmniRouteProvider.configuration()


@pytest.mark.parametrize('url', ['https://example.com/v1', 'http://secret@localhost:20128/v1',
                               'http://localhost:20128/v1?key=secret'])
def test_reject_remote_or_credential_bearing_gateway(monkeypatch, url):
    monkeypatch.setenv('OMNIROUTE_BASE_URL', url)
    with pytest.raises(ValueError):
        OmniRouteProvider.connection()


def test_context_preserves_long_excerpts_and_both_revisions():
    messages, selected, _, _ = OmniRouteProvider().investigation_request('Compare versions', evidence(8))
    payload = json.loads(messages[1]['content'])
    assert len(selected) == 8
    assert all(x['excerpt'].endswith('relevant_tail') for x in payload['evidence'])
    assert {x['commit'] for x in payload['evidence']} == {'base','head'}
    assert payload['evidence_omitted'] == 0


def test_oversized_evidence_omitted_explicitly_without_truncating_others():
    ev = evidence(3)
    ev[0]['quote'] = 'x'*50000
    messages, selected, _, _ = OmniRouteProvider().investigation_request('Compare versions', ev)
    payload = json.loads(messages[1]['content'])
    assert len(selected) == 2 and payload['evidence_omitted'] == 1
    assert all(x['excerpt'].endswith('relevant_tail') for x in payload['evidence'])


def test_transport_maps_citations_and_records_requested_and_reported_models(monkeypatch, configured):
    obj = {'schema_version':2,'decision':'AFFECTED','consistency':'UNCERTAIN','confidence':.8,'evidence_ids':['E1'],
           'affected_artifacts':['A1'],'reason':'Relevant changed symbol','uncertainty':''}
    seen = reply_transport(monkeypatch, 200, {'id':'reply-1','model':'reported-model',
        'choices':[{'finish_reason':'stop','message':{'content':json.dumps(obj)}}],
        'usage':{'completion_tokens':40}})
    result = provider('omniroute').investigate('Inspect change', evidence())
    assert result['validation_error'] is None
    assert result['decision']['evidence_ids'] == ['id-0']
    assert result['usage']['reported_model'] == 'reported-model'
    assert result['usage']['api_cost_usd'] is None
    request = json.loads(seen[0].content)
    assert request['model'] == 'groq/example-free-model'
    assert request['max_tokens'] == 4096
    assert seen[0].headers['Authorization'] == 'Bearer test-key'


@pytest.mark.parametrize('status', [429, 402, 503])
def test_failure_stops_after_one_call_without_fallback(monkeypatch, configured, status):
    seen = reply_transport(monkeypatch, status, {'error':'upstream test failure'})
    result = provider('omniroute').investigate('Inspect change', evidence())
    assert len(seen) == 1
    assert result['validation_error'] is not None
    assert result['decision']['decision'] == 'UNCERTAIN'
    assert not result['usage']


def test_unknown_citation_remains_invalid(monkeypatch, configured):
    obj = {'schema_version':2,'decision':'AFFECTED','consistency':'UNCERTAIN','confidence':.8,'evidence_ids':['E999'],
           'affected_artifacts':['A1'],'reason':'Unsupported','uncertainty':''}
    reply_transport(monkeypatch, 200, {'choices':[{'finish_reason':'stop','message':{'content':json.dumps(obj)}}]})
    result = provider('omniroute').investigate('Inspect change', evidence())
    assert result['validation_error'] and result['decision']['decision'] == 'UNCERTAIN'


def test_truncated_response_is_not_scored_as_reasoning(monkeypatch, configured):
    reply_transport(monkeypatch, 200, {'choices':[{'finish_reason':'length','message':{'content':'{}'}}]})
    result = provider('omniroute').investigate('Inspect change', evidence())
    assert 'incomplete' in result['validation_error']


def test_api_rejects_unconfigured_route(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.app import create_app
    from database.store import Store
    monkeypatch.delenv('OMNIROUTE_MODEL', raising=False)
    store = Store('sqlite:///:memory:')
    store.put('repositories','r',{'repository':'r','path':'unused'})
    with TestClient(create_app(store)) as client:
        response = client.post('/api/analysis/run', json={'repository':'r','model':'omniroute'})
        assert response.status_code == 400 and 'explicit' in response.json()['detail']
    assert store.rows('analysis_runs') == []
