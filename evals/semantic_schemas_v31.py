"""V3.1-only bounded answer keys and reports; no historical schema changes."""

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


class V31Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SemanticFact(V31Model):
    name: Proposition
    established: StrictBool
    # False means NOT established by this closed synthetic record, not globally false.
    support: Literal["telemetry", "synthetic_authority", "unverified_claim", "absent"]
    evidence: str = Field(min_length=1)
    entity: str | None = None
    permitted_source_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid_support(self) -> "SemanticFact":
        if self.name == "actor_attribution" and (
            not self.entity or not self.entity.strip()
        ):
            raise ValueError("Actor fact requires a structured entity")
        if self.name != "actor_attribution" and self.entity is not None:
            raise ValueError("Only actor facts accept entity")
        if self.entity and self.entity not in self.evidence:
            raise ValueError("Actor entity must occur in authoritative fact evidence")
        if self.established and self.support not in {
            "telemetry",
            "synthetic_authority",
        }:
            raise ValueError("Established facts need authoritative support")
        if len(self.permitted_source_ids) != len(set(self.permitted_source_ids)):
            raise ValueError("Duplicate support source IDs")
        return self


class SemanticCheck(V31Model):
    type: Literal[
        "fact_grounding",
        "positive_fact_present",
        "observable_integrity",
        "cross_field",
        "protocol_grounding",
        "positive_protocol_present",
        "endpoint_integrity",
    ]
    fields: list[str] = Field(min_length=1)
    fact: Proposition | None = None
    observable: Literal["ipv4", "sha256", "port"] | None = None

    @model_validator(mode="after")
    def arguments(self) -> "SemanticCheck":
        if len(self.fields) != len(set(self.fields)):
            raise ValueError("Duplicate check fields")
        if self.type == "observable_integrity":
            if self.observable is None or self.fact is not None:
                raise ValueError("Observable check needs only observable kind")
        elif self.type in {
            "protocol_grounding",
            "positive_protocol_present",
            "endpoint_integrity",
        }:
            if self.fact is not None or self.observable is not None:
                raise ValueError("Protocol/endpoint checks use case metadata only")
        elif self.fact is None or self.observable is not None:
            raise ValueError("Proposition check needs only fact")
        if self.type == "cross_field" and len(self.fields) < 2:
            raise ValueError("Cross-field check needs multiple fields")
        return self


Protocol = Literal["SSH", "HTTP", "HTTPS", "RDP"]


class ProtocolFact(V31Model):
    value: Literal["unknown", "SSH", "HTTP", "HTTPS", "RDP"]
    evidence: str = Field(min_length=1)


class EndpointFact(V31Model):
    label: str = Field(min_length=1)
    source_ip: str | None = None
    destination_ip: str | None = None
    destination_port: int | None = Field(default=None, ge=1, le=65535, strict=True)
    protocol: Protocol | None = None
    evidence: str = Field(min_length=1)

    @model_validator(mode="after")
    def endpoint_values(self) -> "EndpointFact":
        from evals.observables import valid_ipv4

        if not self.source_ip and not self.destination_ip:
            raise ValueError("Endpoint needs an IP role")
        for value in [self.source_ip, self.destination_ip]:
            if value is not None and not valid_ipv4(value):
                raise ValueError("Endpoint IP must be valid")
        if self.destination_port is not None and self.destination_ip is None:
            raise ValueError("Destination port needs destination IP")
        return self


class SemanticCase(V31Model):
    test_id: str = Field(pattern=r"^V31-(SOC|GOV)-\d{3}$")
    legacy_case_id: str | None = None
    name: str = Field(min_length=1)
    basis: str = Field(min_length=1)
    category: Category
    mode: Mode
    input: dict[str, Any]
    reference_overrides: list[dict[str, Any]] = Field(default_factory=list)
    facts: list[SemanticFact] = Field(default_factory=list)
    protocol: ProtocolFact | None = None
    endpoints: list[EndpointFact] = Field(default_factory=list)
    positive_control: bool = False
    checks: list[SemanticCheck] = Field(min_length=1)

    @model_validator(mode="after")
    def fact_identity(self) -> "SemanticCase":
        names = [fact.name for fact in self.facts]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate fact identity")
        facts = {fact.name: fact for fact in self.facts}
        labels = [e.label for e in self.endpoints]
        if len(labels) != len(set(labels)):
            raise ValueError("Duplicate endpoint identity")
        positives = [
            c
            for c in self.checks
            if c.type in {"positive_fact_present", "positive_protocol_present"}
        ]
        if self.positive_control != bool(positives):
            raise ValueError("Positive controls require explicit positive checks")
        for endpoint in self.endpoints:
            if endpoint.protocol is not None and (
                self.protocol is None or self.protocol.value != endpoint.protocol
            ):
                raise ValueError("Endpoint protocol contradicts case protocol")
        for check in self.checks:
            if (
                check.type in {"protocol_grounding", "positive_protocol_present"}
                and self.protocol is None
            ):
                raise ValueError("Protocol check needs explicit protocol metadata")
            if (
                check.type == "positive_protocol_present"
                and self.protocol.value == "unknown"
            ):
                raise ValueError("Positive protocol must be established")
            if check.type == "endpoint_integrity" and not self.endpoints:
                raise ValueError("Endpoint check needs endpoint metadata")
            if check.fact is not None and check.fact not in facts:
                raise ValueError("Check refers to unknown fact")
            if (
                check.type == "positive_fact_present"
                and not facts[check.fact].established
            ):
                raise ValueError("Positive check requires established fact")
        return self


class SemanticSuite(V31Model):
    name: str
    version: Literal["3.1"]
    cases: list[SemanticCase] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ids(self) -> "SemanticSuite":
        ids = [case.test_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate case identity")
        legacy = [c.legacy_case_id for c in self.cases if c.legacy_case_id is not None]
        if len(legacy) != len(set(legacy)):
            raise ValueError("Duplicate legacy calibration identity")
        return self


class ClaimMatch(V31Model):
    field: str
    text: str
    token: str | None = None
    state: Literal[
        "asserted",
        "denied",
        "qualified",
        "attributed",
        "question",
        "recommendation",
        "conditional",
    ]


class SemanticCheckResult(V31Model):
    check: SemanticCheck
    passed: bool
    explanation: str
    matches: list[ClaimMatch] = Field(default_factory=list)


class SemanticTrial(V31Model):
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


class SemanticCaseReport(V31Model):
    test_id: str
    category: Category
    positive_control: bool
    totals: TrialTotals
    stability: Literal["stable_pass", "stable_fail", "mixed", "infrastructure_error"]
    trials: list[SemanticTrial]


class SemanticReport(V31Model):
    report_version: Literal["3.1"] = "3.1"
    scorer_version: Literal["3.1"] = "3.1"
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
