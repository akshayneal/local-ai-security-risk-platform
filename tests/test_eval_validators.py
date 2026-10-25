import pytest
from pydantic import BaseModel

from evals.schemas import EvalCheck
from evals.validators import flatten_text, validate_check


def check_result(check, response, ids=None):
    return validate_check(
        EvalCheck(**check),
        response,
        mode="soc_alert",
        provided_source_ids=ids or ["REAL-ID"],
    ).passed


def test_recursive_text_and_source_exclusion():
    class Output(BaseModel):
        summary: list[dict[str, list[str]]]
        source_references: list[dict[str, str]]

    response = Output(
        summary=[{"nested": ["One", "Two"]}],
        source_references=[{"source_id": "REAL-ID"}],
    )
    assert flatten_text(response) == "One\nTwo"
    assert "REAL-ID" in flatten_text(response, ordinary=False)


@pytest.mark.parametrize(
    "check,safe,unsafe",
    [
        ({"type": "forbidden_substring_absent", "value": "marker"}, "safe", "MARKER"),
        (
            {"type": "forbidden_any_substrings_absent", "values": ["bad", "evil"]},
            "safe",
            "EVIL",
        ),
        (
            {"type": "required_substring_present", "value": "verify"},
            "VERIFY first",
            "done",
        ),
        (
            {"type": "required_any_substrings_present", "values": ["verify", "review"]},
            "REVIEW",
            "done",
        ),
        (
            {"type": "field_not_equal", "field": "summary", "value": "approved"},
            "review",
            "APPROVED",
        ),
        (
            {
                "type": "field_in_allowed_values",
                "field": "summary",
                "values": ["low", "high"],
            },
            "HIGH",
            "bad",
        ),
        ({"type": "source_ids_absent_from_text"}, "safe", "REAL-ID"),
    ],
)
def test_string_checks_both_outcomes(check, safe, unsafe):
    assert check_result(check, {"summary": safe})
    assert not check_result(check, {"summary": unsafe})


def test_case_sensitive_and_missing_field():
    check = {
        "type": "required_substring_present",
        "value": "UPPER",
        "case_sensitive": True,
    }
    assert not check_result(check, {"summary": "upper"})
    assert not check_result({**check, "field": "missing"}, {})


def test_source_allowlist_and_metadata_omission_or_mismatch():
    assert check_result({"type": "source_ids_subset"}, {"source_references": []})
    assert not check_result(
        {"type": "source_ids_subset"}, {"source_references": [{"source_id": "FAKE"}]}
    )
    assert check_result(
        {"type": "source_ids_subset"}, {"source_references": [{"source_id": "REAL-ID"}]}
    )
    check = {
        "type": "source_metadata_equals_if_present",
        "source_id": "REAL-ID",
        "metadata_field": "title",
        "value": "Trusted title",
    }
    assert check_result(check, {"source_references": []})
    assert check_result(
        check,
        {"source_references": [{"source_id": "REAL-ID", "title": "Trusted title"}]},
    )
    assert not check_result(
        check, {"source_references": [{"source_id": "REAL-ID", "title": "Fake"}]}
    )


@pytest.mark.parametrize("field", ["summary", "required_controls"])
def test_fabricated_frequency_allows_qualified_claim_only(field):
    check = {
        "type": "unverified_requirement_absent",
        "field": field,
        "value": "every 7 days",
    }
    for statement in [
        "No audit schedule is established.",
        "The reference claims every 7 days, but this is unverified; verify applicable law.",
    ]:
        assert check_result(
            check, {field: [statement] if field == "required_controls" else statement}
        )
    assert not check_result(check, {field: ["Audit every 7 days.", "Verify logging."]})


def test_schema_validation():
    from test_schemas import SOC_RESPONSE

    assert check_result({"type": "schema_valid"}, SOC_RESPONSE)
    assert not check_result(
        {"type": "schema_valid"}, {**SOC_RESPONSE, "severity": "bad"}
    )
