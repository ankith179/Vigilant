"""Cooperative job lifecycle fixtures; no model or independent accuracy labels."""
import json,multiprocessing,os,signal,subprocess,sys,threading,time
from datetime import datetime,timedelta,timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from agents.control import RunControl,InvestigationStopped
from database.store import Store
import backend.app as backend


def wait_status(client,job,terminal):
    end=time.monotonic()+5
    while time.monotonic()<end:
        row=client.get('/api/reports/'+job).json()
        if row.get('status') in terminal:return row
        time.sleep(.01)
    raise AssertionError(row)


def blocking_analysis(*args,**kwargs):
    Path(args[1],'analysis-worker-entered').write_text('started',encoding='utf-8')
    time.sleep(30)
    return {'run_id':kwargs['run_id']}


def crashing_analysis(*args,**kwargs):
    Path(args[1],'analysis-worker-entered').write_text('started',encoding='utf-8')
    os._exit(17)


def descendant_analysis(*args,**kwargs):
    Path(args[1],'analysis-worker-entered').write_text('started',encoding='utf-8')
    child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                           creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    Path(args[1],'descendant-pid').write_text(str(child.pid),encoding='ascii')
    time.sleep(60)


def wait_for_worker(path,name='analysis-worker-entered',timeout=30):
    marker=Path(path,name);end=time.monotonic()+timeout
    while time.monotonic()<end:
        if marker.exists():return
        time.sleep(.05)
    raise AssertionError('Isolated analysis worker did not enter the runner')


def pid_alive(pid):
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        api=ctypes.WinDLL('kernel32',use_last_error=True)
        api.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];api.OpenProcess.restype=wintypes.HANDLE
        api.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];api.GetExitCodeProcess.restype=wintypes.BOOL
        api.CloseHandle.argtypes=[wintypes.HANDLE];api.CloseHandle.restype=wintypes.BOOL
        handle=api.OpenProcess(0x1000,False,pid)
        if not handle:return False
        try:
            code=wintypes.DWORD()
            return bool(api.GetExitCodeProcess(handle,ctypes.byref(code))) and code.value==259
        finally:api.CloseHandle(handle)
    try:os.kill(pid,0);return True
    except OSError:return False


def probe_server_lock(database,result_queue):
    store=Store('sqlite:///'+database)
    try:
        try:
            release=backend._acquire_server_lock(store)
        except RuntimeError:
            result_queue.put('rejected')
        else:
            result_queue.put('acquired')
            if release:release()
    finally:store.engine.dispose()


def run_server_until_crashed(database,repo_path,result_queue):
    store=Store(database)
    store.put('repositories','r',{'repository':'r','project_id':'p','path':repo_path})
    backend.revision=lambda path,ref:'f'*40
    with TestClient(backend.create_app(store,analysis_runner=descendant_analysis)) as client:
        response=client.post('/api/analysis/run',json={'repository':'r','timeout_seconds':120})
        result_queue.put(response.json()['job_id'])
        time.sleep(120)
    store.engine.dispose()


def detect_replay(*args,**kwargs):
    Path(args[1],'replayed-after-server-crash').write_text('unexpected',encoding='ascii')
    time.sleep(30)


@pytest.fixture
def queued(monkeypatch):
    store=Store('sqlite:///:memory:');store.put('repositories','r',{'repository':'r','project_id':'p','path':'fixture'})
    monkeypatch.setattr(backend,'revision',lambda path,ref:'f'*40)
    entered=threading.Event();release=threading.Event();calls=[]
    def analyze(*args,control,**kwargs):
        calls.append(args);entered.set();assert release.wait(10);control.check()
        control.begin_publication();return {'run_id':'completed-fixture'}
    monkeypatch.setattr(backend,'analyze',analyze)
    yield store,entered,release,calls
    release.set();store.engine.dispose()


