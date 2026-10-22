import json,subprocess
from pathlib import Path
import pytest
from ingestion.models import artifact,Decision
from ingestion.parsers import extract
from ingestion.git import snapshot
from ingestion.service import import_repository
from database.store import Store
from retrieval.index import Index
from evaluation.metrics import ranking,classification
from rag.evidence import evidence,verify
from knowledge_graph.graph import build_graph,impact
from consistency.rules import check
from llm.providers import validate,NoLLMProvider

def test_stable_identity():
 a=artifact('p','r','a','a.py','function','f','return 1',1);b=artifact('p','r','b','a.py','function','f','return 2',20)
 assert a.artifact_id==b.artifact_id and a.content_hash!=b.content_hash
@pytest.mark.parametrize('path,code,symbol',[('a.py','def f():\n return 1','f'),('a.java','class A { void f() {} }','A.f()'),('a.js','function f() {return 1}','f'),('a.ts','function f(x:number):number {return x}','f')])
def test_languages(path,code,symbol):assert symbol in [x.symbol for x in extract('p','r','c',path,code)]
def test_overloads():
 a=extract('p','r','c','C.java','class C { void x(int a) {} void x(String a) {} }');assert len({x.artifact_id for x in a})==len(a)
def test_api_prefix():
 a=extract('p','r','c','a.py','router = APIRouter(prefix="/items")\n@router.get("/{id}")\ndef read():\n return 1')
 assert next(x for x in a if x.artifact_type=='api').metadata['route']=='/items/{id}'
def test_parse_error_visible():assert extract('p','r','c','bad.py','def :')[0].metadata['parse_error']
def test_git_read_is_snapshot(tmp_path):
 def g(*a):return subprocess.run(['git','-C',str(tmp_path),*a],check=True,capture_output=True)
 g('init');g('config','user.email','test@example.invalid');g('config','user.name','Test');(tmp_path/'a.py').write_text('def f():\n return 1\n');g('add','.');g('commit','-m','base');(tmp_path/'a.py').write_text('raise Exception()')
 assert list(snapshot(tmp_path,'HEAD'))[0][1].startswith('def f')
 s=Store('sqlite:///'+str(tmp_path/'test.db'));a=import_repository(s,tmp_path);assert a==import_repository(s,tmp_path)
def test_immutable_conflict():
 s=Store('sqlite:///:memory:');s.put('projects','p',{'name':'one'})
 with pytest.raises(ValueError):s.put('projects','p',{'name':'two'})
def test_retrieval_and_filter():
 i=Index([{'id':'1','text':'banana yellow fruit','kind':'code'},{'id':'2','text':'red apple','kind':'test'}]);assert i.search('banana','tfidf',1)[0]['id']=='1';assert i.search('apple','bm25',1,{'kind':'code'})[0]['id']=='1'
def test_empty_text():assert Index([{'id':'1','text':''}]).search('x')[0]['id']=='1'
def test_metrics():
 m,_=ranking({'q':['a','b']},{'q':['x','a','b']});assert m['mrr']==.5;assert m['map']==pytest.approx((.5+2/3)/2)
 assert classification({'a'},{'b'},{'a','b','c'})['false_positive_rate']==.5
@pytest.mark.parametrize('text',['hello\n','hello\n\n','','def f():\n return 1'])
def test_evidence_newlines(text):
 a=artifact('p','r','c','x.py','source_file','',text);assert verify([evidence(a)],[a])==[]
def test_forged_quote():
 a=artifact('p','r','c','x.py','function','f','return 1');e=evidence(a);e['quote']='return 2';assert verify([e],[a])
def test_unknown_model_citations():
 data={'decision':'AFFECTED','consistency':'AFFECTED','confidence':.5,'evidence_ids':['invented'],'affected_artifacts':[],'reason':'x','uncertainty':''}
 with pytest.raises(ValueError):validate(json.dumps(data),[])
def test_contradictory_model_labels():
 with pytest.raises(ValueError):Decision(decision='INCONSISTENT',consistency='UNCERTAIN',confidence=.5,evidence_ids=['a'],affected_artifacts=[],reason='x',uncertainty='')
