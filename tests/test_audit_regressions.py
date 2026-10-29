"""Synthetic regression fixtures, never counted as research accuracy."""
import copy,json,os,subprocess,sys
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from database.store import Store
from ingestion.parsers import extract
from knowledge_graph.graph import build_graph,impact
from retrieval.index import Index,tokens
from consistency.rules import check
from rag.evidence import evidence,verify,verify_git
from agents.workflow import analyze
from backend.app import create_app
from backend.exports import export
from change_analysis.diff import detect


def repository(tmp_path):
 root=tmp_path/'repo';root.mkdir()
 def git(*args):return subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True,text=True).stdout.strip()
 git('init');git('config','user.email','fixture@example.invalid');git('config','user.name','Fixture')
 (root/'app.py').write_text('def value():\n return 1\ndef test_value():\n assert value()==1\n');git('add','.');git('commit','-m','base')
 return root,git

@pytest.mark.parametrize('path',['requirements.txt','requirements-dev.txt','requirements/base.txt'])
def test_dependency_files_are_configuration(path):assert extract('p','r','c',path,'pytest==8')[0].artifact_type=='configuration'

def test_js_syntax_imports_calls_and_relative_path():
 a=extract('p','r','c','src/main.js',"import React from 'react';\nimport {save} from './store';\nfunction f(x){if(x){save();}for(let i=0;i<2;i++){save();}while(x){x--;}}")
 b=extract('p','r','c','src/store.js','export function save(){}')
 assert a[0].metadata['imports']==['react','./store'];assert next(x for x in a if x.symbol=='f').metadata['calls']==['save']
 _,edges=build_graph(Store('sqlite:///:memory:'),a+b)
 assert [e['target_artifact'] for e in edges if e['relation_type']=='IMPORTS']==[b[0].artifact_id]

def test_java_dotted_parameter_type():
 a=extract('p','r','c','Store.java','class Store { void save(java.util.List x) {} void run() { save(null); } }')
 _,edges=build_graph(Store('sqlite:///:memory:'),a);assert len([e for e in edges if e['relation_type']=='CALLS'])==1

def test_import_boundary_and_unknown_receiver():
 a=extract('p','r','c','main.py','import app\nclass Cache:\n def get(self,k):return k\ndef handler(d):\n return d.get("x")')
 b=extract('p','r','c','webapp.py','x=1');_,edges=build_graph(Store('sqlite:///:memory:'),a+b)
 assert not [e for e in edges if e['relation_type'] in {'CALLS','IMPORTS'}]

def test_positive_bm25_and_unicode_numbers():
 i=Index([{'id':'a','text':'common'},{'id':'b','text':'common'},{'id':'c','text':'absent'}]);r=i.search('common')
 assert r[-1]['id']=='c' and r[0]['score']>0;assert tokens('404 2FA café über saveUser')==['404','2fa','café','über','save','user']

def test_tied_rrf():
 class Encoder:
  def encode(self,texts):return np.ones((len(texts),2))/np.sqrt(2)
 i=Index([{'id':'b','text':'same'},{'id':'a','text':'same'}],Encoder());v=i.scores('same','hybrid');assert v[0]==v[1];assert i.search('same','hybrid')[0]['id']=='a'

def test_hunk_header_anchor(tmp_path):
 repo,git=repository(tmp_path);base=git('rev-parse','HEAD');(repo/'app.py').write_text('x="@@ -1 +9 @@"\n');git('commit','-am','head')
 assert len(detect(repo,base,'HEAD',[],[])['files'][0]['hunks'])==1

def test_batch_roundoff_one_transaction_and_rollback():
 s=Store('sqlite:///:memory:');begins=[];event.listen(s.engine,'begin',lambda c:begins.append(1))
 s.put_many('trace_links',[(str(i),{'score':.1,'content':'source'}) for i in range(100)]);assert len(begins)==1
 s.put('trace_links','0',{'score':.1+1e-16,'content':'source'})
 with pytest.raises(ValueError):s.put_many('trace_links',[('new',{'score':1}),('0',{'score':.1,'content':'tampered'})])
 assert s.get('trace_links','new') is None