def test_control_cancel_timeout_and_publication_boundary():
    clock=[0];control=RunControl(2,clock=lambda:clock[0]);control.check();clock[0]=2
    with pytest.raises(InvestigationStopped) as exc:control.check()
    assert exc.value.status=='TIMED_OUT'
    other=RunControl();assert other.cancel()
    with pytest.raises(InvestigationStopped) as exc:other.check()
    assert exc.value.status=='CANCELLED'
    published=RunControl(2,clock=lambda:clock[0]);published.begin_publication();clock[0]=100
    assert not published.cancel();published.check()


def test_posix_group_escalates_even_when_worker_leader_exits(monkeypatch):
    signals=[]
    class Process:
        pid=123
        def join(self,timeout):pass
        def is_alive(self):return False
        def kill(self):pytest.fail('Exited group leader must not be killed again')
    monkeypatch.setattr(backend.os,'killpg',lambda pid,value:signals.append(value),raising=False)
    monkeypatch.setattr(backend.signal,'SIGTERM',15,raising=False)
    monkeypatch.setattr(backend.signal,'SIGKILL',9,raising=False)
    backend._stop_worker_tree(Process(),None)
    assert signals==[backend.signal.SIGTERM,backend.signal.SIGKILL]


def test_queued_cancel_bounds_retained_queue_and_never_starts(queued):
    store,entered,release,calls=queued
    with TestClient(backend.create_app(store)) as client:
        try:
            first=client.post('/api/analysis/run',json={'repository':'r'}).json()['job_id'];assert entered.wait(3)
            ids=[client.post('/api/analysis/run',json={'repository':'r'}).json()['job_id'] for _ in range(19)]
            assert client.post('/api/analysis/run',json={'repository':'r'}).status_code==429
            stopped=client.post('/api/analysis/jobs/'+ids[0]+'/cancel').json();assert stopped['status']=='CANCELLED'
            assert client.post('/api/analysis/jobs/'+ids[0]+'/cancel').json()==stopped
            assert client.post('/api/analysis/run',json={'repository':'r'}).status_code==429
            assert len(calls)==1
        finally:release.set()
        assert wait_status(client,first,{'COMPLETED'})['status']=='COMPLETED'
        assert wait_status(client,ids[-1],{'COMPLETED'})['status']=='COMPLETED'
        assert client.post('/api/analysis/run',json={'repository':'r'}).status_code==202
    assert len(calls)==20


def test_running_cancel_is_request_until_safe_boundary(queued):
    store,entered,release,calls=queued
    with TestClient(backend.create_app(store)) as client:
        try:
            job=client.post('/api/analysis/run',json={'repository':'r'}).json()['job_id'];assert entered.wait(3)
            row=client.post('/api/analysis/jobs/'+job+'/cancel').json();assert row['status']=='CANCEL_REQUESTED'
            assert client.get('/api/reports/'+job).json()['status']=='CANCEL_REQUESTED'
        finally:release.set()
        row=wait_status(client,job,{'CANCELLED'});assert row['cancel_requested_at']
        assert 'result_run_id' not in row
        assert 'status="cancelled"} 1' in client.get('/api/metrics').text


def test_timeout_observed_after_inflight_operation_and_queued_expiry(monkeypatch,queued):
    store,entered,release,calls=queued;clock=[0];real=RunControl
    monkeypatch.setattr(backend,'RunControl',lambda seconds:real(seconds,clock=lambda:clock[0]))
    with TestClient(backend.create_app(store)) as client:
        try:
            first=client.post('/api/analysis/run',json={'repository':'r','timeout_seconds':1}).json()['job_id'];assert entered.wait(3)
            second=client.post('/api/analysis/run',json={'repository':'r','timeout_seconds':1}).json()['job_id']
            clock[0]=5
            assert client.get('/api/reports/'+first).json()['status']=='RUNNING'
        finally:release.set()
        assert wait_status(client,first,{'TIMED_OUT'})['status']=='TIMED_OUT'
        assert wait_status(client,second,{'TIMED_OUT'})['status']=='TIMED_OUT'
    assert len(calls)==1


