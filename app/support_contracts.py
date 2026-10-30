"""Bounded support relationships with explicit provenance, never confidence scores."""

from enum import StrEnum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StrictStr,
    model_validator,
)

from app.retrieval.contracts import Authority


class ClaimKind(StrEnum):
    OBSERVATION = "observation"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    RECOMMENDATION = "recommendation"
    REQUIREMENT = "requirement"
    IMPLEMENTATION = "implementation"
    UNKNOWN = "unknown"


class Relationship(StrEnum):
    DIRECT = "directly_supports"
    PARTIAL = "partially_supports"
    RELATED = "related_but_insufficient"
    CONFLICT = "conflicting"
    INAPPLICABLE = "inapplicable"
    NONE = "no_eligible_evidence"
    UNASSESSED = "unassessed"


class AssessmentOrigin(StrEnum):
    RECORD_MATCH = "deterministic_record_match"
    MODEL = "model_proposed"
    ANALYST = "analyst_recorded"
    UNASSESSED = "unassessed"


class SupportModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ClaimComponent(SupportModel):
    subject: str = Field(min_length=1, max_length=256)
    predicate: str = Field(min_length=1, max_length=128)
    value: StrictStr | StrictInt | StrictBool = Field(union_mode="left_to_right")
    kind: ClaimKind

    @model_validator(mode="after")
    def bounded_value(self):
        if isinstance(self.value, str) and len(self.value) > 4096:
            raise ValueError("Claim value exceeds bounded support contract")
        return self


class EvidenceClaim(SupportModel):
    claim_id: str = Field(min_length=1, max_length=128)
    components: tuple[ClaimComponent, ...] = Field(min_length=1, max_length=16)
    scope: str | None = Field(default=None, max_length=256)


class SourceSupportProvenance(SupportModel):
    evidence_id: str
    source_id: str
    title: str
    source_family: str
    source_type: str
    authority: Authority
    policy_scope: str | None
    applicability: tuple[str, ...]
    document_version_id: str | None
    version_status: str
    content_sha256: str
    eligibility: Literal["workflow/access/policy/date/metadata currentness checked"] = (
        "workflow/access/policy/date/metadata currentness checked"
    )
    registry_check: Literal["not_applicable", "passed"] = "not_applicable"


class ComponentSupport(SupportModel):
    component_index: int = Field(ge=0)
    relationship: Relationship
    supporting_evidence_ids: tuple[str, ...] = ()
    conflicting_evidence_ids: tuple[str, ...] = ()
    reason: str


class EvidenceSupportAssessment(SupportModel):
    claim_id: str
    candidate_evidence_ids: tuple[str, ...]
    relationship: Relationship
    supporting_evidence_ids: tuple[str, ...] = ()
    source_provenance: tuple[SourceSupportProvenance, ...] = ()
    components: tuple[ComponentSupport, ...] = ()
    provenance: AssessmentOrigin
    verification_status: Literal["record_match_only", "not_verified"]
    review_required: Literal[True] = True
    external_verification: Literal["not_performed"] = "not_performed"
    limitation: str = "A record match establishes what an eligible record asserts, not external truth or general natural-language entailment."

    @model_validator(mode="after")
    def proposals_are_not_verified(self):
        if (
            self.provenance != AssessmentOrigin.RECORD_MATCH
            and self.verification_status != "not_verified"
        ):
            raise ValueError(
                "Proposed or manual support is not deterministic verification"
            )
        if not set(self.supporting_evidence_ids) <= set(self.candidate_evidence_ids):
            raise ValueError("Support identities must be eligible candidate identities")
        return self
