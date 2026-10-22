"""Local research API with a single bounded analysis worker."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import uuid,subprocess,json,os,secrets,threading,asyncio
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
ROOT=Path(__file__).resolve().parents[1]
class ProjectInput(BaseModel):name:str=Field(min_length=1,max_length=100)
class ImportInput(BaseModel):
 path:str|None=None;url:str|None=None;project_id:str='vigilant';revision:str='HEAD'
class AnalysisInput(BaseModel):
 repository:str;base:str='HEAD~1';head:str='HEAD';model:str='none';semantic:bool=False;ollama_model:str|None=None
class ChatTurn(BaseModel):
 role:Literal['user','assistant'];content:str=Field(min_length=1,max_length=1000)
class ChatInput(BaseModel):
 repository:str;commit_id:str;question:str=Field(min_length=1,max_length=1200)
 history:list[ChatTurn]=Field(default_factory=list,max_length=6)
 model:Literal['none','local','ollama','omniroute','cloud','gemini','claude']='none'
 ollama_model:str|None=None

def create_app(store=None):
 store=store or Store();executor=ThreadPoolExecutor(max_workers=1);capacity=threading.BoundedSemaphore(20)
 # ponytail: one local server process; use an external broker before multiple workers.
 def submit(body,repo,job=None):
  if not capacity.acquire(blocking=False):raise HTTPException(429,'Analysis queue is full; try after a job finishes')
  job=job or uuid.uuid4().hex
  scope={'run_id':job,'repository':body.repository,'project_id':repo['project_id'],'commit_id':body.head,'kind':'job','request':body.model_dump(),'created_at':now()}
  try:store.put('analysis_runs',job,{**scope,'status':'QUEUED'},replace=True)
  except Exception:capacity.release();raise
  def work():
   try:
    store.put('analysis_runs',job,{**scope,'status':'RUNNING'},replace=True)
    r=analyze(store,repo['path'],body.base,body.head,repo['project_id'],body.model,body.semantic,**({'ollama_model':body.ollama_model} if body.ollama_model else {}))
    store.put('analysis_runs',job,{**scope,'status':'COMPLETED','result_run_id':r['run_id'],'finished_at':now()},replace=True)
   except Exception as e:store.put('analysis_runs',job,{**scope,'status':'FAILED','error':str(e),'finished_at':now()},replace=True)
   finally:capacity.release()
  executor.submit(work)
  return {'job_id':job,'status':'QUEUED'}
 @asynccontextmanager
 async def lifespan(app):
  # Resume only work known not to have started. Never replay a possibly billed call.
  for row in store.rows('analysis_runs'):
   if row.get('kind')!='job':continue
   if row.get('status')=='RUNNING':
    store.put('analysis_runs',row['run_id'],{**row,'status':'FAILED','error':'Server interrupted this running job; inspect saved reports before manually resubmitting.'},replace=True)
   elif row.get('status')=='QUEUED':
    try:
     body=AnalysisInput.model_validate(row['request']);repo=store.get('repositories',body.repository)
     if not repo:raise ValueError('Repository no longer exists')
     submit(body,repo,row['run_id'])
    except Exception as exc:store.put('analysis_runs',row['run_id'],{**row,'status':'FAILED','error':str(exc)},replace=True)
  yield
  await asyncio.to_thread(executor.shutdown,wait=True)
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
 def health():return {'status':'ok','version':'0.2.0'}
 @app.get('/api/stats')
 def stats():
  with store.engine.connect() as c:return {n:c.execute(select(func.count()).select_from(t)).scalar_one() for n,t in store.tables.items()}
 @app.post('/projects')
 @app.post('/api/projects')
 def project(body:ProjectInput):
  pid=digest(body.name);return store.put('projects',pid,{'project_id':pid,'name':body.name})
 @app.post('/repositories/import')
 @app.post('/api/repositories/import')
 def import_repo(body:ImportInput):
  if bool(body.url)==bool(body.path):raise HTTPException(400,'Supply exactly one path or URL')
  if body.url:
   from urllib.parse import urlparse
   u=urlparse(body.url)
   if u.scheme!='https' or u.hostname not in {'github.com','gitlab.com'} or u.username or u.password or u.query or u.fragment:raise HTTPException(400,'Expected public HTTPS GitHub or GitLab repository URL')
   path=ROOT/'data/repos'/digest(body.url)[:16]
   if not path.exists():
    try:subprocess.run(['git','-c','core.hooksPath=/dev/null','clone','--depth','40','--',body.url,str(path)],check=True,capture_output=True,timeout=180)
    except Exception as e:raise HTTPException(400,'Clone failed: '+type(e).__name__)
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
  if body.model not in {'none','local','cloud','ollama','gemini','claude','omniroute'}:raise HTTPException(400,'Unknown provider')
  if os.getenv('VIGILANT_FREE_ONLY','1')!='0' and body.model in {'cloud','gemini','claude'}:raise HTTPException(400,'Paid or unverified-cost providers are disabled in free-only mode')
  if body.model=='ollama':
   from llm.ollama import OllamaProvider,MODELS_32GB
   if body.ollama_model is not None and body.ollama_model not in MODELS_32GB:raise HTTPException(400,'Select a supported 32 GB model')
   try:OllamaProvider(body.ollama_model).preflight()
   except Exception as exc:raise HTTPException(400,'Local model is not ready: '+str(exc)[:200])
  if body.model=='omniroute':
   from llm.omniroute import OmniRouteProvider
   try:OmniRouteProvider.configuration()
   except ValueError as exc:raise HTTPException(400,str(exc))
  try:
   # Resolve refs before queueing so HEAD cannot silently move while waiting.
   body=body.model_copy(update={'base':revision(repo['path'],body.base),'head':revision(repo['path'],body.head)})
  except Exception as exc:raise HTTPException(400,'Cannot resolve repository revisions: '+type(exc).__name__)
  return submit(body,repo)

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
  edges=store.rows('graph_edges',repository=repository,commit_id=commit_id,limit=limit+1);truncated=len(edges)>limit;edges=edges[:limit]
  ids={e[k] for e in edges for k in ['source_artifact','target_artifact']}
  # Artifact nodes use version keys; commit nodes use their commit identity.
  nodes=[n for n in store.get_many('graph_nodes',[key for i in sorted(ids) for key in (digest(i,commit_id),i)]) if n['repository']==repository and n['commit_id']==commit_id]
  return {'nodes':nodes,'edges':edges,'truncated':truncated}
 @app.get('/api/reports/{run_id}')
 def report(run_id:str):
  r=store.get('analysis_runs',run_id)
  if r is None:raise HTTPException(404,'Run not found')
  return r
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
  return {'items':items,'method':'bm25','source_verified':True,'semantic_entailment_verified':False}
 @app.post('/api/chat')
 def chat(body:ChatInput):
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
  retrieval_query=' '.join([turn.content for turn in history if turn.role=='user']+[body.question])
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
   'source_verified':True,'semantic_entailment_verified':False,
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
  counts={k:0 for k in ['QUEUED','RUNNING','COMPLETED','FAILED']}
  for row in store.rows('analysis_runs'):
   if row.get('kind')=='job' and row.get('status')in counts:counts[row['status']]+=1
  text='# HELP vigilant_jobs Persisted local analysis jobs by status.\n# TYPE vigilant_jobs gauge\n'
  text+=''.join('vigilant_jobs{status="'+k.lower()+'"} '+str(v)+'\n' for k,v in counts.items())
  return Response(text,media_type='text/plain; version=0.0.4')
 dist=ROOT/'frontend/dist'
 if dist.exists():app.mount('/',StaticFiles(directory=dist,html=True),name='frontend')
 return app
app=create_app()
