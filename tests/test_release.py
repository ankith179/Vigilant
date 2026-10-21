"""Regression checks for local release reliability, not model accuracy."""
import hashlib
import json
import sqlite3
import threading
import time
import pytest

from fastapi.testclient import TestClient
from database.store import Store
from ingestion.models import artifact,digest
from backend.app import create_app


def test_restore_preserves_snapshot_and_existing_work(tmp_path,monkeypatch):
    from scripts import restore_checkpoint as restore
    monkeypatch.setattr(restore,'ROOT',tmp_path)
    source=tmp_path/'data/snapshots/vigilant.db';source.parent.mkdir(parents=True)
    with sqlite3.connect(source)as c:
        c.execute('CREATE TABLE repositories(id TEXT PRIMARY KEY,payload TEXT)')
        c.execute('INSERT INTO repositories VALUES (?,?)',('r',json.dumps({'path':r'C:\old\data\repos\example'})))
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    restore.main();restore.main()
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before
    with sqlite3.connect(tmp_path/'data/vigilant.db')as c:
        assert json.loads(c.execute('SELECT payload FROM repositories').fetchone()[0])['path']==str(tmp_path/'data/repos/example')
        c.execute('INSERT INTO repositories VALUES (?,?)',('custom','{}'))
    restore.main()
    with sqlite3.connect(tmp_path/'data/vigilant.db')as c:assert c.execute('SELECT count(*) FROM repositories').fetchone()[0]==2


def test_restore_worktree_metadata_uses_portable_paths(tmp_path, monkeypatch):
    from scripts import restore_checkpoint as restore
    monkeypatch.setattr(restore, 'ROOT', tmp_path)
    entry = tmp_path/'data/repos/example/.git/worktrees/case'
    worktree = tmp_path/'data/changebench/case'
    entry.mkdir(parents=True)
    worktree.mkdir(parents=True)
    monkeypatch.setattr(restore.subprocess, 'run', lambda *a, **kw: None)
    restore.main()
    assert (worktree/'.git').read_bytes() == ('gitdir: '+entry.as_posix()+'\n').encode('utf-8')
    assert (entry/'gitdir').read_bytes() == ((worktree/'.git').as_posix()+'\n').encode('utf-8')


def test_auth_exports_and_free_default(monkeypatch):
    monkeypatch.setenv('VIGILANT_ACCESS_TOKEN','secret');monkeypatch.delenv('VIGILANT_FREE_ONLY',raising=False)
    s=Store('sqlite:///:memory:');s.put('repositories','r',{'repository':'r','project_id':'p','path':'unused'})
    s.put('analysis_runs','report',{'run_id':'report','findings':[{'status':'UNCERTAIN','reason':'=BAD() <script>alert(1)</script>'}],'evidence':[]})
    with TestClient(create_app(s))as c:
        assert c.get('/api/auth/status').json()['free_only']
        for path in ['/api/stats','/projects','/api/reports/report','/api/metrics']:assert c.get(path).status_code==401
        c.headers['Authorization']='Bearer secret'
        assert c.get('/api/stats').status_code==200
        assert c.post('/api/analysis/run',json={'repository':'r','model':'cloud'}).status_code==400
        assert c.get('/api/reports/report/export?format=json').json()['run_id']=='report'
        assert "'=BAD()" in c.get('/api/reports/report/export?format=csv').text
        out=c.get('/api/reports/report/export?format=html').text
        assert '<script>'not in out and '&lt;script&gt;'in out
        assert c.get('/api/reports/report/export?format=invalid').status_code==422
        assert 'vigilant_jobs' in c.get('/api/metrics').text

def test_free_policy_applies_to_command_line_provider_selection(monkeypatch):
    from llm.providers import provider
    monkeypatch.delenv('VIGILANT_FREE_ONLY',raising=False)
    for name in ['cloud','gemini','claude']:
        with pytest.raises(ValueError,match='free-only'):provider(name)
    assert provider('none').name

def test_historical_audit_requires_exact_provider_source(tmp_path):
    # Historical runs must remain verifiable after the provider implementation evolves.
    import sys
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    monkey=pytest.MonkeyPatch()
    try:
        monkey.syspath_prepend(str(root/'scripts'))
        from scripts.audit_rag_observations import audit
        assert audit(root/'evaluation/frozen/20261007/providers.py.txt')['verified_observations']==251
        altered=tmp_path/'provider.txt';altered.write_text('different provider implementation')
        with pytest.raises(AssertionError,match='dataset configuration'):audit(altered)
    finally:monkey.undo()


