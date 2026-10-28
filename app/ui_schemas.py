"""Allowlisted product metadata, separate from frozen analysis response models."""

from typing import Any, Literal

from pydantic import BaseModel

from app.analysis_trace import AnalysisTrace
from app.schemas import GovernanceRiskResponse, SocAlertResponse

INTEGRITY_FAILURE_MESSAGE = (
    "The generated analysis could not satisfy the application's factual-integrity "
    "contract after one repair attempt. No analyst result was returned."
)
COMMON_CHECKS = ("schema validation", "source-reference sanitization")
SOC_CHECKS = COMMON_CHECKS + (
    "critical identity integrity",
    "endpoint integrity",
    "observed-evidence contract",
)


class ProductTrace(AnalysisTrace):
    """Keep analyzer repair flags without retaining any diagnostic snapshots."""

    def capture(self, stage: str, value: Any, *, generation: int = 0) -> None:
        pass


class GovernanceMetadata(BaseModel):
    model: str
    local_execution: Literal[True] = True
    human_review_required: Literal[True] = True
    checks: tuple[str, ...] = COMMON_CHECKS


class SocMetadata(GovernanceMetadata):
    integrity_status: Literal["passed"] = "passed"
    repair_attempted: bool
    repair_succeeded: bool | None
    checks: tuple[str, ...] = SOC_CHECKS


class GovernanceAnalysisEnvelope(BaseModel):
    analysis: GovernanceRiskResponse
    metadata: GovernanceMetadata


class SocAnalysisEnvelope(BaseModel):
    analysis: SocAlertResponse
    metadata: SocMetadata
