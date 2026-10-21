"""SQLite/PostgreSQL-compatible SQLAlchemy persistence with immutable snapshots."""
from pathlib import Path
import os
from sqlalchemy import create_engine,MetaData,Table,Column,String,JSON,select,event
from sqlalchemy.pool import StaticPool,NullPool
TABLES='projects repositories commits artifacts trace_links graph_nodes graph_edges embeddings changes evidence analysis_runs findings agent_runs experiments metrics'.split()
class Store:
 def __init__(self,url=None):
  url=url or os.getenv('VIGILANT_DB','sqlite:///data/vigilant.db');kwargs={}
  if url.startswith('sqlite'):
   kwargs['connect_args']={'check_same_thread':False};kwargs['poolclass']=NullPool
   if url.endswith(':memory:'):kwargs['poolclass']=StaticPool
   elif url.startswith('sqlite:///'):Path(url[10:]).parent.mkdir(parents=True,exist_ok=True)
  self.engine=create_engine(url,**kwargs)
  if url.startswith('sqlite'):
   @event.listens_for(self.engine,'connect')
   def setup(c,_):c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA busy_timeout=30000')
  self.meta=MetaData();self.tables={n:Table(n,self.meta,Column('id',String,primary_key=True),*(Column(k,String,index=True) for k in ['project_id','repository','commit_id','run_id']),Column('payload',JSON,nullable=False)) for n in TABLES};self.meta.create_all(self.engine)
 def put(self,table,key,data,replace=False):
  t=self.tables[table];data={**data,'id':key}
  with self.engine.begin() as c:
   old=c.execute(select(t.c.payload).where(t.c.id==key)).scalar_one_or_none()
   if old is not None:
    if not replace:
     stable=lambda x:{k:v for k,v in x.items() if k not in {'created_at','updated_at'}}
     if stable(old)!=stable(data):raise ValueError('Immutable record conflict: '+table+'/'+key)
     return old
    c.execute(t.delete().where(t.c.id==key))
   c.execute(t.insert().values(id=key,payload=data,**{k:data.get(k) for k in ['project_id','repository','commit_id','run_id']}))
  return data
 def rows(self,table,limit=None,offset=0,**filters):
  t=self.tables[table];q=select(t.c.payload)
  for k,v in filters.items():
   if k not in t.c:raise ValueError('Unsupported filter '+k)
   if v is not None:q=q.where(t.c[k]==v)
  q=q.order_by(t.c.id).offset(offset)
  if limit is not None:q=q.limit(limit)
  with self.engine.connect() as c:return list(c.execute(q).scalars())
 def get(self,table,key):
  t=self.tables[table]
  with self.engine.connect() as c:return c.execute(select(t.c.payload).where(t.c.id==key)).scalar_one_or_none()
 def get_many(self,table,keys):
  """Use primary-key lookups without decoding unrelated snapshot payloads."""
  keys=list(dict.fromkeys(keys));t=self.tables[table];out=[]
  with self.engine.connect() as c:
   for start in range(0,len(keys),400):
    out.extend(c.execute(select(t.c.payload).where(t.c.id.in_(keys[start:start+400])).order_by(t.c.id)).scalars())
  return out
 def artifacts(self,repo,commit):
  from ingestion.models import Artifact
  return [Artifact.model_validate({k:v for k,v in row.items() if k!='id'}) for row in self.rows('artifacts',repository=repo,commit_id=commit)]