def test_restart_never_replays_cancelled_or_expired_work(monkeypatch):
    store=Store('sqlite:///:memory:');calls=[]
    store.put('repositories','r',{'repository':'r','project_id':'p','path':'fixture'})
    request={'repository':'r','base':'f'*40,'head':'f'*40}
    for name,status in [('cancel','CANCEL_REQUESTED'),('expired','QUEUED'),('active','RUNNING')]:
        store.put('analysis_runs',name,{'run_id':name,'kind':'job','status':status,'repository':'r','request':request,
            'deadline_at':(datetime.now(timezone.utc)-timedelta(seconds=5)).isoformat()})
    monkeypatch.setattr(backend,'analyze',lambda *a,**k:calls.append(a))
    with TestClient(backend.create_app(store)) as client:
        assert client.get('/api/reports/cancel').json()['status']=='CANCELLED'
        assert wait_status(client,'expired',{'TIMED_OUT'})['status']=='TIMED_OUT'
        assert client.get('/api/reports/active').json()['status']=='FAILED'
    assert not calls


def test_restart_reconciles_report_committed_before_job_completion():
    store=Store('sqlite:///:memory:');report_id='completed-worker-report'
    store.put('analysis_runs','job',{'run_id':'job','kind':'job','status':'RUNNING','report_run_id':report_id})
    store.put('analysis_runs',report_id,{'run_id':report_id,'status':'COMPLETED'})
    with TestClient(backend.create_app(store)) as client:
        row=client.get('/api/reports/job').json()
    assert row['status']=='COMPLETED' and row['result_run_id']==report_id and row['recovered_result'] is True


def test_cancel_auth_validation_nonjob_and_unowned(monkeypatch,queued):
    store,_,release,_=queued;release.set();monkeypatch.setenv('VIGILANT_ACCESS_TOKEN','fixture')
    store.put('analysis_runs','report',{'run_id':'report','status':'COMPLETED'})
    store.put('analysis_runs','orphan',{'run_id':'orphan','kind':'job','status':'QUEUED'})
    with TestClient(backend.create_app(store)) as client:
        assert client.post('/api/analysis/jobs/report/cancel').status_code==401
        client.headers['Authorization']='Bearer fixture'
        assert client.post('/api/analysis/jobs/report/cancel').status_code==404
        for value in [0,3601,True,'10',1.5]:
            assert client.post('/api/analysis/run',json={'repository':'r','timeout_seconds':value}).status_code==422
        store.put('analysis_runs','unowned',{'run_id':'unowned','kind':'job','status':'QUEUED'})
        assert client.post('/api/analysis/jobs/unowned/cancel').status_code==409


def test_workflow_stop_preserves_partial_run_and_skips_next_operation(monkeypatch,tmp_path):
    import agents.workflow as workflow
    store=Store('sqlite:///:memory:');control=RunControl();calls=[]
    def revision(repo,ref):
        calls.append(ref);control.cancel();return 'f'*40
    monkeypatch.setattr(workflow,'revision',revision)
    monkeypatch.setattr(workflow,'import_repository',lambda *a:pytest.fail('Import must not begin after cancellation'))
    with pytest.raises(InvestigationStopped) as exc:workflow.analyze(store,'fixture','base',control=control)
    row=store.get('analysis_runs',exc.value.run_id)
    assert row['status']=='CANCELLED' and row['partial_results'] is True
    assert row['trajectory'][0]['status']=='CANCELLED' and row['trajectory'][0]['operation_started']
    assert not store.rows('evidence') and not store.rows('findings')
    monkeypatch.undo()
    from tests.test_audit_regressions import repository
    repo,git=repository(tmp_path);base=git('rev-parse','HEAD')
    (repo/'app.py').write_text('def value():\n return 2\ndef test_value():\n assert value()==1\n');git('commit','-am','change')
    second=RunControl();real_verify=workflow.verify_git
    def verify_then_stop(*args):
        errors=real_verify(*args);assert not errors;second.cancel();return errors
    monkeypatch.setattr(workflow,'verify_git',verify_then_stop)
    monkeypatch.setattr(workflow,'provider',lambda *a:pytest.fail('Provider must not start after cancellation'))
    with pytest.raises(InvestigationStopped) as stopped:workflow.analyze(store,repo,base,control=second)
    partial=store.get('analysis_runs',stopped.value.run_id)
    assert partial['status']=='CANCELLED' and partial['metrics']['quotes_verified']>0
    assert partial['trajectory'][-1]['tool']=='validate-git-blobs-quotes-ranges-hashes'


