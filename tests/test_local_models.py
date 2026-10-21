import json
import sqlite3
from types import SimpleNamespace
import pytest
from ingestion.models import artifact
from rag.evidence import evidence,paired_versions,verify
from llm.context import request
from llm.providers import LLMProvider,uncertain
from llm.ollama import OllamaProvider
from scripts.evaluate_local_models import run,metrics,validate_dataset
from scripts.export_graph import export


def pair():
    text='\n'.join('line '+str(i) for i in range(1,501))
    before=artifact('p','r','base','a.py','source_file','',text)
    after=artifact('p','r','head','a.py','source_file','',text.replace('line 450','CHANGED CONTRACT'))
    changes={'artifacts':[{'artifact_id':before.artifact_id,'new_artifact_id':after.artifact_id,'artifact_type':'source_file','file':'a.py'}],
        'files':[{'old_path':'a.py','new_path':'a.py','hunks':[{'old_start':450,'new_start':450}]}]}
    return paired_versions(changes,[before],[after]),[before,after]


def test_changed_window_verified_and_prompt_retains_tail():
    ev,artifacts=pair();assert not verify(ev,artifacts)
    assert all(e['start_line']>400 for e in ev)
    messages,selected,_,_=request('Check contract',ev)
    payload=json.loads(messages[-1]['content'])
    assert len(selected)==2 and 'CHANGED CONTRACT' in messages[-1]['content']
    assert not payload['excerpt_text_truncated']
    assert '"decision": "UNCERTAIN"' not in messages[0]['content']
    assert all(x['excerpt']==e['quote'] for x,e in zip(payload['evidence'],selected))


def test_pair_not_split_by_budget():
    ev,_=pair();assert request('check',ev,limit=1)[1]==[]
    assert request('check',ev,budget=1)[1]==[]
    with pytest.raises(ValueError):request('x'*8001,ev)


def test_legacy_prompt_still_bounded():
    ev,_=pair();messages,_,_,_=LLMProvider().legacy_investigation_request('check',ev)
    payload=json.loads(messages[-1]['content'].split('\nEVIDENCE\n')[1])
    assert all(len(x['excerpt'])<=400 for x in payload)


@pytest.mark.parametrize('url',['https://example.com','http://localhost:11434/x','http://user:secret@localhost:11434'])
def test_ollama_local_only(monkeypatch,url):
    monkeypatch.setenv('OLLAMA_URL',url)
    with pytest.raises(ValueError):OllamaProvider.base_url()


def test_ollama_schema_and_identity(monkeypatch):
    calls=[]
    class Client:
        def __init__(self,**kwargs):assert kwargs['trust_env'] is False
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def get(self,url):return self.response({'models':[{'name':'qwen3:8b','digest':'sha256:test','size':123}]})
        def post(self,url,json):
            calls.append((url,json))
            if url.endswith('/show'):return self.response({'capabilities':['thinking']})
            return self.response({'done':True,'done_reason':'stop','message':{'content':uncertain('insufficient').model_dump_json()},'model':'qwen3:8b','eval_count':12})
        def response(self,data):return SimpleNamespace(raise_for_status=lambda:None,json=lambda:data)
    monkeypatch.setattr('llm.ollama.httpx.Client',Client)
    engine=OllamaProvider('qwen3:8b');result=engine.investigate('check',[])
    assert result['validation_error'] is None
    body=calls[-1][1];assert body['keep_alive']==0 and body['think'] is False
    assert body['format']['type']=='object' and body['options']['num_ctx']==8192
    assert body['format']['properties']['evidence_ids']['maxItems']==0
    assert result['usage']['local_model']['digest']=='sha256:test'
    ev,_=pair();engine.investigate('check',ev)
    body=calls[-1][1]
    assert body['format']['properties']['evidence_ids']['items']['enum']==['E1','E2']
    assert body['format']['properties']['affected_artifacts']['items']['enum']==['A1','A2']
    with pytest.raises(ValueError):OllamaProvider('qwen3:cloud').preflight()


@pytest.mark.parametrize('eids,aids,valid', [(['E1'],[],True), (['E1'],['A2'],True),
                                         (['E99'],[],False), (['E1'],['a.py'],False)])
def test_citation_resolution_stays_strict_and_derives_references(eids,aids,valid):
    ev,_=pair()
    class Response(OllamaProvider):
        def complete(self,messages):
            obj=uncertain('Insufficient contract evidence').model_dump()
            obj.update(evidence_ids=eids,affected_artifacts=aids)
            return json.dumps(obj),{}
    result=Response().investigate('check',ev)
    assert (result['validation_error'] is None)==valid
    assert result['raw_output']
    if valid:
        assert result['decision']['evidence_ids']==[ev[0]['evidence_id']]
        assert result['cited_artifacts']==[ev[0]['artifact_id']]
        assert result['decision']['affected_artifacts']==([ev[1]['artifact_id']] if aids else [])
    else:
        assert result['cited_artifacts']==[]


