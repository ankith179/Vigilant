"""Production UI/API lifecycle acceptance with a labelled cooperative worker fixture."""
from pathlib import Path
import argparse,json,os,socket,subprocess,sys,threading,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['VIGILANT_DB']='sqlite:///:memory:'
import uvicorn
import backend.app as backend
from database.store import Store


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise FileExistsError('Refusing to overwrite browser acceptance')
    args.output.mkdir(parents=True)
    shutdown=threading.Event();store=Store('sqlite:///:memory:')
    store.put('repositories','fixture',{'repository':'fixture','project_id':'fixture','name':'Authored job-control fixture','path':'NOT_A_SUBJECT_REPOSITORY'})
    store.put('commits','fixture-commit',{'repository':'fixture','commit_id':'f'*40,'subject':'Authored lifecycle fixture'})
    backend.revision=lambda path,ref:'f'*40
    def worker(*args,control,**kwargs):
        while not shutdown.wait(.02):control.check()
        raise RuntimeError('Authored fixture server stopping')
    backend.analyze=worker
    app=backend.create_app(store)
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    try:
        end=time.monotonic()+10
        while not server.started and thread.is_alive() and time.monotonic()<end:time.sleep(.05)
        if not server.started:raise RuntimeError('Fixture server did not start')
        env={**os.environ,'VIGILANT_TEST_URL':f'http://127.0.0.1:{port}','VIGILANT_BROWSER_REPORT':str(args.output.resolve())}
        result=subprocess.run(['node','scripts/test_job_controls.cjs'],cwd=ROOT,env=env)
        (args.output/'jobs.json').write_text(json.dumps({'fixture_only':True,'model_calls':0,'independent_labels_created':0,'jobs':store.jobs()},indent=2)+'\n')
        return result.returncode
    finally:
        shutdown.set();server.should_exit=True;thread.join(15)
        if thread.is_alive():raise RuntimeError('Fixture server failed to stop')
        store.engine.dispose()

if __name__=='__main__':raise SystemExit(main())
