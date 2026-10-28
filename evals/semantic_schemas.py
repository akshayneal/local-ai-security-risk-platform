"""V3-only bounded answer keys and reports; no historical schema changes."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from evals.reliability_schemas import ModelCall, RuntimeProvenance, TrialTotals
from evals.schemas import Mode

Proposition = Literal[
    "malicious_reputation",
    "actor_attribution",
    "legal_obligation",
    "weekly_audit",
    "authentication_success",
    "process_execution",
    "maintenance_authorized",
    "compromise",
]
Category = Literal[
    "claim_authority",
    "event_grounding",
    "observable_fidelity",
    "cross_field_consistency",
]


class V3Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SemanticFact(V3Model):
    name: Proposition
    established: StrictBool
    # False means NOT established by this closed synthetic record, not globally false.
    support: Literal["telemetry", "synthetic_authority", "unverified_claim", "absent"]
    evidence: str = Field(min_length=1)
    permitted_source_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid_support(self) -> "SemanticFact":
        if self.established and self.support not in {
            "telemetry",
            "synthetic_authority",
        }:
            raise ValueError("Established facts need authoritative support")
        if len(self.permitted_source_ids) != len(set(self.permitted_source_ids)):
            raise ValueError("Duplicate support source IDs")
        return self


class SemanticCheck(V3Model):
    type: Literal[
        "fact_grounding", "positive_fact_present", "observable_integrity", "cross_field"
    ]
    fields: list[str] = Field(min_length=1)
    fact: Proposition | None = None
    observable: Literal["ipv4", "sha256"] | None = None

    @model_validator(mode="after")
    def arguments(self) -> "SemanticCheck":
        if len(self.fields) != len(set(self.fields)):
            raise ValueError("Duplicate check fields")
        if self.type == "observable_integrity":
            if self.observable is None or self.fact is not None:
                raise ValueError("Observable check needs only observable kind")
        elif self.fact is None or self.observable is not None:
            raise ValueError("Proposition check needs only fact")
        if self.type == "cross_field" and len(self.fields) < 2:
            raise ValueError("Cross-field check needs multiple fields")
        return self


class SemanticCase(V3Model):
    test_id: str = Field(pattern=r"^V3-(SOC|GOV)-\d{3}$")
    name: str = Field(min_length=1)
    basis: str = Field(min_length=1)
    category: Category
    mode: Mode
    input: dict[str, Any]
    reference_overrides: list[dict[str, Any]] = Field(default_factory=list)
    facts: list[SemanticFact] = Field(default_factory=list)
    positive_control: bool = False
    checks: list[SemanticCheck] = Field(min_length=1)

    @model_validator(mode="after")
    def fact_identity(self) -> "SemanticCase":
        names = [fact.name for fact in self.facts]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate fact identity")
        facts = {fact.name: fact for fact in self.facts}
        positives = [c for c in self.checks if c.type == "positive_fact_present"]
        if self.positive_control != bool(positives):
            raise ValueError("Positive controls require explicit positive checks")
        for check in self.checks:
            if check.fact is not None and check.fact not in facts:
                raise ValueError("Check refers to unknown fact")
            if (
                check.type == "positive_fact_present"
                and not facts[check.fact].established
            ):
                raise ValueError("Positive check requires established fact")
        return self


class SemanticSuite(V3Model):
    name: str
    version: Literal["3.0"]
    cases: list[SemanticCase] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ids(self) -> "SemanticSuite":
        ids = [case.test_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate case identity")
        return self


class ClaimMatch(V3Model):
    field: str
    text: str
    state: Literal["asserted", "denied", "qualified"]


class SemanticCheckResult(V3Model):
    check: SemanticCheck
    passed: bool
    explanation: str
    matches: list[ClaimMatch] = Field(default_factory=list)


class SemanticTrial(V3Model):
    trial: int = Field(ge=1)
    passed: bool
    response: dict[str, Any] | None
    error: str | None
    checks: list[SemanticCheckResult]
    duration_seconds: float = Field(ge=0, allow_inf_nan=False)
    provided_source_ids: list[str]
    model_calls: list[ModelCall]
    analysis_trace: dict[str, Any] | None

    @model_validator(mode="after")
    def outcome(self) -> "SemanticTrial":
        if self.error is not None:
            if self.passed or self.response is not None or self.checks:
                raise ValueError("Error trials have no scored response")
        elif (
            self.response is None
            or not self.checks
            or self.passed != all(c.passed for c in self.checks)
        ):
            raise ValueError("Invalid scored trial")
        return self


class SemanticCaseReport(V3Model):
    test_id: str
    category: Category
    positive_control: bool
    totals: TrialTotals
    stability: Literal["stable_pass", "stable_fail", "mixed", "infrastructure_error"]
    trials: list[SemanticTrial]


class SemanticReport(V3Model):
    report_version: Literal["3.0"] = "3.0"
    suite_byte_sha256: str
    suite_semantic_sha256: str
    provenance: RuntimeProvenance
    file_sha256: dict[str, str]
    started_utc: str
    ended_utc: str
    trials_per_case: int = Field(ge=1)
    totals: TrialTotals
    category_summary: dict[str, TrialTotals]
    positive_control_totals: TrialTotals
    stability_counts: dict[str, int]
    total_model_calls: int
    failed_model_calls: int
    cases: list[SemanticCaseReport]
