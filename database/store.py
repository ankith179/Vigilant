"""SQLite/PostgreSQL-compatible SQLAlchemy persistence with immutable snapshots."""
from pathlib import Path
import os
from contextlib import contextmanager,nullcontext
from threading import RLock
from sqlalchemy import create_engine,MetaData,Table,Column,String,JSON,select,event
from sqlalchemy.pool import StaticPool,NullPool
TABLES='projects repositories commits artifacts trace_links graph_nodes graph_edges embeddings changes evidence analysis_runs findings agent_runs experiments metrics tool_results unknown_revisions'.split()
class Store:
 def __init__(self,url=None):
  url=url or os.getenv('VIGILANT_DB','sqlite:///data/vigilant.db');kwargs={}
  if url.startswith('sqlite'):
   kwargs['connect_args']={'check_same_thread':False};kwargs['poolclass']=NullPool
   if url.endswith(':memory:'):kwargs['poolclass']=StaticPool
   elif url.startswith('sqlite:///'):
    path=Path(url[10:]);path.parent.mkdir(parents=True,exist_ok=True)
    if path.is_file() and path.stat().st_size<1024 and path.read_bytes().startswith(b'version https://git-lfs'):
     raise ValueError('Database is a Git LFS pointer; restore the full checkpoint or fetch LFS objects: '+str(path))
  self.engine=create_engine(url,**kwargs)
  # A StaticPool memory database shares one DBAPI connection across threads.
  self._connection_lock=RLock() if kwargs.get('poolclass') is StaticPool else nullcontext()
  if url.startswith('sqlite'):
   @event.listens_for(self.engine,'connect')
   def setup(c,_):c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA busy_timeout=30000')
  self.meta=MetaData();self.tables={n:Table(n,self.meta,Column('id',String,primary_key=True),*(Column(k,String,index=True) for k in ['project_id','repository','commit_id','run_id']),Column('payload',JSON,nullable=False)) for n in TABLES};self.meta.create_all(self.engine)
 @contextmanager
 def connection(self,write=False):
  with self._connection_lock:
   with (self.engine.begin() if write else self.engine.connect()) as connection:yield connection
 def put(self,table,key,data,replace=False,connection=None):
  return self.put_many(table,[(key,data)],replace,connection)[0]
 def put_many(self,table,entries,replace=False,connection=None):
  entries=list(entries)
  if not entries:return []
  if connection is not None:return self._put_many(connection,table,entries,replace)
  with self.connection(write=True) as c:return self._put_many(c,table,entries,replace)
 def _put_many(self,c,table,entries,replace=False):
  entries=list(entries)
  if not entries:return []
  t=self.tables[table];keys=list(dict.fromkeys(k for k,_ in entries));out=[];pending={}
  def stable(x,key=None):
   if isinstance(x,dict):return {k:stable(v,k) for k,v in x.items() if k not in {'created_at','updated_at'}}
   if isinstance(x,list):return [stable(v) for v in x]
   if isinstance(x,float) and key in {'score','confidence'}:return round(x,12)
   return x
  existing={}
  for start in range(0,len(keys),400):
   rows=c.execute(select(t.c.id,t.c.payload).where(t.c.id.in_(keys[start:start+400]))).mappings()
   existing.update({row['id']:row['payload'] for row in rows})
  for key,data in entries:
   data={**data,'id':key};old=pending.get(key,existing.get(key))
   if old is not None and not replace:
    if stable(old)!=stable(data):raise ValueError('Immutable record conflict: '+table+'/'+key)
    out.append(old);continue
   pending[key]=data;out.append(data)
  if replace:
   replaced=[k for k in pending if k in existing]
   for start in range(0,len(replaced),400):c.execute(t.delete().where(t.c.id.in_(replaced[start:start+400])))
  if pending:c.execute(t.insert(),[{'id':k,'payload':v,**{f:v.get(f) for f in ['project_id','repository','commit_id','run_id']}} for k,v in pending.items()])
  return out
 def rows(self,table,limit=None,offset=0,**filters):
  t=self.tables[table];q=select(t.c.payload)
  for k,v in filters.items():
   if k not in t.c:raise ValueError('Unsupported filter '+k)
   if v is not None:q=q.where(t.c[k]==v)
  q=q.order_by(t.c.id).offset(offset)
  if limit is not None:q=q.limit(limit)
  with self.connection() as c:return list(c.execute(q).scalars())
 def get(self,table,key):
  t=self.tables[table]
  with self.connection() as c:return c.execute(select(t.c.payload).where(t.c.id==key)).scalar_one_or_none()
 def get_many(self,table,keys):
  """Use primary-key lookups without decoding unrelated snapshot payloads."""
  keys=list(dict.fromkeys(keys));t=self.tables[table];out=[]
  with self.connection() as c:
   for start in range(0,len(keys),400):
    out.extend(c.execute(select(t.c.payload).where(t.c.id.in_(keys[start:start+400])).order_by(t.c.id)).scalars())
  return out
 def artifacts(self,repo,commit):
  from ingestion.models import Artifact
  return [Artifact.model_validate({k:v for k,v in row.items() if k!='id'}) for row in self.rows('artifacts',repository=repo,commit_id=commit)]

 def jobs(self):
  t=self.tables['analysis_runs']
  with self.connection() as c:return list(c.execute(select(t.c.payload).where(t.c.payload['kind'].as_string()=='job')).scalars())
 def graph_edges(self,repository,commit,limit):
  t=self.tables['graph_edges'];p=t.c.payload
  q=select(p).where(t.c.repository==repository,t.c.commit_id==commit).order_by(p['relation_type'].as_string(),p['source_artifact'].as_string(),p['target_artifact'].as_string(),t.c.id).limit(limit)
  with self.connection() as c:
   if c.execute(select(t.c.id).where(t.c.repository==repository,t.c.commit_id==commit,p['edge_policy'].as_string()=='typed-v2').limit(1)).first():q=q.where(p['edge_policy'].as_string()=='typed-v2')
   return list(c.execute(q).scalars())