def test_no_model_is_uncertain():assert NoLLMProvider().investigate('x',[])['decision']['decision']=='UNCERTAIN'
def test_graph_rules():
 before=extract('p','r','a','x.py','def f():\n return 1\ndef test_f():\n assert f()==1');after=extract('p','r','b','x.py','def f():\n return 2\ndef test_f():\n assert f()==1');s=Store('sqlite:///:memory:');g,edges=build_graph(s,before);f=next(a for a in before if a.symbol=='f');t=next(a for a in before if a.symbol=='test_f');assert t.artifact_id in impact(g,{f.artifact_id});out=check([{'artifact_id':f.artifact_id}],before,after,edges);assert any(x['status']=='POTENTIAL_INCONSISTENCY' for x in out)

def test_inferred_lost_edge_is_not_confirmed_broken_trace():
 before=extract('p','r','a','x.py','def removed():\n return 1\ndef caller():\n return removed()')
 after=extract('p','r','b','x.py','def caller():\n return removed()')
 store=Store('sqlite:///:memory:');_,edges=build_graph(store,before)
 lost=next(edge for edge in edges if edge['relation_type']=='CALLS')

 findings=check([{'artifact_id':lost['target_artifact']}],before,after,[lost])

 assert any(item['rule']=='inferred-edge-endpoint-removed' and item['status']=='POTENTIAL_INCONSISTENCY' for item in findings)
 assert not any(item['status']=='BROKEN_TRACE' for item in findings)

def test_declared_lost_edge_is_broken_trace():
 requirement=artifact('p','r','a','requirements/REQ-1.md','requirement','','Must exist')
 implementation=artifact('p','r','a','src.py','source_file','','def f(): pass')
 after=[requirement]
 store=Store('sqlite:///:memory:')
 _,edges=build_graph(store,[requirement,implementation],[{'source_artifact':requirement.artifact_id,'target_artifact':implementation.artifact_id,'relation_type':'IMPLEMENTS'}])
 assert 'is_declared' not in store.get('graph_edges',edges[0]['id'])
 build_graph(store,[requirement,implementation],[{'source_artifact':requirement.artifact_id,'target_artifact':implementation.artifact_id,'relation_type':'IMPLEMENTS'}])

 findings=check([{'artifact_id':implementation.artifact_id}], [requirement,implementation], after, edges)

 assert any(item['rule']=='deleted-endpoint' and item['status']=='BROKEN_TRACE' for item in findings)

def test_deleted_implementation_does_not_report_test_as_unchanged():
 before=extract('p','r','a','x.py','def f():\n return 1\ndef test_f():\n assert f()==1')
 after=extract('p','r','b','x.py','def test_f():\n assert f()==1')
 store=Store('sqlite:///:memory:');_,edges=build_graph(store,before)
 implementation=next(a for a in before if a.symbol=='f')
 findings=check([{'artifact_id':implementation.artifact_id,'kind':'deleted'}],before,after,edges)
 assert not any(item['rule']=='implementation-changed-test-unchanged' for item in findings)

def test_last_deleted_test_is_reported_as_missing_test_once():
 before=extract('p','r','a','x.py','def f():\n return 1\ndef test_f():\n assert f()==1')
 after=[a for a in before if a.symbol!='test_f']
 store=Store('sqlite:///:memory:');_,edges=build_graph(store,before)
 test=next(a for a in before if a.symbol=='test_f')
 implementation=next(a for a in before if a.symbol=='f')
 findings=check([{'artifact_id':test.artifact_id,'kind':'deleted'}],before,after,edges)
 assert sum(item['status']=='MISSING_TEST' for item in findings)==1
 assert not any(item['status']=='BROKEN_TRACE' and implementation.artifact_id in item['affected_artifacts'] for item in findings)
def test_real_truth_endpoints():
 from scripts.prepare_data import validate
 for p in Path('data/prepared').glob('*.json'):
  d=json.loads(p.read_text())
  if 'sources' in d:assert validate(d)['dangling_links']==0
