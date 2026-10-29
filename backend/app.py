"""Local research API with bounded, supervised analysis workers."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import multiprocessing,uuid,os,secrets,threading,asyncio,signal
from time import monotonic
from datetime import datetime,timedelta,timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI,HTTPException,Query,Request
from fastapi.responses import JSONResponse,Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from typing import Literal
from sqlalchemy import select,func
from database.store import Store
from ingestion.models import digest,now
from ingestion.git import revision
from ingestion.service import import_repository
from knowledge_graph.graph import build_graph
from traceability.recovery import recover
from agents.workflow import analyze
from agents.control import RunControl,InvestigationStopped
from backend.partial_delivery import ExplanationInput
from backend.report_chat import ReportChatInput,explain
from investigation.service import InvestigationService,catalog,ToolResult
ROOT=Path(__file__).resolve().parents[1]
_DEFAULT_ANALYZE=analyze
_CANCEL_GRACE_SECONDS=.5

def _isolated_analysis_worker(database_url,repo_path,request,project_id,report_id,control,runner,connection,start_event):
 if not start_event.wait(10):
  connection.send({'status':'FAILED','error':'Worker process containment setup did not complete.'});connection.close();return
 if os.name!='nt':os.setsid()
 child_store=Store(database_url)
 try:
  row=runner(child_store,repo_path,request['base'],request['head'],project_id,request['model'],request['semantic'],
             control=control,run_id=report_id,**({'ollama_model':request['ollama_model']} if request.get('ollama_model') else {}))
  connection.send({'status':'COMPLETED','result_run_id':row['run_id'],'finished_monotonic':monotonic()})
 except InvestigationStopped as exc:
  connection.send({'status':exc.status,'partial_run_id':exc.run_id,'error':str(exc)})
 except Exception as exc:
  connection.send({'status':'FAILED','error':str(exc)[:1000]})
 finally:
  child_store.engine.dispose();connection.close()

def _file_sqlite_url(store):
 url=store.engine.url;database=url.database or ''
 if url.get_backend_name()!='sqlite' or database in {'',':memory:'} or 'mode=memory' in database:return None
 return url.render_as_string(hide_password=False)

def _acquire_server_lock(store):
 url=store.engine.url;database=url.database or ''
 if url.get_backend_name()!='sqlite' or database in {'',':memory:'} or 'mode=memory' in database:return None
 lock_path=Path(database).resolve().with_name(Path(database).name+'.vigilant.lock')
 lock_path.parent.mkdir(parents=True,exist_ok=True);handle=lock_path.open('a+b')
 try:
  if os.name=='nt':
   import msvcrt
   handle.seek(0)
   if not handle.read(1):handle.seek(0);handle.write(b'0');handle.flush()
   handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
  else:
   import fcntl
   fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
 except (OSError,BlockingIOError) as exc:
  handle.close()
  raise RuntimeError(f'Another VIGILANT server already owns this SQLite database ({lock_path})') from exc
 def release():
  try:
   if os.name=='nt':
    import msvcrt
    handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
   else:
    import fcntl
    fcntl.flock(handle.fileno(),fcntl.LOCK_UN)
  finally:handle.close()
 return release

def _windows_worker_job(process):
 if os.name!='nt':return None
 import ctypes
 from ctypes import wintypes
 class Basic(ctypes.Structure):
  _fields_=[('PerProcessUserTimeLimit',ctypes.c_longlong),('PerJobUserTimeLimit',ctypes.c_longlong),('LimitFlags',wintypes.DWORD),('MinimumWorkingSetSize',ctypes.c_size_t),('MaximumWorkingSetSize',ctypes.c_size_t),('ActiveProcessLimit',wintypes.DWORD),('Affinity',ctypes.c_size_t),('PriorityClass',wintypes.DWORD),('SchedulingClass',wintypes.DWORD)]
 class Io(ctypes.Structure):
  _fields_=[('ReadOperationCount',ctypes.c_ulonglong),('WriteOperationCount',ctypes.c_ulonglong),('OtherOperationCount',ctypes.c_ulonglong),('ReadTransferCount',ctypes.c_ulonglong),('WriteTransferCount',ctypes.c_ulonglong),('OtherTransferCount',ctypes.c_ulonglong)]
 class Extended(ctypes.Structure):
  _fields_=[('BasicLimitInformation',Basic),('IoInfo',Io),('ProcessMemoryLimit',ctypes.c_size_t),('JobMemoryLimit',ctypes.c_size_t),('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]
 api=ctypes.WinDLL('kernel32',use_last_error=True)
 api.CreateJobObjectW.restype=wintypes.HANDLE
 api.SetInformationJobObject.argtypes=[wintypes.HANDLE,wintypes.INT,ctypes.c_void_p,wintypes.DWORD];api.SetInformationJobObject.restype=wintypes.BOOL
 api.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];api.OpenProcess.restype=wintypes.HANDLE
 api.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE];api.AssignProcessToJobObject.restype=wintypes.BOOL
 api.CloseHandle.argtypes=[wintypes.HANDLE];api.CloseHandle.restype=wintypes.BOOL
 api.TerminateJobObject.argtypes=[wintypes.HANDLE,wintypes.UINT];api.TerminateJobObject.restype=wintypes.BOOL
 job=api.CreateJobObjectW(None,None)
 if not job:raise ctypes.WinError(ctypes.get_last_error())
 try:
  info=Extended();info.BasicLimitInformation.LimitFlags=0x2000
  if not api.SetInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info)):raise ctypes.WinError(ctypes.get_last_error())
  handle=api.OpenProcess(0x0100|0x0001|0x1000,False,process.pid)
  if not handle:raise ctypes.WinError(ctypes.get_last_error())
  try:
   if not api.AssignProcessToJobObject(job,handle):raise ctypes.WinError(ctypes.get_last_error())
  finally:api.CloseHandle(handle)
  return api,job
 except Exception:
  api.CloseHandle(job);raise

def _stop_worker_tree(process,job):
 if job:
  job[0].TerminateJobObject(job[1],1)
 else:
  try:os.killpg(process.pid,signal.SIGTERM)
  except ProcessLookupError:return
  process.join(2)
  # The group leader can exit before descendants honor TERM. Escalate the
  # group itself regardless of the leader's state so orphaned children stop.
  try:os.killpg(process.pid,signal.SIGKILL)
  except ProcessLookupError:pass
  process.join(2)
 if process.is_alive():process.kill();process.join(2)

def _close_worker_job(job):
 if job:job[0].CloseHandle(job[1])

class ProjectInput(BaseModel):name:str=Field(min_length=1,max_length=100)
class ImportInput(BaseModel):
 path:str|None=Field(default=None,max_length=1024);url:str|None=Field(default=None,max_length=2048);project_id:str='vigilant';revision:str='HEAD'
class AnalysisInput(BaseModel):
 repository:str;base:str='HEAD~1';head:str='HEAD';model:str='none';semantic:bool=False;ollama_model:str|None=None
 timeout_seconds:int=Field(default=900,ge=1,le=3600,strict=True)
class ChatTurn(BaseModel):
 role:Literal['user','assistant'];content:str=Field(min_length=1,max_length=1000)
class ToolCall(BaseModel):
 name:str=Field(min_length=1,max_length=80)
 arguments:dict
class ChatInput(BaseModel):
 repository:str;commit_id:str;question:str=Field(min_length=1,max_length=1200)
 history:list[ChatTurn]=Field(default_factory=list,max_length=6)
 model:Literal['none','local','ollama','omniroute','cloud','gemini','claude','glm']='none'
 ollama_model:str|None=None
 base_revision:str|None=Field(default=None,min_length=1,max_length=180)
 head_revision:str|None=Field(default=None,min_length=1,max_length=180)

def create_app(store=None,partial_reports=None,analysis_runner=None):
 if partial_reports is None and os.getenv('VIGILANT_PARTIAL_REPORT_MANIFEST_SHA256'):
  from backend.partial_reports import packaged_access
  partial_reports=packaged_access(ROOT,os.environ['VIGILANT_PARTIAL_REPORT_MANIFEST_SHA256'])
 store=store or Store();runner=analysis_runner or analyze
 database_url=_file_sqlite_url(store) if (analysis_runner is not None or runner is _DEFAULT_ANALYZE) else None
 process_context=multiprocessing.get_context('spawn') if database_url else None
 executor=ThreadPoolExecutor(max_workers=1);capacity=threading.BoundedSemaphore(20)
 active_jobs={};job_lock=threading.RLock()
 # ponytail: one local server process; use an external broker before multiple workers.
 def submit(body,repo,job=None):
  job=job or uuid.uuid4().hex
  previous=store.get('analysis_runs',job) or {}
  report_id=previous.get('report_run_id') or (uuid.uuid4().hex if process_context else None)
  created=previous.get('created_at',now())
  deadline=previous.get('deadline_at') or (datetime.now(timezone.utc)+timedelta(seconds=body.timeout_seconds)).isoformat()
  remaining=(datetime.fromisoformat(deadline)-datetime.now(timezone.utc)).total_seconds()
  if process_context:
   control=RunControl(remaining,deadline=monotonic()+max(0,remaining),cancelled=process_context.Event(),
                      publishing=process_context.Event(),lock=process_context.RLock())
  else:control=RunControl(remaining)
  stop_mode='PROCESS_ISOLATED_WITH_BOUNDED_TERMINATION' if process_context else 'COOPERATIVE_STAGE_BOUNDARY'
  scope={'run_id':job,'repository':body.repository,'project_id':repo['project_id'],'commit_id':body.head,'kind':'job','request':body.model_dump(),'created_at':created,'deadline_at':deadline,'stop_mode':stop_mode}
  if report_id:scope['report_run_id']=report_id
  if not capacity.acquire(blocking=False):raise HTTPException(429,'Analysis queue is full; try after a job finishes')
  try:store.put('analysis_runs',job,{**scope,'status':'QUEUED'},replace=True)
  except Exception:capacity.release();raise
  def release():
   with job_lock:
    if active_jobs.pop(job,None) is not None:capacity.release()
  def finish(status,**extra):
   with job_lock:
    current=store.get('analysis_runs',job) or scope
    store.put('analysis_runs',job,{**current,'status':status,'finished_at':now(),**extra},replace=True)
  def mark_forced_stop(report_id,status):
   previous_report=store.get('analysis_runs',report_id) or {'run_id':report_id,'repository':body.repository,'project_id':repo['project_id'],'commit_id':body.head}
   if previous_report.get('status')=='COMPLETED':
    finish('COMPLETED',result_run_id=report_id);return
   if previous_report.get('status')==status and previous_report.get('trajectory') is not None:
    finish(status,error=previous_report.get('error','Investigation stopped at a safe stage boundary.'),partial_run_id=report_id,stop_mode='COOPERATIVE_STAGE_BOUNDARY');return
   message='Isolated worker terminated after '+status.lower()+'; atomic report publication rolled back if it had not committed.'
   stopped={**previous_report,'status':status,'partial_results':True,'stop_mode':'PROCESS_ISOLATED_HARD_STOP','error':message,'finished_at':now()}
   store.put('analysis_runs',report_id,stopped,replace=True)
   agent=store.get('agent_runs',report_id) or {'run_id':report_id,'repository':body.repository,'project_id':repo['project_id'],'commit_id':body.head}
   store.put('agent_runs',report_id,{**agent,'status':status,'partial_results':True,'stop_mode':'PROCESS_ISOLATED_HARD_STOP','error':message},replace=True)
   finish(status,error=message,partial_run_id=report_id,stop_mode='PROCESS_ISOLATED_HARD_STOP')
  def isolated_work():
   receiver,sender=process_context.Pipe(duplex=False)
   start_event=process_context.Event()
   process=process_context.Process(target=_isolated_analysis_worker,args=(database_url,repo['path'],body.model_dump(),repo['project_id'],report_id,control,runner,sender,start_event))
   worker_job=None
   try:
    process.start();worker_job=_windows_worker_job(process);start_event.set()
   except Exception:
    if process.is_alive():
     if worker_job:_stop_worker_tree(process,worker_job)
     else:process.terminate();process.join(2)
    _close_worker_job(worker_job)
    receiver.close();sender.close();raise
   sender.close();forced=None
   try:
    while process.is_alive():
     process.join(.05)
     if monotonic()>=control.deadline:forced='TIMED_OUT'
     elif control.cancelled.is_set() and not control.publishing.is_set():forced='CANCELLED'
     if forced:
      control.cancelled.set();process.join(_CANCEL_GRACE_SECONDS)
      if process.is_alive():_stop_worker_tree(process,worker_job)
      break
    if not forced:process.join()
    if process.is_alive():_stop_worker_tree(process,worker_job)
    if process.is_alive():
     finish('FAILED',error='Isolated worker did not terminate after bounded stop escalation.',stop_mode='PROCESS_ISOLATED_HARD_STOP')
     return
    payload=None
    if not forced:
     try:
      if receiver.poll():payload=receiver.recv()
     except (EOFError,OSError):pass
   finally:
    receiver.close();_close_worker_job(worker_job)
   if forced:mark_forced_stop(report_id,forced)
   elif payload and payload.get('status')=='COMPLETED':finish('COMPLETED',result_run_id=payload['result_run_id'])
   elif payload:finish(payload.get('status','FAILED'),error=payload.get('error','Isolated analysis worker stopped.'),partial_run_id=payload.get('partial_run_id'))
   else:
    report=store.get('analysis_runs',report_id) or {}
    if report.get('status')=='COMPLETED':finish('COMPLETED',result_run_id=report_id)
    else:finish('FAILED',error='Isolated analysis worker exited without a terminal result.')
  def work():
   try:
    with job_lock:
     if store.get('analysis_runs',job).get('status')=='CANCELLED':return
     control.check();store.put('analysis_runs',job,{**scope,'status':'RUNNING'},replace=True)
    if process_context:isolated_work()
    else:
     r=runner(store,repo['path'],body.base,body.head,repo['project_id'],body.model,body.semantic,control=control,**({'ollama_model':body.ollama_model} if body.ollama_model else {}))
     control.check();finish('COMPLETED',result_run_id=r['run_id'])
   except InvestigationStopped as e:finish(e.status,error=str(e),partial_run_id=e.run_id)
   except Exception as e:finish('FAILED',error=str(e)[:1000])
   finally:release()
  try:
   with job_lock:
    active_jobs[job]=control;executor.submit(work)
  except Exception:
   finish('FAILED',error='Analysis worker rejected this request');release()
   raise HTTPException(503,'Analysis worker unavailable')
  return {'job_id':job,'status':'QUEUED'}
 @asynccontextmanager
 async def lifespan(app):
   release_server_lock=_acquire_server_lock(store)
   try:
    # Resume only work known not to have started. Never replay a possibly billed call.
    for row in store.jobs():
     if row.get('kind')!='job':continue
     if row.get('status')=='CANCEL_REQUESTED':
      store.put('analysis_runs',row['run_id'],{**row,'status':'CANCELLED','finished_at':now(),'error':'Server stopped after cancellation was requested; the interrupted operation outcome is unknown.'},replace=True)
     elif row.get('status')=='RUNNING':
      report=store.get('analysis_runs',row.get('report_run_id')) if row.get('report_run_id') else None
      if report and report.get('status')=='COMPLETED':
       store.put('analysis_runs',row['run_id'],{**row,'status':'COMPLETED','result_run_id':report['run_id'],'finished_at':now(),'recovered_result':True},replace=True)
      elif report and report.get('status') in {'CANCELLED','TIMED_OUT'}:
       store.put('analysis_runs',row['run_id'],{**row,'status':report['status'],'partial_run_id':report['run_id'],'finished_at':now(),'recovered_result':True},replace=True)
      else:
       store.put('analysis_runs',row['run_id'],{**row,'status':'FAILED','finished_at':now(),'error':'Server interrupted this running job; inspect the linked worker report before manually resubmitting.'},replace=True)
     elif row.get('status')=='QUEUED':
      try:
       body=AnalysisInput.model_validate(row['request']);repo=store.get('repositories',body.repository)
       if not repo:raise ValueError('Repository no longer exists')
       submit(body,repo,row['run_id'])
      except Exception as exc:store.put('analysis_runs',row['run_id'],{**row,'status':'FAILED','error':str(exc)},replace=True)
    yield
   finally:
    try:await asyncio.to_thread(executor.shutdown,wait=True)
    finally:
     if release_server_lock:release_server_lock()
 app=FastAPI(title='VIGILANT',version='0.2.0',lifespan=lifespan);app.state.store=store
 token=os.getenv('VIGILANT_ACCESS_TOKEN','')
 @app.middleware('http')
 async def protect(request:Request,call_next):
  path=request.url.path
  public=path in {'/','/index.html','/favicon.ico','/api/health','/api/auth/status'} or path.startswith('/assets/')
  if token and not public:
   supplied=request.headers.get('Authorization','')
   if not secrets.compare_digest(supplied.encode(),('Bearer '+token).encode()):return JSONResponse({'detail':'Workspace access token required'},status_code=401)
  return await call_next(request)
 @app.get('/api/auth/status')
 def auth_status():return {'authentication_required':bool(token),'mode':'shared-workspace-token' if token else 'local-only','multiuser_roles':False,'free_only':os.getenv('VIGILANT_FREE_ONLY','1')!='0'}

 @app.get('/api/health')
 def health():return {'status':'ok','version':'0.3.0'}
 @app.get('/api/partial-reports')
 def partial_report_list(offset:int=Query(0,ge=0,le=200),limit:int=Query(20,ge=1,le=100)):
  if partial_reports is None:return {'enabled':False,'items':[],'total':0,'next_offset':None}
  try:return partial_reports.listing(offset,limit)
  except (ValueError,OSError):raise HTTPException(409,'Partial report catalog rejected; verify configured manifest')
 def verified_partial(report_id,repository,base_commit,head_commit):
  if partial_reports is None:raise HTTPException(404,'Partial reports are not enabled')
  try:return partial_reports.read(report_id,repository,base_commit,head_commit)
  except KeyError:raise HTTPException(404,'Partial report not found')
  except (ValueError,OSError):raise HTTPException(409,'Partial report source, identity or scope revalidation failed')
 @app.get('/api/partial-reports/{report_id}')
 def partial_report_read(report_id:str,repository:str,base_commit:str,head_commit:str):
  return verified_partial(report_id,repository,base_commit,head_commit)
 @app.post('/api/partial-reports/{report_id}/explain')
 def partial_report_explain(report_id:str,body:ExplanationInput):
  from backend.partial_delivery import explain
  loaded=verified_partial(report_id,body.repository,body.base_commit,body.head_commit)
  return explain(loaded,body.intent)
 @app.get('/api/partial-reports/{report_id}/export')
 def partial_report_export(report_id:str,repository:str,base_commit:str,head_commit:str,format:Literal['json','html']='json'):
  from backend.partial_delivery import export
  loaded=verified_partial(report_id,repository,base_commit,head_commit);content,media=export(loaded,format)
  return Response(content,media_type=media,headers={'Content-Disposition':f'attachment; filename="vigilant-partial-report-{report_id}.{format}"',
    'Cache-Control':'no-store','Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"})
 @app.get('/api/partial-reports/{report_id}/source')
 def partial_report_source(report_id:str,repository:str,base_commit:str,head_commit:str,commit_id:str,artifact_id:str,
                           start_line:int|None=Query(None,ge=1),max_lines:int=Query(40,ge=1,le=80)):
  if partial_reports is None:raise HTTPException(404,'Partial reports are not enabled')
  try:return partial_reports.inspect(report_id,repository,base_commit,head_commit,commit_id,artifact_id,start_line,max_lines)
  except KeyError:raise HTTPException(404,'Partial report not found')
  except (ValueError,OSError):raise HTTPException(409,'Partial report source, identity or scope revalidation failed')
 @app.get('/api/investigation/tools')
 def investigation_tools():return {'tools':[t for t in catalog() if t['name']!='update_unknown']}
 @app.post('/api/investigation/call',response_model=ToolResult)
 def investigation_call(body:ToolCall):
  if body.name=='update_unknown':raise HTTPException(403,'Record updates are available only through the explicit local CLI/MCP opt-in')
  try:return InvestigationService(store).call(body.name,body.arguments)
  except ValueError:raise HTTPException(409,'Tool rejected the arguments or scoped evidence; inspect tool schema and pinned source availability')
 @app.get('/api/stats')
 def stats():
  with store.connection() as c:return {n:c.execute(select(func.count()).select_from(t)).scalar_one() for n,t in store.tables.items()}
 @app.post('/projects')
 @app.post('/api/projects')
 def project(body:ProjectInput):
  pid=digest(body.name);return store.put('projects',pid,{'project_id':pid,'name':body.name})
 @app.post('/repositories/import')
 @app.post('/api/repositories/import')
 def import_repo(body:ImportInput):
  if bool(body.url)==bool(body.path):raise HTTPException(400,'Supply exactly one path or URL')
  if body.url:
   from backend.repository_import import validate_public_repository_url
   try:validate_public_repository_url(body.url)
   except ValueError:raise HTTPException(400,'Expected public HTTPS GitHub or GitLab repository URL')
   path=ROOT/'data/repos'/digest(body.url)[:16]
   if not path.exists():
    from backend.repository_import import clone_repository
    try:clone_repository(body.url,path)
    except ValueError as e:raise HTTPException(400,str(e))
    except OSError as e:raise HTTPException(400,'Clone failed: '+type(e).__name__)
  elif body.path:
   path=(ROOT/body.path).resolve()
   if not any(path.is_relative_to((ROOT/'data'/p).resolve()) for p in ['repos','raw','changebench']):raise HTTPException(400,'Path must be under data/repos, data/raw, or data/changebench')
  else:raise HTTPException(400,'Supply path or URL')
  try:
   r=import_repository(store,path,body.project_id,body.revision);a=store.artifacts(r['repository'],r['commit_id']);_,edges=build_graph(store,a);links=recover(store,a);return {**r,'graph_edges':len(edges),'trace_candidates':len(links)}
  except Exception as e:raise HTTPException(400,str(e)[:300])
 @app.post('/analysis/run',status_code=202)
 @app.post('/api/analysis/run',status_code=202)
 def start(body:AnalysisInput):
  repo=store.get('repositories',body.repository)
  if not repo:raise HTTPException(404,'Repository not found')
  if body.model not in {'none','local','cloud','ollama','gemini','claude','omniroute','glm'}:raise HTTPException(400,'Unknown provider')
  if os.getenv('VIGILANT_FREE_ONLY','1')!='0' and body.model in {'cloud','gemini','claude','glm'}:raise HTTPException(400,'Paid or unverified-cost providers are disabled in free-only mode')
  if body.model=='ollama':
   from llm.ollama import OllamaProvider,MODELS_32GB
   if body.ollama_model is not None and body.ollama_model not in MODELS_32GB:raise HTTPException(400,'Select a supported 32 GB model')
   try:OllamaProvider(body.ollama_model).preflight()
   except Exception as exc:raise HTTPException(400,'Local model is not ready: '+str(exc)[:200])
  if body.model=='omniroute':
   from llm.omniroute import OmniRouteProvider
   try:OmniRouteProvider.configuration()
   except ValueError as exc:raise HTTPException(400,str(exc))
  if body.model=='glm':
   from llm.glm import GLMProvider
   try:GLMProvider().preflight()
   except ValueError as exc:raise HTTPException(400,str(exc))
  try:
   # Resolve refs before queueing so HEAD cannot silently move while waiting.
   body=body.model_copy(update={'base':revision(repo['path'],body.base),'head':revision(repo['path'],body.head)})
  except Exception as exc:raise HTTPException(400,'Cannot resolve repository revisions: '+type(exc).__name__)
  return submit(body,repo)

 @app.post('/api/analysis/jobs/{job_id}/cancel')
 def cancel_job(job_id:str):
  with job_lock:
   row=store.get('analysis_runs',job_id)
   if not row or row.get('kind')!='job':raise HTTPException(404,'Analysis job not found')
   if row.get('status') in {'COMPLETED','FAILED','CANCELLED','TIMED_OUT'}:return row
   record=active_jobs.get(job_id)
   if record is None:raise HTTPException(409,'Job is not owned by this server process')
   if not record.cancel():raise HTTPException(409,'Final report publication has started; wait for its terminal status')
   queued=row.get('status')=='QUEUED'
   row={**row,'status':'CANCELLED' if queued else 'CANCEL_REQUESTED','cancel_requested_at':row.get('cancel_requested_at',now())}
   if queued:row['finished_at']=now()
   store.put('analysis_runs',job_id,row,replace=True)
   # ponytail: cancelled placeholders retain their slots until drained, bounding
   # the executor's otherwise unbounded queue during repeated queue/cancel calls.
   return row

 def listing(table):
  def get(repository:str|None=None,commit_id:str|None=None,project_id:str|None=None,run_id:str|None=None,limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0)):
   rows=store.rows(table,repository=repository,commit_id=commit_id,project_id=project_id,run_id=run_id,limit=limit+1,offset=offset);has_more=len(rows)>limit;rows=rows[:limit]
   return {'items':rows,'limit':limit,'offset':offset,'returned':len(rows),'has_more':has_more,'next_offset':offset+limit if has_more else None}
  return get
 for path,table in {'projects':'projects','repositories':'repositories','commits':'commits','artifacts':'artifacts','traceability':'trace_links','changes':'changes','evidence':'evidence','findings':'findings','reports':'analysis_runs','experiments':'experiments','agents':'agent_runs','consistency':'findings','evaluation':'experiments'}.items():
  app.add_api_route('/'+path,listing(table),methods=['GET']);app.add_api_route('/api/'+path,listing(table),methods=['GET'])
 @app.get('/graph')
 @app.get('/api/graph')
 def graph(repository:str,commit_id:str,limit:int=Query(100,ge=1,le=500)):
  edges=store.graph_edges(repository,commit_id,limit+1);truncated=len(edges)>limit;edges=edges[:limit]
  ids={e[k] for e in edges for k in ['source_artifact','target_artifact']}
  # Artifact nodes use version keys; commit nodes use their commit identity.
  nodes=[n for n in store.get_many('graph_nodes',[key for i in sorted(ids) for key in (digest(i,commit_id),i)]) if n['repository']==repository and n['commit_id']==commit_id]
  return {'nodes':nodes,'edges':edges,'truncated':truncated}
 @app.get('/api/reports/{run_id}')
 def report(run_id:str):
  r=store.get('analysis_runs',run_id)
  if r is None:raise HTTPException(404,'Run not found')
  return r
 @app.get('/api/reports/{run_id}/coverage')
 def report_coverage(run_id:str):
  row=store.get('analysis_runs',run_id)
  if not row:raise HTTPException(404,'Run not found')
  return {'state':'RECORDED' if row.get('coverage') else 'NOT_RECORDED','run_id':run_id,
          'base_commit':row.get('base_commit'),'head_commit':row.get('commit_id'),'coverage':row.get('coverage'),
          'semantic_completeness':'NOT_ESTABLISHED'}
 @app.get('/api/artifacts/{artifact_id}')
 def artifact(artifact_id:str,repository:str,commit_id:str):
  r=store.get('artifacts',digest(artifact_id,commit_id))
  if r is None or r['repository']!=repository or r['commit_id']!=commit_id:raise HTTPException(404,'Version not found')
  return r
 @app.get('/api/impact')
 def impact_records(repository:str,commit_id:str,limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0)):
  rows=[{**a,'run_id':r['run_id'],'repository':repository,'commit_id':commit_id} for r in store.rows('analysis_runs',repository=repository,commit_id=commit_id) for a in r.get('affected_artifacts',[])]
  return {'items':rows[offset:offset+limit],'has_more':len(rows)>offset+limit,'offset':offset,'limit':limit}
 @app.get('/api/rag')
 def retrieve_evidence(repository:str,commit_id:str,query:str=Query(min_length=1,max_length=1200),limit:int=Query(8,ge=1,le=24)):
  from rag.evidence import retrieve,verify
  artifacts=store.artifacts(repository,commit_id)
  if not artifacts:raise HTTPException(404,'Snapshot not found')
  items=retrieve(query,artifacts,k=limit)
  if verify(items,artifacts):raise HTTPException(500,'Stored evidence failed verification')
  return {'items':items,'method':'bm25','source_verified':True,'verification_scope':'quoted excerpts against stored artifacts','semantic_entailment_verified':False}
 @app.post('/api/report-chat')
 def report_chat(body:ReportChatInput):return explain(store,body)
 @app.get('/api/project-overview')
 def project_overview(repository:str,commit_id:str):
  from backend.project_overview import describe
  return describe(store,repository,commit_id)
 @app.post('/api/chat')
 def chat(body:ChatInput):
  from backend.chat_tools import comparison,response
  action=comparison(body.question,body.base_revision,body.head_revision)
  if action:
   if not store.get('repositories',body.repository):raise HTTPException(404,'Repository not found')
   if action['state']!='READY':return response(action['state'],action['answer'])
   job=start(AnalysisInput(repository=body.repository,base=action['base'],head=action['head'],model='none'))
   queued=store.get('analysis_runs',job['job_id'])
   request=queued['request']
   return response('QUEUED','Comparing the pinned repository revisions with deterministic tools.',
                   action='COMPARE_REVISIONS',job_id=job['job_id'],repository=body.repository,
                   base_commit=request['base'],head_commit=request['head'])
  from backend.project_overview import describe,matches
  if matches(body.question):return describe(store,body.repository,body.commit_id)
  from rag.evidence import retrieve,verify
  from llm.providers import provider
  artifacts=store.artifacts(body.repository,body.commit_id)
  if not artifacts:raise HTTPException(404,'Repository snapshot not found')
  try:
   if body.model=='ollama':
    from llm.ollama import MODELS_32GB,OllamaProvider
    if body.ollama_model is not None and body.ollama_model not in MODELS_32GB:
     raise HTTPException(400,'Select a supported 32 GB model')
    engine=OllamaProvider(body.ollama_model)
   else:engine=provider(body.model)
  except ValueError as exc:raise HTTPException(400,str(exc))
  history=body.history[-6:]
  retrieval_query=body.question  # Prior turns are untrusted dialogue, not additional search terms.
  items=retrieve(retrieval_query,artifacts,k=8)
  errors=verify(items,artifacts)
  if errors:raise HTTPException(500,'Retrieved evidence failed source verification')
  turns='\n'.join(f'{turn.role}: {turn.content}' for turn in history)
  question=('Prior conversation is context, not repository evidence.\n'+turns+'\nCurrent question: '+body.question)[-8000:]
  result=engine.investigate(question,items)
  decision=result['decision'];by_id={item['evidence_id']:item for item in items}
  citations=[by_id[eid] for eid in decision['evidence_ids'] if eid in by_id]
  answer=decision['reason'] or decision.get('uncertainty') or 'The available evidence does not establish an answer.'
  if body.model=='none':
   answer=f'No model was called. I found {len(items)} source-verified excerpts for this snapshot; select a reasoning provider for an interpretation.'
  return {'answer':answer,'decision':decision,'citations':citations,'retrieved_evidence':items,
   'source_verified':True,'verification_scope':'quoted excerpts against stored artifacts','semantic_entailment_verified':False,
   'confidence_note':'Model-reported confidence is not calibrated accuracy.',
   'validation_error':result['validation_error'],'provider':result['provider'],
   'repository':body.repository,'commit_id':body.commit_id}
 @app.get('/api/reports/{run_id}/export')
 def export_report(run_id:str,format:str=Query('json',pattern='^(json|csv|html)$')):
  from backend.exports import export
  row=store.get('analysis_runs',run_id)
  if not row:raise HTTPException(404,'Run not found')
  content,media=export(row,format)
  return Response(content,media_type=media,headers={'Content-Disposition':f'attachment; filename="vigilant-report.{format}"'})
 @app.get('/api/metrics')
 def metrics():
  counts={k:0 for k in ['QUEUED','RUNNING','CANCEL_REQUESTED','CANCELLED','TIMED_OUT','COMPLETED','FAILED']}
  for row in store.jobs():
   if row.get('kind')=='job' and row.get('status')in counts:counts[row['status']]+=1
  text='# HELP vigilant_jobs Persisted local analysis jobs by status.\n# TYPE vigilant_jobs gauge\n'
  text+=''.join('vigilant_jobs{status="'+k.lower()+'"} '+str(v)+'\n' for k,v in counts.items())
  return Response(text,media_type='text/plain; version=0.0.4')
 dist=ROOT/'frontend/dist'
 if dist.exists():app.mount('/',StaticFiles(directory=dist,html=True),name='frontend')
 return app