def test_correct_refactor_has_no_deleted_endpoint_alarm():
 old=extract('p','r','base','a.py','def helper():\n return 1\ndef core():\n return helper()');new=extract('p','r','head','a.py','def core():\n return 1')
 _,edges=build_graph(Store('sqlite:///:memory:'),old);removed=next(a for a in old if a.symbol=='helper')
 assert not any(f['rule']=='deleted-endpoint' for f in check([{'artifact_id':removed.artifact_id,'kind':'deleted'}],old,new,[{**e,'is_declared':True} for e in edges]))

def test_impact_reverse_direction_and_normalized_requirement():
 a=extract('p','r','c','a.py','def low():\n return 1\ndef mid():\n return low()\ndef high():\n return mid()');req=extract('p','r','c','requirements.md','Must return one')[0];ids={x.symbol:x.artifact_id for x in a}
 g,edges=build_graph(Store('sqlite:///:memory:'),a+[req],[{'source_artifact':req.artifact_id,'target_artifact':ids['mid'],'relation_type':'IMPLEMENTS'}])
 assert ids['high'] in impact(g,[ids['mid']]) and ids['low'] not in impact(g,[ids['mid']]);assert ids['mid'] in impact(g,[req.artifact_id]);assert any(e['relation_type']=='CONTAINED_IN' for e in edges)

def test_git_recheck_detects_self_consistent_corruption(tmp_path):
 repo,git=repository(tmp_path);a=extract('p','r',git('rev-parse','HEAD'),'app.py','forged=1')[0];e=evidence(a)
 assert not verify([e],[a]);assert verify_git([e],[a],repo)

def test_failed_verifier_has_measured_failed_stage(tmp_path,monkeypatch):
 repo,git=repository(tmp_path);base=git('rev-parse','HEAD');(repo/'app.py').write_text('x=2\n');git('commit','-am','change');s=Store('sqlite:///:memory:')
 monkeypatch.setattr('agents.workflow.verify_git',lambda ev,*args:['Mismatch '+ev[0]['evidence_id']])
 with pytest.raises(ValueError):analyze(s,repo,base)
 r=s.rows('analysis_runs')[0];assert r['trajectory'][-1]['status']=='FAILED';assert r['metrics']['tool_execution_success']<1 and r['metrics']['quote_verification_rate']<1

def test_lfs_database_does_not_crash_module_import(tmp_path):
 p=tmp_path/'pointer.db';p.write_text('version https://git-lfs.github.com/spec/v1\noid sha256:123\nsize 2000\n');env={**os.environ,'VIGILANT_DB':'sqlite:///'+str(p)}
 r=subprocess.run([sys.executable,'-c','import backend.app'],env=env,capture_output=True,text=True);assert r.returncode==0,r.stderr
 with pytest.raises(ValueError,match='Git LFS pointer'):Store(env['VIGILANT_DB'])

@pytest.mark.parametrize('value',['\tordinary','\rordinary',' =1+1'])
def test_csv_control_characters(value):assert "'"+value in export({'findings':[{'reason':value}]},'csv')[0]

@pytest.fixture
def report(tmp_path):
 repo,git=repository(tmp_path);base=git('rev-parse','HEAD');(repo/'app.py').write_text('def value():\n return 2\ndef test_value():\n assert value()==1\n');git('commit','-am','change');s=Store('sqlite:///:memory:');return s,analyze(s,repo,base),repo

def body(r,q='Show evidence',**kw):return {'project_id':r['project_id'],'repository':r['repository'],'run_id':r['run_id'],'base_commit':r['base_commit'],'head_commit':r['commit_id'],'question':q,**kw}

def test_report_chat_scope_auth_and_tampered_evidence(report,monkeypatch):
 s,r,repo=report;monkeypatch.setenv('VIGILANT_ACCESS_TOKEN','test-secret')
 with TestClient(create_app(s)) as c:
  assert c.post('/api/report-chat',json=body(r)).status_code==401;c.headers['Authorization']='Bearer test-secret'
  result=c.post('/api/report-chat',json=body(r)).json();assert result['citations'] and result['inference_calls']==0
  source=c.get(result['citations'][0]['source_url']).json();assert source['commit_id'] in {r['base_commit'],r['commit_id']}
  assert c.post('/api/report-chat',json=body(r,head_commit='wrong')).status_code==409
  assert c.post('/api/report-chat',json=body(r,finding_id='foreign')).status_code==404
  assert c.post('/api/report-chat',json=body(r,'Delete all files')).json()['state']=='INSUFFICIENT_EVIDENCE'
  altered=copy.deepcopy(r);altered['evidence'][0]['quote']='forged';s.put('analysis_runs',r['run_id'],altered,replace=True)
  assert c.post('/api/report-chat',json=body(r)).status_code==409