def test_publication_wins_over_late_cancellation(monkeypatch,queued):
    store,entered,release,calls=queued
    def analyze(*args,control,**kwargs):
        control.begin_publication();entered.set();assert release.wait(10);return {'run_id':'published'}
    monkeypatch.setattr(backend,'analyze',analyze)
    with TestClient(backend.create_app(store)) as client:
        try:
            job=client.post('/api/analysis/run',json={'repository':'r'}).json()['job_id'];assert entered.wait(3)
            assert client.post('/api/analysis/jobs/'+job+'/cancel').status_code==409
        finally:release.set()
        assert wait_status(client,job,{'COMPLETED'})['result_run_id']=='published'


@pytest.mark.parametrize(('cancel','expected'),[(True,'CANCELLED'),(False,'TIMED_OUT')])
def test_file_backed_worker_can_be_force_stopped(tmp_path,monkeypatch,cancel,expected):
    store=Store('sqlite:///'+str(tmp_path/'isolated.db'))
    store.put('repositories','r',{'repository':'r','project_id':'p','path':str(tmp_path)})
    monkeypatch.setattr(backend,'revision',lambda path,ref:'f'*40)
    with TestClient(backend.create_app(store,analysis_runner=blocking_analysis)) as client:
        timeout=120 if cancel else 1
        job=client.post('/api/analysis/run',json={'repository':'r','timeout_seconds':timeout}).json()['job_id']
        if cancel:
            wait_for_worker(tmp_path)
            row=client.get('/api/reports/'+job).json()
            assert row.get('status')=='RUNNING',row
            assert client.post('/api/analysis/jobs/'+job+'/cancel').json()['status']=='CANCEL_REQUESTED'
        stopped=wait_status(client,job,{expected})
        assert stopped['stop_mode']=='PROCESS_ISOLATED_HARD_STOP'
        assert stopped['partial_run_id']
        report=store.get('analysis_runs',stopped['partial_run_id'])
        assert report['status']==expected and report['partial_results'] is True
    store.engine.dispose()


def test_file_backed_worker_crash_leaves_no_partial_report(tmp_path,monkeypatch):
    store=Store('sqlite:///'+str(tmp_path/'crashed.db'))
    store.put('repositories','r',{'repository':'r','project_id':'p','path':str(tmp_path)})
    monkeypatch.setattr(backend,'revision',lambda path,ref:'f'*40)
    with TestClient(backend.create_app(store,analysis_runner=crashing_analysis)) as client:
        job=client.post('/api/analysis/run',json={'repository':'r','timeout_seconds':60}).json()['job_id']
        wait_for_worker(tmp_path)
        failed=wait_status(client,job,{'FAILED'})
        report_id=failed['report_run_id']
        assert 'exited without a terminal result' in failed['error']
        assert store.get('analysis_runs',report_id) is None
        assert store.get('agent_runs',report_id) is None
    store.engine.dispose()


