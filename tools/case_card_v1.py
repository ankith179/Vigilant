"""Case-card validation. Reviewers supply labels; the pipeline never creates them."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Artifact(StrictModel):
    path: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class Artifacts(StrictModel):
    requirement: list[Artifact]
    code: list[Artifact]
    test: list[Artifact]


class RequirementSource(StrictModel):
    kind: Literal["NORMATIVE", "DOCUMENTATION_DERIVED", "AUTHORED"]
    reference: str = Field(min_length=1)
    review_id: str = Field(min_length=1)


class Adjudication(StrictModel):
    status: Literal["PENDING", "IN_REVIEW", "ADJUDICATED", "UNRESOLVED"]
    reviewer_ids: list[str]
    rationale: str | None


class CaseCard(StrictModel):
    case_id: str = Field(min_length=1)
    d_ids: list[str]
    priority_tier: Literal["P1", "P2", "P3", "P4"]
    origin: Literal["MINED", "CURATED", "SYNTHETIC"]
    source_id: str = Field(min_length=1)
    family: str = Field(min_length=1)
    split: Literal["dev", "test"]
    history_source: Literal["A", "B", "C", "D"]
    base_revision: str = Field(min_length=1)
    head_revision: str = Field(min_length=1)
    artifacts: Artifacts
    change_facts: dict
    requirement_source: RequirementSource | None
    expected_trace: Literal["LINKED", "BROKEN_TRACE", "MISSING_TRACE", "UNCERTAIN"] | None
    expected_consistency: Literal["CONSISTENT", "INCONSISTENT", "POTENTIAL_INCONSISTENCY", "NO_ASSURANCE_IMPACT", "UNCERTAIN"] | None
    expected_test_obligation: Literal["SATISFIED", "UNSATISFIED", "UNVERIFIED", "NOT_APPLICABLE"] | None
    expected_authority: Literal["NORMATIVE", "INFORMATIONAL", "NOT_ESTABLISHED"] | None
    impact_ground_truth: list[str] | None
    supporting_evidence_ids: list[str]
    adjudication: Adjudication
    notes: str
    allow_synthetic_test: bool = False
    label_status: Literal["UNREVIEWED_SILVER", "ADJUDICATED"]

    @model_validator(mode="after")
    def verify_integrity(self):
        labels = (self.expected_trace, self.expected_consistency, self.expected_test_obligation,
                  self.expected_authority, self.impact_ground_truth)
        if self.adjudication.status != "ADJUDICATED" and any(value is not None for value in labels):
            raise ValueError("labels require adjudication")
        if self.origin == "MINED" and self.label_status == "UNREVIEWED_SILVER" and any(value is not None for value in labels):
            raise ValueError("unreviewed mined cases cannot contain labels")
        if self.label_status == "ADJUDICATED" and self.adjudication.status != "ADJUDICATED":
            raise ValueError("adjudicated label status requires adjudication")
        if self.adjudication.status == "ADJUDICATED" and (self.label_status != "ADJUDICATED" or not self.adjudication.reviewer_ids or not self.adjudication.rationale):
            raise ValueError("adjudication requires reviewer identity and rationale")
        if self.origin == "SYNTHETIC" and self.split == "test" and not self.allow_synthetic_test:
            raise ValueError("synthetic test case requires explicit approval")
        refs = self.artifacts.requirement + self.artifacts.code + self.artifacts.test
        if not refs:
            raise ValueError("at least one hashed artifact is required")
        if any(ref.revision not in (self.base_revision, self.head_revision) for ref in refs):
            raise ValueError("artifact revision is outside case revisions")
        return self
