import subprocess,time
from fastapi.testclient import TestClient
from database.store import Store
from agents.workflow import analyze
from ingestion.service import import_repository
from ingestion.git import revision
from change_analysis.diff import detect
from rag.evidence import verify

def repository(path):
 path.mkdir(exist_ok=True)
 def git(*args):return subprocess.run(['git','-C',str(path),*args],check=True,capture_output=True,text=True).stdout.strip()
 git('init');git('config','user.email','test@example.invalid');git('config','user.name','Test')
 (path/'app.py').write_text('def value():\n    return 1\n\ndef test_value():\n    assert value() == 1\n')
 git('add','.');git('commit','-m','base');return git

def test_end_to_end(tmp_path):
 p=tmp_path/'repo';g=repository(p);base=revision(p);(p/'app.py').write_text('def value():\n    return 2\n\ndef test_value():\n    assert value() == 1\n');g('commit','-am','drift');s=Store('sqlite:///'+str(tmp_path/'store.db'))
 r=analyze(s,p,base);assert r['status']=='COMPLETED';assert any(f['status']=='POTENTIAL_INCONSISTENCY' for f in r['findings']);assert all(x['status']=='SUCCESS' for x in r['trajectory']);assert not verify(r['evidence'],s.artifacts(r['repository'],base)+s.artifacts(r['repository'],r['commit_id']))

def test_rename_and_delete(tmp_path):
 p=tmp_path/'repo';g=repository(p);s=Store('sqlite:///:memory:');a=import_repository(s,p);before=s.artifacts(a['repository'],a['commit_id']);g('mv','app.py','renamed.py');g('commit','-m','rename');b=import_repository(s,p);after=s.artifacts(b['repository'],b['commit_id']);r=detect(p,a['commit_id'],b['commit_id'],before,after);assert any(x['kind']=='renamed' and x.get('new_artifact_id') for x in r['artifacts']);g('rm','renamed.py');g('commit','-m','delete');c=import_repository(s,p);r=detect(p,b['commit_id'],c['commit_id'],after,s.artifacts(c['repository'],c['commit_id']));assert all(x['kind']=='deleted' for x in r['artifacts'])

def test_api_background_and_scoping(tmp_path):
 from backend.app import create_app
 p=tmp_path/'repo';g=repository(p);base=revision(p);(p/'app.py').write_text('def value():\n    return 2\n\ndef test_value():\n    assert value() == 1\n');g('commit','-am','change');s=Store('sqlite:///'+str(tmp_path/'api.db'));r=import_repository(s,p)
 with TestClient(create_app(s)) as c:
  assert c.get('/api/health').status_code==200
  assert c.get('/api/artifacts',params={'repository':r['repository']}).json()['returned']==3
  assert c.get('/api/artifacts',params={'repository':'absent'}).json()['returned']==0
  assert c.post('/api/repositories/import',json={'path':'/tmp'}).status_code==400
  response=c.post('/api/analysis/run',json={'repository':r['repository'],'base':base});assert response.status_code==202;job=response.json()['job_id'];end=time.monotonic()+15
  while time.monotonic()<end:
   status=c.get('/api/reports/'+job).json()
   if status['status'] in ['COMPLETED','FAILED']:break
   time.sleep(.05)
  assert status['status']=='COMPLETED',status
  assert c.get('/api/reports/'+status['result_run_id']).json()['evidence']

def test_existing_project_name_preserved(tmp_path):
 p=tmp_path/'repo';repository(p);s=Store('sqlite:///:memory:');s.put('projects','custom',{'project_id':'custom','name':'My project'});import_repository(s,p,project='custom');assert s.get('projects','custom')['name']=='My project'
