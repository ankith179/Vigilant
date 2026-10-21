"""Synthetic transport checks for bounded evaluation, not accuracy measurements."""
import json
import sys
import httpx
from llm.providers import LLMProvider
from llm.omniroute import OmniRouteProvider
from scripts import evaluate_omniroute as runner


def test_bounded_resume_preserves_prompts_and_does_not_repeat_calls(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    (tmp_path/'llm').mkdir()
    for name in ['omniroute.py','providers.py','context.py']:
        (tmp_path/'llm'/name).write_text('synthetic test version')
    ev = [{'evidence_id':'ev','artifact_id':'a','file':'a.py','commit':'head','quote':'def f(): pass'}]
    messages = LLMProvider().legacy_investigation_request('Inspect change', ev)[0]
    source = tmp_path/'original.json'
    source.write_text(json.dumps({'rows':[{'case_id':'case','variant':v,'expected_status':'UNCERTAIN',
        'evidence':ev,'model':{'messages':messages}} for v in ['E','F']]}))
    original_source = source.read_bytes()
    monkeypatch.setattr(runner, 'SOURCE', source)
    monkeypatch.setenv('OMNIROUTE_MODEL','groq/test-free')
    monkeypatch.setenv('OMNIROUTE_FREE_MODELS','groq/test-free')
    monkeypatch.setattr(OmniRouteProvider, 'models', classmethod(lambda cls:[{'id':'groq/test-free'}]))
    calls = []
    client = httpx.Client
    def handler(request):
        sent=json.loads(request.content)
        assert sent['messages']==messages
        calls.append(sent)
        decision={'decision':'UNCERTAIN','consistency':'UNCERTAIN','confidence':0.,'evidence_ids':[],
                  'affected_artifacts':[],'reason':'Insufficient evidence','uncertainty':'Missing caller'}
        return httpx.Response(200,json={'model':'test-free','choices':[{'finish_reason':'stop',
            'message':{'content':json.dumps(decision)}}]})
    monkeypatch.setattr(httpx,'Client',lambda **kwargs:client(transport=httpx.MockTransport(handler),**kwargs))
    monkeypatch.setattr(sys,'argv',['evaluate_omniroute.py','--max-calls','1'])
    assert runner.main()==75
    summary=next((tmp_path/'experiments').glob('**/summary.json'))
    assert json.loads(summary.read_text())['accuracy'] is None
    assert runner.main()==0
    assert len(calls)==2
    assert runner.main()==0
    assert len(calls)==2
    assert source.read_bytes()==original_source


def test_inference_error_is_excluded_and_stops_batch(tmp_path, monkeypatch):
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    (tmp_path/'llm').mkdir()
    for name in ['omniroute.py','providers.py','context.py']:(tmp_path/'llm'/name).write_text('fixture')
    source=tmp_path/'original.json'
    source.write_text(json.dumps({'rows':[{'case_id':'case','variant':'E','expected_status':'UNCERTAIN',
        'evidence':[],'model':{'messages':[{'role':'user','content':'Question\nEVIDENCE\n[]'}]}}]}))
    monkeypatch.setattr(runner,'SOURCE',source)
    monkeypatch.setattr(OmniRouteProvider,'configuration',classmethod(lambda cls:('http://localhost/v1',{},'free/test')))
    monkeypatch.setattr(OmniRouteProvider,'models',classmethod(lambda cls:[{'id':'free/test'}]))
    monkeypatch.setattr(runner.LegacyOmniRoute,'investigate',lambda *a:{'validation_error':'quota','usage':{}})
    monkeypatch.setattr(sys,'argv',['evaluate_omniroute.py'])
    assert runner.main()==2
    failure=next((tmp_path/'experiments').glob('**/last-failure.json'))
    assert json.loads(failure.read_text())['excluded_from_accuracy'] is True
    assert not list((tmp_path/'experiments').glob('**/summary.json'))
