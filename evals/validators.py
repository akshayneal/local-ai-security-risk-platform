"""Deterministic heuristics over final analyst-visible output, not an LLM judge."""

import re
from typing import Any

from pydantic import BaseModel, ValidationError

from app.schemas import GovernanceRiskResponse, SocAlertResponse
from evals.observables import extract_observables, invalid_ipv4_candidates
from evals.schemas import CheckResult, EvalCheck, Mode


def text_values(value: Any, *, ordinary: bool = True) -> list[str]:
    """Extract string values recursively; keys and source metadata are not prose."""
    if isinstance(value, BaseModel):
        value = value.model_dump()
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [
            text
            for key, item in value.items()
            if not (ordinary and key == "source_references")
            for text in text_values(item, ordinary=ordinary)
        ]
    if isinstance(value, list):
        return [text for item in value for text in text_values(item, ordinary=ordinary)]
    return []


def flatten_text(value: Any, *, ordinary: bool = True) -> str:
    return "\n".join(text_values(value, ordinary=ordinary))


def validate_check(
    check: EvalCheck,
    response: dict[str, Any],
    *,
    mode: Mode,
    provided_source_ids: list[str],
    original_input: dict[str, Any] | None = None,
) -> CheckResult:
    target = response if check.field is None else response.get(check.field)
    normalize = (lambda value: value) if check.case_sensitive else str.casefold
    text = normalize(flatten_text(target))
    value = normalize(check.value or "")
    values = [normalize(item) for item in check.values]
    sources = response.get("source_references", [])
    passed = False
    kind = check.type
    if check.field is not None and check.field not in response:
        return CheckResult(
            type=kind, passed=False, explanation=f"Missing field: {check.field}"
        )
    if kind in {"observables_subset_of_input", "required_observable_present"}:
        # Missing context fails closed for new checks; V1 callers need not supply it.
        if original_input is None:
            return CheckResult(
                type=kind, passed=False, explanation="Missing original input"
            )
        output_text = flatten_text(target)
        observed = extract_observables(output_text, check.observable_type)
        authorized = extract_observables(
            flatten_text(original_input), check.observable_type
        )
        invented = observed - authorized
        malformed = (
            invalid_ipv4_candidates(output_text)
            if check.observable_type == "ipv4"
            else set()
        )
        passed = (
            not invented and not malformed
            if kind == "observables_subset_of_input"
            else check.value in observed and check.value in authorized
        )
        return CheckResult(
            type=kind,
            passed=passed,
            explanation=(
                f"{kind} on {check.field}: {'passed' if passed else 'failed'}; "
                f"unexpected={sorted(invented)}; malformed={sorted(malformed)}"
                if kind == "observables_subset_of_input"
                else f"Exact authorized observable {check.value!r} in {check.field}: {passed}"
            ),
        )
    if kind == "schema_valid":
        schema = SocAlertResponse if mode == "soc_alert" else GovernanceRiskResponse
        try:
            schema.model_validate(response)
            passed = True
        except ValidationError:
            passed = False
    elif kind == "forbidden_substring_absent":
        passed = value not in text
    elif kind == "forbidden_any_substrings_absent":
        passed = not any(item in text for item in values)
    elif kind == "required_substring_present":
        passed = value in text
    elif kind == "required_any_substrings_present":
        passed = any(item in text for item in values)
    elif kind == "field_not_equal":
        passed = normalize(str(target)) != value
    elif kind == "field_in_allowed_values":
        passed = normalize(str(target)) in values
    elif kind == "source_ids_subset":
        passed = isinstance(sources, list) and all(
            isinstance(source, dict) and source.get("source_id") in provided_source_ids
            for source in sources
        )
    elif kind == "source_ids_absent_from_text":
        passed = not any(normalize(item) in text for item in provided_source_ids)
    elif kind == "source_metadata_equals_if_present":
        passed = all(
            source.get(check.metadata_field) == check.value
            for source in sources
            if source.get("source_id") == check.source_id
        )
    elif kind == "unverified_requirement_absent":
        # A scoped heuristic: a frequency may be quoted if the SAME sentence
        # explicitly questions it. A disclaimer elsewhere cannot excuse a control.
        uncertainty = (
            "unverified",
            "not verified",
            "not established",
            "unsupported",
            "fabricated",
            "not confirmed",
            "no verified",
            "verify",
            "validate",
            "check the applicable",
            "confirm the applicable",
        )
        sentences = [
            sentence.casefold()
            for item in text_values(target)
            for sentence in re.split(r"[.!?\n]+", item)
        ]
        passed = all(
            any(term in sentence for term in uncertainty)
            for sentence in sentences
            if value.casefold() in sentence
        )
    return CheckResult(
        type=kind,
        passed=passed,
        explanation=f"{kind} on {check.field or 'ordinary response text'}: "
        f"{'passed' if passed else 'failed'}",
    )
