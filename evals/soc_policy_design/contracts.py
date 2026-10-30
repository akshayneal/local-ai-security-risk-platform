"""Draft future-workflow shapes, intentionally isolated from released selection."""

from typing import Literal

from pydantic import Field

from app.support_contracts import EvidenceSupportAssessment, SupportModel


class DraftPolicyReviewRequest(SupportModel):
    scenario: Literal["synthetic-unit-a", "synthetic-unit-b"]
    incident_context: str = Field(min_length=1, max_length=4000)
    proposed_action: str = Field(min_length=1, max_length=1000)
    unverified_policy_notes: str = Field(default="", max_length=2000)


class DraftPolicyReviewProposal(SupportModel):
    proposed_escalations: tuple[str, ...] = ()
    verification_needs: tuple[str, ...]
    support_assessments: tuple[EvidenceSupportAssessment, ...] = ()
    application_approval_status: Literal["not_granted_or_verified"] = (
        "not_granted_or_verified"
    )
    human_review_required: Literal[True] = True
    experimental: Literal[True] = True
    scope: Literal["synthetic fixture scenario only; not enterprise access control"] = (
        "synthetic fixture scenario only; not enterprise access control"
    )
