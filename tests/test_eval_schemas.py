import pytest
from pydantic import ValidationError

from evals.runner import load_suite
from evals.schemas import EvalCheck, EvaluationCase, EvaluationSuite


def test_suite_has_exact_initial_cases_and_valid_requests():
    from app.schemas import GovernanceRiskRequest, SocAlertRequest

    suite, digest = load_suite()
    assert len(suite.cases) == 12
    assert len({case.category for case in suite.cases}) == 7
    assert len(digest) == 64
    for case in suite.cases:
        schema = SocAlertRequest if case.mode == "soc_alert" else GovernanceRiskRequest
        schema.model_validate(case.input)


@pytest.mark.parametrize(
    "field,value",
    [
        ("category", "unknown"),
        ("mode", "tools"),
        ("test_id", "bad id"),
        ("severity", "urgent"),
        ("checks", []),
    ],
)
def test_invalid_cases_rejected(field, value):
    case = load_suite()[0].cases[0].model_dump()
    case[field] = value
    with pytest.raises(ValidationError):
        EvaluationCase.model_validate(case)


def test_duplicate_ids_rejected():
    case = load_suite()[0].cases[0]
    with pytest.raises(ValidationError, match="Duplicate"):
        EvaluationSuite(cases=[case, case])


def test_suite_hash_tracks_actual_case_file_bytes(tmp_path):
    from evals.runner import CASE_PATH

    path = tmp_path / "suite.json"
    data = CASE_PATH.read_bytes()
    path.write_bytes(data)
    original = load_suite(path)[1]
    path.write_bytes(data + b"\n")
    assert load_suite(path)[1] != original


@pytest.mark.parametrize(
    "check",
    [
        {"type": "execute"},
        {"type": "forbidden_substring_absent"},
        {"type": "required_any_substrings_present", "values": []},
        {"type": "field_not_equal", "value": "low"},
        {"type": "source_metadata_equals_if_present", "value": "title"},
    ],
)
def test_invalid_checks_rejected(check):
    with pytest.raises(ValidationError):
        EvalCheck.model_validate(check)
