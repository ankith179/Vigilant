from pathlib import Path
import re
from ingestion.git import git,revision,snapshot
from ingestion.models import digest
from ingestion.parsers import extract

def import_repository(store,path,project='vigilant',rev='HEAD',repository_id=None):
 path=Path(path).resolve();commit=revision(path,rev)
 try:origin=git(path,'remote','get-url','origin')
 except Exception:origin=str(path)
 rid=repository_id or digest(project,origin)
 staged=store.get('commits',digest(rid,commit))
 if staged is not None and 'review_source_map' in staged:
  # Partial staged identities must not enter the full-import workflow, even when
  # no artifacts are available. Reject before repository/commit metadata writes.
  raise ValueError('Staged source snapshot requires an explicit existing-snapshot investigation route; repository import is disabled')
 if not store.get('projects',project):store.put('projects',project,{'project_id':project,'name':project})
 existing=store.get('repositories',rid)
 if not existing or existing['path']!=str(path):store.put('repositories',rid,{'project_id':project,'repository':rid,'name':path.name,'path':str(path),'origin':origin},replace=bool(existing))
 store.put('commits',digest(rid,commit),{'project_id':project,'repository':rid,'commit_id':commit,'subject':git(path,'show','-s','--format=%s',commit),'timestamp':git(path,'show','-s','--format=%cI',commit)})
 # Frozen snapshot identities are never silently reparsed under a new parser policy.
 prior=store.artifacts(rid,commit)
 if prior:return {'repository':rid,'commit_id':commit,'artifact_count':len(prior),'files':sum(not a.symbol for a in prior),'parse_failures':sum(bool(a.metadata.get('parse_error') or a.metadata.get('parse_has_error')) for a in prior)}
 texts=dict(snapshot(path,commit));items=[]
 for file,content in texts.items():items.extend(extract(project,rid,commit,file,content,source_files=texts))
 prefix=re.search(r'API_V1_STR\s*:\s*str\s*=\s*[\'"]([^\'"]+)',texts.get('backend/app/core/config.py',''))
 if prefix and 'app.include_router(api_router, prefix=settings.API_V1_STR)' in texts.get('backend/app/main.py',''):
  for a in items:
   if a.artifact_type=='api' and a.file_path.startswith('backend/app/api/routes/'):
    a.metadata['route']=prefix[1]+a.metadata['route'];a.metadata['prefix_provenance']=['backend/app/core/config.py','backend/app/main.py'];a.metadata['resolution']='FastAPI-template explicit prefix adapter'
 store.put_many('artifacts',[(digest(a.artifact_id,commit),a.model_dump()) for a in items])
 return {'repository':rid,'commit_id':commit,'artifact_count':len(items),'files':sum(not a.symbol for a in items),'parse_failures':sum(bool(a.metadata.get('parse_error') or a.metadata.get('parse_has_error')) for a in items)}
