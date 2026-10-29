import json
from copy import deepcopy

import pytest
from test_schemas import GOVERNANCE_RESPONSE, SOC_RESPONSE

from evals.microsoft_reliability import runner
from evals.microsoft_reliability.cases import load_cases


def test_complete_frozen_cases_and_plan():
    cases = load_cases()
    plan = json.loads((runner.SUITE / "plan.json").read_bytes())
    assert len(cases) == len({c["case_id"] for c in cases}) == 24
    assert sum(c["trials"] for c in cases) == plan["baseline_attempts"] == 32
    assert runner.identity() == json.loads((runner.SUITE / "freeze.json").read_bytes())
    for case in cases:
        runner.request_for(case)
        assert all(
            case[k]
            for k in (
                "supported",
                "unsupported",
                "unknowns",
                "alternatives",
                "contracts",
            )
        )


def test_review_proxy_positive_negative_and_documented_limits():
    case = load_cases()[0]
    assert runner.checks(
        case, {**SOC_RESPONSE, "summary": "Shadowcopy deletion command recorded"}, set()
    )["coverage_groups"] == [True]
    assert runner.checks(case, SOC_RESPONSE, set())["coverage_groups"] == [False]
    # Known lexical false positive: a negation still matches. Never a semantic pass.
    assert runner.checks(
        case, {**SOC_RESPONSE, "summary": "No shadowcopy deletion"}, set()
    )["coverage_groups"] == [True]
    # Known lexical false negative: meaningful paraphrase needs manual review.
    assert runner.checks(
        case,
        {**SOC_RESPONSE, "summary": "Recovery snapshots were requested for removal"},
        set(),
    )["coverage_groups"] == [False]


def test_source_identifier_endpoint_controls():
    case = load_cases()[5]
    good = {
        **SOC_RESPONSE,
        "summary": "Remote 203.0.113.91:8443; local 192.0.2.25:51234",
    }
    assert runner.checks(case, good, set())["recognized_endpoint_membership"]
    bad = {**good, "summary": "Remote 203.0.113.91:51234"}
    assert not runner.checks(case, bad, set())["recognized_endpoint_membership"]
    assert not runner.checks(case, {**good, "summary": "203.0.113.201:8443"}, set())[
        "identifier_membership"
    ]
    assert not runner.checks(
        case, {**good, "source_references": [{"source_id": "untrusted"}]}, set()
    )["source_membership"]


def test_trial_without_runtime_or_model_access(monkeypatch):
    monkeypatch.setattr(runner, "runtime_snapshot", dict)
    from app.schemas import GovernanceRiskResponse

    monkeypatch.setattr(
        runner,
        "analyze_governance_risk",
        lambda *a, **kw: GovernanceRiskResponse(**GOVERNANCE_RESPONSE),
    )
    case = load_cases()[14]
    first = runner.trial(case, 1)
    assert first["result"] and first["retry_count"] == 0

    def fail(*a, **kw):
        kw["trace"].repair_attempted = True
        raise ValueError("private telemetry")

    monkeypatch.setattr(runner, "analyze_governance_risk", fail)
    second = runner.trial(case, 2)
    assert second["error"] == "analysis_failed"
    assert "private" not in json.dumps(second)
    metrics = runner.aggregate([first, second])
    assert metrics["attempts"] == 2 and metrics["returned"] == 1
    assert metrics["repair_attempted"] == 1 and metrics["repair_succeeded"] == 0
    assert metrics["per_case"][case["case_id"]] == ["returned", "withheld"]
    report = {
        "identity": runner.identity(),
        "runtime": {"git_commit": "a", "model_digest": "same"},
        "records": [first, second],
    }
    assert runner.compare(report, report)["baseline"]["returned"] == 1
    altered = deepcopy(report)
    altered["records"][0]["request_sha256"] = "changed"
    with pytest.raises(ValueError, match="schedule"):
        runner.compare(report, altered)
    altered = deepcopy(report)
    altered["identity"]["version"] = "changed"
    with pytest.raises(ValueError, match="frozen"):
        runner.compare(report, altered)