def test_restart_recovers_only_unstarted_jobs(tmp_path,monkeypatch):
    import backend.app as backend
    s=Store('sqlite:///'+str(tmp_path/'jobs.db'));calls=[]
    s.put('repositories','r',{'repository':'r','project_id':'p','path':'repo'})
    request={'repository':'r','base':'base','head':'head','model':'none','semantic':False}
    for name,status in [('pending','QUEUED'),('inflight','RUNNING')]:s.put('analysis_runs',name,{'run_id':name,'kind':'job','request':request,'status':status})
    def analyze(*args):calls.append(args);return {'run_id':'result'}
    monkeypatch.setattr(backend,'analyze',analyze)
    with TestClient(create_app(s))as c:
        end=time.monotonic()+5
        while time.monotonic()<end and c.get('/api/reports/pending').json()['status']!='COMPLETED':time.sleep(.01)
        assert c.get('/api/reports/pending').json()['result_run_id']=='result'
        assert c.get('/api/reports/inflight').json()['status']=='FAILED'
    assert len(calls)==1 and calls[0][2:4]==('base','head')


def test_queue_capacity_and_revision_pinning(tmp_path,monkeypatch):
    import backend.app as backend
    gate=threading.Event();s=Store('sqlite:///'+str(tmp_path/'queue.db'))
    s.put('repositories','r',{'repository':'r','project_id':'p','path':'repo'})
    monkeypatch.setattr(backend,'revision',lambda path,ref:'pinned-'+ref)
    def analyze(*args):gate.wait(10);return {'run_id':'result'}
    monkeypatch.setattr(backend,'analyze',analyze)
    with TestClient(create_app(s))as c:
        try:
            ids=[]
            for _ in range(20):
                r=c.post('/api/analysis/run',json={'repository':'r'});assert r.status_code==202;ids.append(r.json()['job_id'])
            assert c.post('/api/analysis/run',json={'repository':'r'}).status_code==429
            assert s.get('analysis_runs',ids[0])['request']['head']=='pinned-HEAD'
        finally:gate.set()
    assert all(s.get('analysis_runs',i)['status']=='COMPLETED'for i in ids)


def test_impact_scope_pagination_and_rag():
    s=Store('sqlite:///:memory:')
    for i in range(40):s.put('analysis_runs',str(i),{'run_id':str(i),'repository':'r','commit_id':'c','affected_artifacts':[{'artifact_id':str(i),'path':['seed',str(i)]}]})
    s.put('analysis_runs','other',{'run_id':'other','repository':'other','commit_id':'c','affected_artifacts':[{'artifact_id':'wrong'}]})
    a=artifact('p','r','c','requirements.md','requirement','','The calculator shall add two numbers.',1)
    s.put('artifacts',digest(a.artifact_id,a.commit_id),a.model_dump())
    with TestClient(create_app(s))as c:
        first=c.get('/api/impact?repository=r&commit_id=c&limit=20').json();last=c.get('/api/impact?repository=r&commit_id=c&limit=20&offset=20').json()
        assert len(first['items'])==len(last['items'])==20 and not last['has_more']
        assert all(x['repository']=='r'for x in first['items']+last['items'])
        rag=c.get('/api/rag',params={'repository':'r','commit_id':'c','query':'calculator add'}).json()
        assert rag['source_verified']and not rag['semantic_entailment_verified']
        assert rag['items'][0]['quote']==a.content
        assert c.get('/api/rag',params={'repository':'r','commit_id':'absent','query':'add'}).status_code==404


def test_watcher_rejects_state_from_another_repository(tmp_path):
    from scripts.watch_repository import read_previous
    state=tmp_path/'state.json'
    state.write_text(json.dumps({'repository':str(tmp_path/'old'),'last_commit':'old-ref'}))
    with pytest.raises(ValueError,match='another repository'):read_previous(state,tmp_path/'new')

def test_report_survives_unavailable_process_telemetry(tmp_path,monkeypatch):
    from evaluation import runs
    monkeypatch.setattr(runs,'ROOT',tmp_path)
    def unavailable():raise runs.psutil.NoSuchProcess(123)
    monkeypatch.setattr(runs.psutil,'Process',unavailable)
    directory,report=runs.save_run('pipeline',{'status':'COMPLETED','findings':[]})
    assert report['status']=='COMPLETED' and report['rss_mib_at_save'] is None
    assert report['memory_measurement_error']=='NoSuchProcess'
    assert json.loads((directory/'results.json').read_text())==report
