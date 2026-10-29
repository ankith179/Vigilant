"""Reviewed change-centric annotations; validation never supplies missing labels."""
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator
from ingestion.models import Status


class SourceReference(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    artifact_id:str=Field(min_length=1)
    commit_id:str=Field(min_length=1)
    file:str=Field(min_length=1)
    content_hash:str=Field(min_length=1)
    start_line:int=Field(ge=1)
    end_line:int=Field(ge=1)

    @model_validator(mode='after')
    def range_valid(self):
        if self.end_line<self.start_line:raise ValueError('Reversed source span')
        return self


class VerificationObligation(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    obligation_id:str=Field(min_length=1)
    requirement:str=Field(min_length=1)
    acceptance_criterion:str=Field(min_length=1)
    lifecycle:Literal['ACTIVE','RETIRED','UNKNOWN']
    applicable_artifact_ids:list[str]
    source:SourceReference
    verification_kind:Literal['TEST','STATIC_CHECK','HUMAN_REVIEW']
    satisfaction:Literal['SATISFIED','UNMET','UNKNOWN']
    evidence:list[SourceReference]
    test_search_coverage:Literal['REVIEWED_COMPLETE','PARTIAL','UNKNOWN']

    @model_validator(mode='after')
    def evidence_for_satisfaction(self):
        if self.satisfaction!='UNKNOWN' and not self.evidence:raise ValueError('A satisfaction judgment requires evidence')
        if self.verification_kind=='TEST' and self.satisfaction=='UNMET' and self.test_search_coverage!='REVIEWED_COMPLETE':raise ValueError('Unmet test obligation requires complete reviewed search scope')
        return self


class ReviewedChangeCase(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    case_id:str=Field(min_length=1)
    repository:str=Field(min_length=1)
    change_family:str=Field(min_length=1)
    base_commit:str=Field(min_length=1)
    head_commit:str=Field(min_length=1)
    change_intent:str=Field(min_length=1)
    consistency_label:Status
    affected_artifact_ids:list[str]
    trace_links:list[str]
    reviewed_negative_links:list[str]
    obligations:list[VerificationObligation]
    obligation_inventory:Literal['REVIEWED','INCOMPLETE','UNKNOWN']
    unknowns:list[str]
    evidence:list[SourceReference]=Field(min_length=1)
    reviewer_ids:list[str]=Field(min_length=2)
    adjudicator_id:str=Field(min_length=1)
    adjudication_rationale:str=Field(min_length=1)
    semantic_support:Literal['ENTAILED','CONTRADICTED','INSUFFICIENT']
    semantic_reviewer_id:str=Field(min_length=1)

    @model_validator(mode='after')
    def reviewed(self):
        if len({r.strip() for r in self.reviewer_ids if r.strip()})<2:raise ValueError('Two distinct nonempty reviewer identities required')
        if any(e.commit_id not in {self.base_commit,self.head_commit} for e in self.evidence):raise ValueError('Evidence outside case revisions')
        if any(o.source.commit_id not in {self.base_commit,self.head_commit} or any(e.commit_id not in {self.base_commit,self.head_commit} for e in o.evidence) for o in self.obligations):raise ValueError('Obligation provenance outside case revisions')
        return self
