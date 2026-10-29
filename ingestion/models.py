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
 schema_version:Literal[1,2]=1;decision:Status;confidence:float=Field(ge=0,le=1);evidence_ids:list[str];affected_artifacts:list[str];reason:str;consistency:Status;uncertainty:str
 @model_validator(mode='after')
 def coherent(self):
  if self.schema_version==1 and self.decision!=self.consistency:raise ValueError('Conflicting legacy decision labels')
  if self.schema_version==2 and self.consistency not in {'CONSISTENT','INCONSISTENT','POTENTIAL_INCONSISTENCY','UNCERTAIN'}:raise ValueError('Invalid v2 consistency label')
  if self.schema_version==2 and self.decision in {'CONSISTENT','INCONSISTENT','POTENTIAL_INCONSISTENCY'} and self.decision!=self.consistency:raise ValueError('Conflicting v2 consistency outcomes')
  if (self.decision!='UNCERTAIN' or self.consistency!='UNCERTAIN') and (self.confidence==0 or not self.evidence_ids):raise ValueError('Conclusion without confidence/evidence')
  return self

class DecisionV2(Decision):
 schema_version:Literal[2]
 consistency:Literal['CONSISTENT','INCONSISTENT','POTENTIAL_INCONSISTENCY','UNCERTAIN']

from typing import Any

class FactSource(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 revision:Literal['BASE','HEAD']
 commit_id:str=Field(min_length=1)
 path:str
 start_line:int=Field(ge=1)
 end_line:int=Field(ge=1)
 content_hash:str=Field(pattern=r'^[0-9a-f]{64}$')
 extraction_method:str=Field(min_length=1,max_length=80)
 artifact_role:Literal['requirement','implementation','test','consumer','contract','unknown']='unknown'
 evidence_id:str=Field(min_length=1)
 @model_validator(mode='after')
 def valid_source(self):
  p=PurePosixPath(self.path)
  if p.is_absolute() or '..' in p.parts or self.end_line<self.start_line:raise ValueError('Invalid revision evidence source')
  return self

class SourcedFact(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
 value:Any=None
 sources:list[FactSource]=Field(default_factory=list)
 unknown_reason:str|None=None
 @model_validator(mode='after')
 def provenance_required(self):
  if self.value is None and not self.unknown_reason:raise ValueError('Unknown facts require a reason')
  if self.value is not None and not self.sources:raise ValueError('Known facts require revision-scoped provenance')
  return self
 @classmethod
 def unknown(cls,reason):return cls(value=None,sources=[],unknown_reason=reason)

class FactsV3(BaseModel):
 model_config=ConfigDict(extra='forbid')
 evidence_sufficient:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('not established'))
 has_head_evidence_for_req_impl_test:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('relevance not established'))
 symbol_deleted_at_head:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('not inspected'))
 renamed_to:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('not inspected'))
 declared_link_to_symbol:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('link registry not supplied'))
 head_refs_symbol:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('not inspected'))
 stale_consumer:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('not established'))
 linked_verification_unchanged:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('no revision-bound validation link reviewed'))
 expected_link:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('link expectation not adjudicated'))
 link_present:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('link inventory not supplied'))
 change_kind:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('not classified'))
 comment_has_contract_markers:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('not inspected'))
 doc_default:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('not extracted'))
 sig_default:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('not extracted'))
 default_changed_base_to_head:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('not compared'))
 contract_authority:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('authority review not supplied'))
 requirement_default:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('no normative requirement value supplied'))
 route_changed:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('routes not compared'))
 route_alias_kept:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('alias not checked'))
 consumer_exists:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('consumer inventory incomplete'))
 consumer_matches_new_route:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('consumer route not compared'))
 test_deleted:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('test history not inspected'))
 obligation_explicit:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('approved obligation registry not supplied'))
 other_test_covers_path:SourcedFact=Field(default_factory=lambda:SourcedFact.unknown('coverage not reviewed'))

class DecisionV3(BaseModel):
 """Orthogonal V3 assessment; confidence is raw model output, never calibration."""
 model_config=ConfigDict(extra='forbid',strict=True)
 schema_version:Literal[3]=3
 trace:Literal['LINKED','BROKEN_TRACE','MISSING_TRACE','UNCERTAIN']='UNCERTAIN'
 consistency:Literal['CONSISTENT','INCONSISTENT','POTENTIAL_INCONSISTENCY','NO_ASSURANCE_IMPACT','UNCERTAIN']='UNCERTAIN'
 test_obligation:Literal['SATISFIED','UNSATISFIED','UNVERIFIED','NOT_APPLICABLE']='NOT_APPLICABLE'
 contract_authority:Literal['NORMATIVE','INFORMATIONAL','NOT_ESTABLISHED']='NOT_ESTABLISHED'
 evidence_ids:list[str]=Field(default_factory=list)
 rationale:str=Field(default='',max_length=1000)
 raw_confidence:float|None=Field(default=None,ge=0,le=1)
 rule_id:str=Field(default='R0_INSUFFICIENT_EVIDENCE',max_length=100)
 needs_review:bool=True
 needs_llm:bool=False
 blockers:list[str]=Field(default_factory=list)
 @model_validator(mode='after')
 def prevent_unsupported_consistency(self):
  if self.consistency=='CONSISTENT' and self.blockers:raise ValueError('CONSISTENT is forbidden while blockers are present')
  if self.consistency=='CONSISTENT' and not self.evidence_ids:raise ValueError('CONSISTENT requires cited evidence')
  return self

def legacy_to_v3(record):
 """Conservatively project a legacy label without modifying the source record."""
 raw=record.model_dump() if hasattr(record,'model_dump') else dict(record)
 label=raw.get('decision','UNCERTAIN');cons=raw.get('consistency','UNCERTAIN')
 consistency=cons if cons in {'CONSISTENT','INCONSISTENT','POTENTIAL_INCONSISTENCY','UNCERTAIN'} else 'UNCERTAIN'
 trace=label if label in {'LINKED','BROKEN_TRACE','MISSING_TRACE','UNCERTAIN'} else 'UNCERTAIN'
 test='UNVERIFIED'
 blockers=['legacy_single_label_cannot_recover_orthogonal_axes']
 if consistency=='CONSISTENT':consistency='UNCERTAIN'
 return DecisionV3(trace=trace,consistency=consistency,test_obligation=test,
  contract_authority='NOT_ESTABLISHED',evidence_ids=list(raw.get('evidence_ids',[])),
  rationale='Compatibility projection; historical labels: '+str(label)+' / '+str(cons)+'. No new verification.',
  raw_confidence=raw.get('confidence'),rule_id='LEGACY_V1_V2_MAPPING',
  needs_review=True,blockers=blockers)