def test_finite_resume_and_labels_never_in_prompt(tmp_path):
    class Fake(LLMProvider):
        count=0
        def __init__(self,model):self.model=model
        def preflight(self):return {'model':self.model,'digest':'test-digest'}
        def complete(self,messages):
            Fake.count+=1;assert 'expected_status' not in str(messages)
            return uncertain('No sufficient evidence').model_dump_json(),{'output_tokens':10}
    data={'split':'diagnostic','cases':[{'case_id':str(i),'question':'check','evidence':[],'expected_status':'UNCERTAIN'} for i in range(2)]}
    first=run(data,['test'],tmp_path,1,Fake)
    assert first['results'][0]['metrics'] is None
    second=run(data,['test'],tmp_path,1,Fake)
    assert second['status']=='COMPLETED' and Fake.count==2
    assert second['results'][0]['metrics']['accuracy']==1
    assert second['results'][0]['target_status']=='NOT_ESTABLISHED'
    assert run(data,['test'],tmp_path,1,Fake)['new_calls']==0
    data['cases'][0]['question']='different';run(data,['test'],tmp_path,1,Fake);assert Fake.count==3


def test_invalid_outputs_count_as_errors_and_test_selection_rejected():
    cases=[{'expected_status':'UNCERTAIN'}]
    result={'decision':{'decision':'UNCERTAIN'},'validation_error':'invalid JSON','seconds':1}
    assert metrics(cases,[result])['accuracy']==0
    assert metrics(cases,[]) is None
    with pytest.raises(ValueError):validate_dataset({'split':'test','cases':[]},['a','b'])


def test_export_scope_and_graphml(tmp_path):
    db=tmp_path/'graph.db'
    with sqlite3.connect(db) as c:
        for table in ['graph_nodes','graph_edges']:
            c.execute('CREATE TABLE '+table+'(id TEXT,repository TEXT,commit_id TEXT,payload TEXT)')
        for id,repo in [('a','r'),('b','r'),('unrelated','other')]:
            c.execute('INSERT INTO graph_nodes VALUES(?,?,?,?)',(id,repo,'c',json.dumps({'artifact_id':id,'repository':repo,'commit_id':'c'})))
        edge={'id':'e','source_artifact':'a','target_artifact':'b','relation_type':'CALLS','evidence':['a','b']}
        c.execute('INSERT INTO graph_edges VALUES(?,?,?,?)',('e','r','c',json.dumps(edge)))
    result=export(db,'r','c',tmp_path/'out');assert result['nodes']==2 and result['edges']==1
    import networkx as nx
    g=nx.read_graphml(tmp_path/'out/graph.graphml');assert set(g.nodes)=={'a','b'}


def test_truncated_generation_retained_and_counted_invalid():
    class Incomplete(LLMProvider):
        def complete(self,messages):return uncertain('partial').model_dump_json(),{'output_tokens':20,'completion_error':'length limit'}
    result=Incomplete().investigate('check',[])
    assert result['raw_output'] and result['validation_error']
    assert metrics([{'expected_status':'UNCERTAIN'}],[result])['accuracy']==0


def test_balanced_context_keeps_changed_code_caller_and_test():
    from rag.evidence import balanced_change_context
    before=[];after=[]
    specs=[('api.py','source_file','', 'route = "/items"'),
           ('client.py','function','read_items','return get("/items")'),
           ('tests/test_api.py','test_method','test_items','assert get("/items").status == 200'),
           ('requirements.md','requirement','','The items route returns status 200.')]
    for file,kind,symbol,text in specs:
        before.append(artifact('p','r','base',file,kind,symbol,text))
        after.append(artifact('p','r','head',file,kind,symbol,text.replace('/items','/catalog') if file=='api.py' else text))
    changes={'artifacts':[{'artifact_id':before[0].artifact_id,'new_artifact_id':after[0].artifact_id}],
             'files':[{'old_path':'api.py','new_path':'api.py','hunks':[{'old_start':1,'new_start':1}],
                       'patch':'-route = "/items"\n+route = "/catalog"'}]}
    ev,report=balanced_change_context(changes,before,after)
    assert not verify(ev,before+after)
    _,selected,_,_=request('check',ev,budget=18000)
    assert {'api.py','client.py','tests/test_api.py','requirements.md'} <= {e['file'] for e in selected}
    assert {e['commit'] for e in selected if e['file']=='api.py'}=={'base','head'}
    assert report['semantic_sufficiency']=='UNREVIEWED'


def test_api_model_selection_reaches_worker(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    import backend.app as backend
    from database.store import Store
    store=Store('sqlite:///'+str(tmp_path/'queue.db'));seen=[]
    store.put('repositories','r',{'repository':'r','project_id':'p','path':'repo'})
    monkeypatch.setattr(backend,'revision',lambda path,ref:'pinned-'+ref)
    monkeypatch.setattr(OllamaProvider,'preflight',lambda self:{'model':self.model})
    def analyze(*args,**kwargs):seen.append(kwargs);return {'run_id':'result'}
    monkeypatch.setattr(backend,'analyze',analyze)
    with TestClient(backend.create_app(store)) as client:
        good=client.post('/api/analysis/run',json={'repository':'r','model':'ollama','ollama_model':'qwen3:14b'})
        assert good.status_code==202
        assert client.post('/api/analysis/run',json={'repository':'r','model':'ollama','ollama_model':'unknown'}).status_code==400
    assert seen==[{'ollama_model':'qwen3:14b'}]