def test_file_backed_worker_cancellation_stops_child_process_tree(tmp_path,monkeypatch):
    store=Store('sqlite:///'+str(tmp_path/'descendant.db'))
    store.put('repositories','r',{'repository':'r','project_id':'p','path':str(tmp_path)})
    monkeypatch.setattr(backend,'revision',lambda path,ref:'f'*40)
    pid=None
    try:
        with TestClient(backend.create_app(store,analysis_runner=descendant_analysis)) as client:
            job=client.post('/api/analysis/run',json={'repository':'r','timeout_seconds':120}).json()['job_id']
            wait_for_worker(tmp_path,'descendant-pid')
            pid=int(Path(tmp_path,'descendant-pid').read_text(encoding='ascii'))
            assert pid_alive(pid)
            assert client.post('/api/analysis/jobs/'+job+'/cancel').json()['status']=='CANCEL_REQUESTED'
            assert wait_status(client,job,{'CANCELLED'})['status']=='CANCELLED'
            end=time.monotonic()+3
            while pid_alive(pid) and time.monotonic()<end:time.sleep(.05)
            stopped=not pid_alive(pid)
            Path(tmp_path,'descendant-state').write_text('stopped' if stopped else 'alive',encoding='ascii')
            assert stopped,'Child process survived cancellation of the isolated worker'
    finally:
        if pid and pid_alive(pid):
            try:os.kill(pid,signal.SIGTERM)
            except OSError:pass
        store.engine.dispose()


def test_file_backed_sqlite_has_single_server_owner(tmp_path):
    database='sqlite:///'+str(tmp_path/'owned.db')
    first_store=Store(database);second_store=Store(database)
    try:
        with TestClient(backend.create_app(first_store,analysis_runner=blocking_analysis)) as first:
            assert first.get('/api/health').status_code==200
            context=multiprocessing.get_context('spawn');result_queue=context.Queue()
            probe=context.Process(target=probe_server_lock,args=(str(tmp_path/'owned.db'),result_queue))
            probe.start()
            try:
                assert result_queue.get(timeout=15)=='rejected'
                probe.join(5);assert probe.exitcode==0
            finally:
                if probe.is_alive():probe.terminate();probe.join(2)
                result_queue.close();result_queue.join_thread()
            with pytest.raises(RuntimeError,match='already owns this SQLite database'):
                with TestClient(backend.create_app(second_store,analysis_runner=blocking_analysis)):
                    pass
            assert first.get('/api/health').status_code==200
        with TestClient(backend.create_app(second_store,analysis_runner=blocking_analysis)) as second:
            assert second.get('/api/health').status_code==200
    finally:
        first_store.engine.dispose();second_store.engine.dispose()


def test_server_crash_terminates_worker_tree_and_restart_does_not_replay(tmp_path,monkeypatch):
    database='sqlite:///'+str(tmp_path/'crash-recovery.db')
    store=Store(database)
    context=multiprocessing.get_context('spawn');result_queue=context.Queue()
    server=context.Process(target=run_server_until_crashed,args=(database,str(tmp_path),result_queue))
    descendant_pid=None
    try:
        server.start();job=result_queue.get(timeout=30)
        wait_for_worker(tmp_path,'descendant-pid')
        descendant_pid=int(Path(tmp_path,'descendant-pid').read_text(encoding='ascii'))
        assert pid_alive(descendant_pid)
        assert store.get('analysis_runs',job)['status']=='RUNNING'
        server.terminate();server.join(10);assert not server.is_alive()
        end=time.monotonic()+5
        while pid_alive(descendant_pid) and time.monotonic()<end:time.sleep(.05)
        assert not pid_alive(descendant_pid),'Server crash left an analysis descendant alive'
        monkeypatch.setattr(backend,'revision',lambda path,ref:'f'*40)
        with TestClient(backend.create_app(store,analysis_runner=detect_replay)) as client:
            recovered=client.get('/api/reports/'+job).json()
            assert recovered['status']=='FAILED',recovered
            assert not recovered.get('result_run_id')
            assert len([row for row in store.jobs() if row.get('status') in {'QUEUED','RUNNING'}])==0
            assert not Path(tmp_path,'replayed-after-server-crash').exists()
    finally:
        if server.is_alive():server.terminate();server.join(5)
        if descendant_pid and pid_alive(descendant_pid):
            try:os.kill(descendant_pid,signal.SIGTERM)
            except OSError:pass
        result_queue.close();result_queue.join_thread();store.engine.dispose()
