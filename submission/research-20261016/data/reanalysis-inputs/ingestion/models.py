"""Deterministic artifact identity is independent of content, lines, and commits."""
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Literal
import json
from pydantic import BaseModel,ConfigDict,Field,model_validator

def digest(*parts):return sha256(json.dumps(parts,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
class Artifact(BaseModel):
 model_config=ConfigDict(extra='forbid')
 artifact_id:str;project_id:str;repository:str;artifact_type:str;file_path:str;symbol:str='';content:str
 start_line:int=Field(ge=1);end_line:int=Field(ge=1);commit_id:str;version:str;content_hash:str
 metadata:dict=Field(default_factory=dict);created_at:str=Field(default_factory=now);updated_at:str=Field(default_factory=now)
 @model_validator(mode='after')
 def validate_artifact(self):
  if self.end_line<self.start_line or self.content_hash!=digest(self.content):raise ValueError('Invalid range or content hash')
  p=PurePosixPath(self.file_path)
  if p.is_absolute() or '..' in p.parts:raise ValueError('Path must be repository-relative')
  return self

def artifact(project,repo,commit,path,kind,symbol,content,start=1,end=None,metadata=None):
 h=digest(content)
 return Artifact(artifact_id=digest(project,repo,path,kind,symbol),project_id=project,repository=repo,artifact_type=kind,file_path=path,symbol=symbol,content=content,start_line=start,end_line=end or start+max(1,len(content.splitlines()))-1,commit_id=commit,version=h,content_hash=h,metadata=metadata or {})
Status=Literal['CONSISTENT','INCONSISTENT','POTENTIAL_INCONSISTENCY','BROKEN_TRACE','MISSING_TEST','AFFECTED','UNCERTAIN']
class Decision(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 decision:Status;confidence:float=Field(ge=0,le=1);evidence_ids:list[str];affected_artifacts:list[str];reason:str;consistency:Status;uncertainty:str
 @model_validator(mode='after')
 def coherent(self):
  if self.decision!=self.consistency:raise ValueError('Conflicting decision labels')
  if self.decision!='UNCERTAIN' and (self.confidence==0 or not self.evidence_ids):raise ValueError('Conclusion without confidence/evidence')
  return self