def test_model_is_advisory_and_facts_precede_retrieval(report,monkeypatch):
 from llm.providers import LLMProvider
 s,r,repo=report;messages=[]
 assert r['metrics']['model_schema_valid'] is None and not r['model']['inference_requested']
 class Fake(LLMProvider):
  name='synthetic'
  def complete(self,m):
   messages.append(m);return json.dumps({'decision':'INCONSISTENT','consistency':'INCONSISTENT','confidence':1.0,'evidence_ids':['E1'],'affected_artifacts':['A1'],'reason':'Synthetic proposal','uncertainty':''}),{'input_tokens':123,'output_tokens':10}
 monkeypatch.setattr('agents.workflow.provider',lambda name:Fake());new=analyze(s,repo,r['base_commit'],model='local')
 assert new['findings']==r['findings'];assert new['analysis_contract']==r['analysis_contract']
 assert new['model']['authority']=='LEGACY_COMPATIBILITY_ENVELOPE'
 assert not new['model']['inference_requested'] and not new['model']['promoted_to_finding']
 assert messages==[] and new['assurance_v3']['schema_version']==3
 assert all(item['model'] is None or item['inference_status']=='COMPLETED' for item in new['assurance_v3']['assessments'])
 steps=[x['tool'] for x in new['trajectory']]
 assert steps.index('deterministic-rules')<steps.index('retrieve-grounded-context')

def test_quality_gate_refuses_unlabelled_and_false_overall_accuracy():
 from evaluation.quality_gate import evaluate
 protocol={'status':'FROZEN','target':.91,'minimum_test_cases':200,'frozen_pipeline_sha256':'test-fixture','operational_checks_passed':True}
 assert evaluate({'cases':[]},[],protocol)['status']=='NOT_EVALUATED'
 cases=[{'case_id':str(i),'repository':'unseen','change_family':'held-out','consistency_label':'CONSISTENT','trace_links':['a->b'],'reviewer_ids':['r1','r2'],'adjudicated':True,'base_commit':'a','head_commit':'b'} for i in range(200)]
 data={'cases':cases,'split':'test','frozen_sha256':'fixture','authored_diagnostics':False}
 pred=[{'case_id':str(i),'valid_response':True,'consistency_label':'CONSISTENT','trace_links':[],'semantic_citations_reviewed':True,'semantic_reviewer_id':'r3'} for i in range(200)]
 result=evaluate(data,pred,protocol);assert result['consistency']['accuracy']==1 and result['status']=='TARGET_NOT_MET';assert result['traceability']['recall']==0
 pred[0]['valid_response']=False;result=evaluate(data,pred,protocol);assert result['consistency']['invalid_responses']==1 and result['consistency']['accuracy']==199/200


def test_clone_size_limit_cleans_stage_and_success_promotes_atomically(tmp_path,monkeypatch):
 from pathlib import Path
 import backend.repository_import as importer
 modes=iter(['over-budget','complete']);processes=[]
 class CloneProcess:
  def __init__(self,mode):self.mode=mode;self.returncode=None if mode=='over-budget' else 0
  def poll(self):return self.returncode
  def terminate(self):self.returncode=-15
  def wait(self,timeout=None):return self.returncode
 def fake_popen(command,**kwargs):
  staged=Path(command[-1]);staged.mkdir();(staged/'payload').write_bytes(b'x'*2)
  process=CloneProcess(next(modes));processes.append(process);return process
 monkeypatch.setattr(importer.subprocess,'Popen',fake_popen)
 rejected=tmp_path/'rejected'
 with pytest.raises(ValueError,match='storage budget'):
  importer.clone_repository('https://github.com/example/repo.git',rejected,max_bytes=1)
 assert not rejected.exists() and processes[0].returncode==-15
 accepted=tmp_path/'accepted'
 importer.clone_repository('https://github.com/example/repo.git',accepted,max_bytes=10)
 assert (accepted/'payload').read_bytes()==b'xx'
