"""Small, validated definitions for deterministic application evaluations."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Category = Literal[
    "direct_prompt_injection",
    "indirect_prompt_injection",
    "retrieval_poisoning",
    "source_integrity",
    "conflicting_evidence",
    "excessive_agency",
    "unsupported_claims",
]
Mode = Literal["soc_alert", "governance"]
Severity = Literal["low", "medium", "high", "critical"]
CheckType = Literal[
    "schema_valid",
    "forbidden_substring_absent",
    "forbidden_any_substrings_absent",
    "required_substring_present",
    "required_any_substrings_present",
    "field_not_equal",
    "field_in_allowed_values",
    "source_ids_subset",
    "source_ids_absent_from_text",
    "source_metadata_equals_if_present",
    "unverified_requirement_absent",
]


class EvalCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: CheckType
    field: str | None = None  # None scans ordinary text, excluding source_references.
    value: str | None = None
    values: list[str] = Field(default_factory=list)
    source_id: str | None = None
    metadata_field: Literal["title", "framework"] | None = None
    case_sensitive: bool = False

    @model_validator(mode="after")
    def validate_arguments(self) -> "EvalCheck":
        scalar = {
            "forbidden_substring_absent",
            "required_substring_present",
            "field_not_equal",
            "source_metadata_equals_if_present",
            "unverified_requirement_absent",
        }
        multiple = {
            "forbidden_any_substrings_absent",
            "required_any_substrings_present",
            "field_in_allowed_values",
        }
        if self.type in scalar and not self.value:
            raise ValueError("This check requires a nonempty value")
        if self.type in multiple and (not self.values or not all(self.values)):
            raise ValueError("This check requires nonempty values")
        if (
            self.type in {"field_not_equal", "field_in_allowed_values"}
            and not self.field
        ):
            raise ValueError("Field comparison requires field")
        if self.type == "source_metadata_equals_if_present" and (
            not self.source_id or not self.metadata_field
        ):
            raise ValueError("Metadata check requires source_id and metadata_field")
        return self


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    test_id: str = Field(pattern=r"^(SOC|GOV)-[A-Z]+-\d{3}$")
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: Category
    severity: Severity
    mode: Mode
    input: dict[str, Any]
    reference_overrides: list[dict[str, Any]] | None = None
    expected_safe_behavior: str = Field(min_length=1)
    checks: list[EvalCheck] = Field(min_length=1)


class EvaluationSuite(BaseModel):
    cases: list[EvaluationCase] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ids(self) -> "EvaluationSuite":
        ids = [case.test_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate evaluation test_id")
        return self


class CheckResult(BaseModel):
    type: CheckType
    passed: bool
    explanation: str


class EvaluationResult(BaseModel):
    test_id: str
    category: Category
    severity: Severity
    mode: Mode
    passed: bool
    check_results: list[CheckResult] = Field(default_factory=list)
    response: dict[str, Any] | None = None
    error: str | None = None
    provided_source_ids: list[str] = Field(default_factory=list)
    duration_seconds: float = Field(ge=0)


class Summary(BaseModel):
    total: int
    passed: int
    failed: int
    pass_rate: float


class EvaluationReport(BaseModel):
    model: str
    timestamp_utc: str
    git_commit: str | None
    suite_hash: str
    # The hash covers the complete file; selection records any filtered execution.
    selected_case_ids: list[str]
    total_cases: int
    passed: int
    failed: int
    pass_rate: float
    category_summary: dict[str, Summary]
    severity_summary: dict[str, Summary]
    results: list[EvaluationResult]
