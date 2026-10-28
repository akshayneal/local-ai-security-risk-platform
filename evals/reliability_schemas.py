"""V2-only repeated reports. Frozen V1 report fields retain their meaning."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from evals.schemas import Category, EvaluationResult, EvaluationSuite, Mode, Severity


class V2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReliabilitySuite(EvaluationSuite):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class RuntimeProvenance(V2Model):
    python_version: str
    ollama_version: str | None
    model: str
    model_digest: str | None
    model_digest_kind: Literal["ollama_ls_short_id"] | None
    git_commit: str | None
    git_dirty: bool | None
    temperature: float
    seed: int | None = None
    seed_state: Literal["not_configured"] = "not_configured"
    unavailable: list[str] = Field(default_factory=list)


class ModelCall(V2Model):
    duration_seconds: float = Field(ge=0, allow_inf_nan=False)
    completed: bool
    error_type: str | None = None
    generation: Literal["initial", "repair"] = "initial"

    @model_validator(mode="after")
    def consistent_error(self) -> "ModelCall":
        if self.completed == (self.error_type is not None):
            raise ValueError(
                "Completed calls have no error; failed calls require an error type"
            )
        return self


class TrialResult(V2Model):
    trial: int = Field(ge=1)
    result: EvaluationResult
    model_calls: list[ModelCall] = Field(default_factory=list)
    analysis_trace: dict[str, Any] | None = None

    @model_validator(mode="after")
    def valid_outcome(self) -> "TrialResult":
        if self.result.error and (
            self.result.passed or self.result.response is not None
        ):
            raise ValueError(
                "Application-error trials cannot pass or have a final response"
            )
        if not self.result.error and self.result.response is None:
            raise ValueError("Completed trials require a final response")
        return self


class LatencySummary(V2Model):
    completed: int = Field(ge=0)
    minimum_seconds: float | None
    median_seconds: float | None
    mean_seconds: float | None
    maximum_seconds: float | None


class ValueCount(V2Model):
    value: str | list[str] | None
    count: int = Field(ge=1)


class FieldStability(V2Model):
    observed_values: list[ValueCount]
    identical: bool | None  # None when no valid final response exists.


class TrialTotals(V2Model):
    trials_requested: int = Field(ge=1)
    trials_attempted: int = Field(ge=0)
    trials_completed: int = Field(ge=0)
    trials_passed: int = Field(ge=0)
    trials_failed: int = Field(ge=0)
    application_error_count: int = Field(ge=0)
    pass_rate: float = Field(ge=0, le=100, allow_inf_nan=False)

    @model_validator(mode="after")
    def valid_totals(self) -> "TrialTotals":
        if not (
            self.trials_attempted <= self.trials_requested
            and self.trials_completed + self.application_error_count
            == self.trials_attempted
            and self.trials_passed + self.trials_failed == self.trials_completed
        ):
            raise ValueError("Inconsistent trial counts")
        expected = (
            100 * self.trials_passed / self.trials_completed
            if self.trials_completed
            else 0
        )
        if abs(self.pass_rate - expected) > 1e-9:
            raise ValueError("Pass rate must use completed valid trials")
        return self


class CaseReliabilitySummary(TrialTotals):
    test_id: str
    category: Category
    severity: Severity
    mode: Mode
    stability: Literal["stable_pass", "stable_fail", "mixed", "infrastructure_error"]
    latency: LatencySummary
    structured_output_stability: dict[str, FieldStability]
    trials: list[TrialResult]


class RepeatedEvaluationReport(V2Model):
    report_version: Literal["2.0"] = "2.0"
    suite_name: str
    suite_version: str
    suite_byte_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    suite_semantic_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provenance: RuntimeProvenance
    started_utc: str
    ended_utc: str
    trials_per_case: int = Field(ge=1)
    selected_case_ids: list[str]
    total_cases: int = Field(ge=1)
    totals: TrialTotals
    total_model_calls_attempted: int = Field(ge=0)
    total_completed_model_calls: int = Field(ge=0)
    model_call_error_count: int = Field(ge=0)
    # Trial-level application/runtime errors, distinct from assertion failures.
    total_infrastructure_errors: int = Field(ge=0)
    stability_counts: dict[str, int]
    category_aggregation: Literal["trial_weighted_completed_valid_trials"] = (
        "trial_weighted_completed_valid_trials"
    )
    category_summary: dict[str, TrialTotals]
    latency: (
        LatencySummary  # Completed valid analyzer trials, including cleanup/checks.
    )
    model_call_latency: (
        LatencySummary  # Completed raw client.chat calls (incl. retries).
    )
    cases: list[CaseReliabilitySummary]
