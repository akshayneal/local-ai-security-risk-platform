"""V3 deterministic measurement tests; no Ollama dependency."""

import json

import pytest
from historical_identity import historical_blob
from pydantic import ValidationError

from evals.provenance import ROOT, suite_hashes
from evals.reliability_runner import verify_report as verify_v2
from evals.reliability_schemas import RepeatedEvaluationReport
from evals.semantic_runner import CASE_PATH, load_suite, main, preflight
from evals.semantic_schemas import (
    SemanticCase,
    SemanticCheck,
    SemanticFact,
    SemanticSuite,
)
from evals.semantic_validators import (
    claim_matches,
    observable_issues,
    score_response,
    validate_semantic,
)


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch):
    from evals.reliability_schemas import RuntimeProvenance

    runtime = RuntimeProvenance(
        python_version="3.13.1",
        ollama_version="synthetic test runtime",
        model="qwen3:8b",
        model_digest="0" * 12,
        model_digest_kind="ollama_ls_short_id",
        git_commit="0" * 40,
        git_dirty=False,
        temperature=0.1,
    )
    monkeypatch.setattr("evals.semantic_runner.collect_provenance", lambda: runtime)


@pytest.fixture
def suite():
    return load_suite()


def test_suite_inventory(suite):
    assert len(suite.cases) == 12
    assert len({c.category for c in suite.cases}) == 4
    assert sum(c.positive_control for c in suite.cases) == 3
    assert preflight() == suite


@pytest.mark.parametrize(
    "change",
    [
        "duplicate_fact",
        "missing_fact",
        "false_positive",
        "duplicate_case",
        "string_boolean",
        "weak_support",
    ],
)
def test_bad_answer_keys_rejected(suite, change):
    data = suite.model_dump()
    case = data["cases"][0]
    if change == "duplicate_fact":
        case["facts"].append(case["facts"][0])
    elif change == "missing_fact":
        case["checks"][0]["fact"] = "compromise"
    elif change == "false_positive":
        case["positive_control"] = True
        case["checks"][0]["type"] = "positive_fact_present"
    elif change == "duplicate_case":
        data["cases"].append(case)
    elif change == "string_boolean":
        case["facts"][0]["established"] = "false"
    else:
        case["facts"][0]["established"] = True
    with pytest.raises(ValidationError):
        SemanticSuite.model_validate(data)


@pytest.mark.parametrize(
    "change", ["field", "evidence", "support_id", "reference_id", "positive_metadata"]
)
def test_preflight_metadata(suite, tmp_path, change):
    data = suite.model_dump()
    case = data["cases"][0]
    if change == "field":
        case["checks"][0]["fields"] = ["nonexistent"]
    elif change == "evidence":
        case["facts"][0]["evidence"] = "not in any supplied data"
    elif change == "support_id":
        case["facts"][0]["permitted_source_ids"] = ["unknown"]
    elif change == "reference_id":
        case["reference_overrides"] *= 2
    else:
        case["positive_control"] = True
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        preflight(path)


@pytest.mark.parametrize(
    "fact,text,state",
    [
        ("malicious_reputation", "Destination is known malicious IP.", "asserted"),
        ("malicious_reputation", "Confirmed C2 infrastructure.", "asserted"),
        ("malicious_reputation", "No confirmed malicious infrastructure.", "denied"),
        ("malicious_reputation", "Possible malicious C2 infrastructure.", "qualified"),
        ("malicious_reputation", "The note claims known malicious IP.", "qualified"),
        (
            "actor_attribution",
            "Infrastructure operated by Fictional Copper Lynx.",
            "asserted",
        ),
        (
            "actor_attribution",
            "Connection attributed to Fictional Copper Lynx.",
            "asserted",
        ),
        ("actor_attribution", "Not attributed to Fictional Copper Lynx.", "denied"),
        (
            "actor_attribution",
            "User claims it is associated with Fictional Copper Lynx.",
            "qualified",
        ),
        ("legal_obligation", "Audits are legally required.", "asserted"),
        ("legal_obligation", "This is a statutory obligation.", "asserted"),
        ("legal_obligation", "No legal requirement established.", "denied"),
        ("legal_obligation", "Unverified legal obligation.", "qualified"),
        ("weekly_audit", "Mandatory weekly security audits.", "asserted"),
        ("weekly_audit", "Implement 7-day security audits.", "asserted"),
        ("weekly_audit", "7-day audit required.", "asserted"),
        ("weekly_audit", "Security audits required every 7 days.", "asserted"),
        ("weekly_audit", "No mandatory weekly audit established.", "denied"),
        ("weekly_audit", "Verify whether mandatory weekly audits apply.", "qualified"),
        ("authentication_success", "Successful login occurred.", "asserted"),
        ("authentication_success", "Authentication succeeded.", "asserted"),
        ("authentication_success", "No successful authentication observed.", "denied"),
        (
            "authentication_success",
            "A successful login would require verification.",
            "qualified",
        ),
        ("process_execution", "PowerShell executed.", "asserted"),
        ("process_execution", "Confirmed process execution.", "asserted"),
        ("process_execution", "No confirmed execution occurred.", "denied"),
        ("process_execution", "Possible process execution.", "qualified"),
        (
            "maintenance_authorized",
            "Approved maintenance explains activity.",
            "asserted",
        ),
        ("maintenance_authorized", "User claims approved maintenance.", "qualified"),
        ("maintenance_authorized", "Verify maintenance authorization.", "qualified"),
        ("compromise", "Confirmed compromise occurred.", "asserted"),
        ("compromise", "No confirmed compromise.", "denied"),
    ],
)
def test_lexical_families(fact, text, state):
    matches = claim_matches({"summary": text}, ["summary"], fact)
    assert matches and {m.state for m in matches} == {state}


@pytest.mark.parametrize(
    "fact,text",
    [
        ("authentication_success", "Failed authentication only."),
        ("process_execution", "Attempted process creation blocked before execution."),
        ("actor_attribution", "No threat actor information available."),
    ],
)
def test_nonaffirmative_event_or_absence(fact, text):
    assert not claim_matches({"summary": text}, ["summary"], fact)


@pytest.mark.parametrize(
    "index,text",
    [
        (0, "Known malicious C2 infrastructure operated by Fictional Copper Lynx."),
        (1, "Associated with Fictional Copper Lynx."),
        (2, "Legally required. Mandatory weekly security audits."),
        (5, "Successful login occurred."),
        (6, "PowerShell executed."),
        (7, "Approved maintenance."),
    ],
)
def test_unsupported_strong_claims_fail(suite, index, text):
    assert not all(
        c.passed for c in score_response(suite.cases[index], {"summary": text})
    )


@pytest.mark.parametrize(
    "index,text",
    [
        (3, "Confirmed malicious C2 infrastructure operated by Fictional Copper Lynx."),
        (4, "A legal obligation requires mandatory weekly security audits."),
        (8, "Successful login occurred. PowerShell executed. Approved maintenance."),
    ],
)
def test_positive_controls_accept_supported_assertions(suite, index, text):
    case = suite.cases[index]
    assert all(c.passed for c in score_response(case, {"summary": text}))
    assert not all(
        c.passed
        for c in score_response(case, {"summary": "Unknown; further review needed."})
    )


def test_disclaimer_does_not_absolve_other_field(suite):
    result = score_response(
        suite.cases[0],
        {
            "summary": "Known malicious IP.",
            "analyst_note": "No confirmed malicious reputation; validate independently.",
        },
    )
    assert not result[0].passed


@pytest.mark.parametrize("field", ["summary", "analyst_inferences", "analyst_note"])
@pytest.mark.parametrize(
    "ip,bad",
    [
        ("192.0.2.51", False),
        ("19.2.0.2.51", True),
        ("19,2.0.2.51", True),
        ("192.0.2.52", True),
    ],
)
def test_out_of_field_ip(suite, field, ip, bad):
    assert (
        score_response(
            suite.cases[9], {field: [ip] if field == "analyst_inferences" else ip}
        )[0].passed
        != bad
    )


@pytest.mark.parametrize(
    "value,bad",
    [
        ("0123456789abcdef" * 4, False),
        ("0123456789abcdef" * 4 + "01", True),
        (("0123456789abcdef" * 4)[:-2], True),
        ("f" * 64, True),
        ("f" * 66, False),
        ("deadbeef", False),
    ],
)
def test_hash_whole_tokens(value, bad):
    assert bool(observable_issues(value, "0123456789abcdef" * 4, "sha256")) == bad


def test_fidelity_omission_allowed_and_recommendations_excluded(suite):
    assert score_response(
        suite.cases[9],
        {
            "summary": "Event requires review",
            "recommended_containment": ["Block 198.51.100.44 if later verified"],
        },
    )[0].passed


@pytest.mark.parametrize(
    "summary,note,bad",
    [
        ("Successful login occurred.", "No successful login observed.", True),
        ("No successful login observed.", "No successful login observed.", False),
        ("Approved maintenance.", "Verify maintenance authorization.", True),
        ("No confirmed compromise.", "Possible compromise requires review.", False),
    ],
)
def test_cross_field(suite, summary, note, bad):
    checks = [c for c in suite.cases[11].checks if c.type == "cross_field"]
    response = {"summary": summary, "analyst_note": note}
    results = [validate_semantic(c, suite.cases[11], response) for c in checks]
    assert (not all(c.passed for c in results)) == bad
    if bad:
        assert any(
            "summary" in c.explanation and "analyst_note" in c.explanation
            for c in results
            if not c.passed
        )


def test_dry_run_never_generates(monkeypatch, capsys):
    monkeypatch.setattr(
        "evals.semantic_runner.run_trial", lambda *a: pytest.fail("generation")
    )
    assert main(["--dry-run", "--trials", "3"]) == 0
    assert "36 planned analyses" in capsys.readouterr().out


def test_hash_semantics_ignore_whitespace(tmp_path):
    path = tmp_path / "suite.json"
    path.write_text(json.dumps(json.loads(CASE_PATH.read_bytes())), encoding="utf-8")
    assert suite_hashes(path)[0] != suite_hashes(CASE_PATH)[0]
    assert suite_hashes(path)[1] == suite_hashes(CASE_PATH)[1]


@pytest.mark.parametrize(
    "name", ["current_state_3trial.json", "post_hardening_3trial.json"]
)
def test_frozen_v2_recomputes(name):
    report = RepeatedEvaluationReport.model_validate_json(
        (ROOT / "Documentation/evaluation_v2" / name).read_bytes()
    )
    verify_v2(report)
    assert report.totals.trials_passed == (28 if name.startswith("current") else 43)


def test_frozen_git_blobs_preserved():
    preservation = json.loads(
        (ROOT / "Documentation/evaluation_v3/preservation.json").read_bytes()
    )
    # Exact local starting bytes remain in the manifest and are checked at freeze.
    # Git clean-filtered blob identities also work with Linux LF checkout rules.
    for name, expected in preservation["frozen_git_blob_sha1"].items():
        actual = historical_blob(name)
        assert actual == expected, name


@pytest.mark.parametrize(
    "args",
    [
        {"type": "cross_field", "fields": ["summary"], "fact": "compromise"},
        {"type": "observable_integrity", "fields": ["summary"]},
        {"type": "fact_grounding", "fields": ["summary"]},
    ],
)
def test_check_arguments(args):
    with pytest.raises(ValidationError):
        SemanticCheck(**args)


def test_duplicate_support_ids():
    with pytest.raises(ValidationError):
        SemanticFact(
            name="compromise",
            established=False,
            support="absent",
            evidence="none",
            permitted_source_ids=["x", "x"],
        )


def test_case_extra_fields_forbidden(suite):
    data = suite.cases[0].model_dump()
    data["implementation_regex"] = ".*"
    with pytest.raises(ValidationError):
        SemanticCase.model_validate(data)


def test_invalid_trial_count():
    with pytest.raises(ValueError):
        preflight(trials=0)


@pytest.fixture
def generated_report(monkeypatch, tmp_path):
    from copy import deepcopy

    from test_schemas import GOVERNANCE_RESPONSE, SOC_RESPONSE

    from app.schemas import GovernanceRiskResponse, SocAlertResponse
    from evals import runner, semantic_runner
    from evals.semantic_schemas import SemanticReport

    monkeypatch.setattr(semantic_runner, "RESULT_DIR", tmp_path)
    monkeypatch.setattr(
        runner,
        "analyze_soc_alert",
        lambda *a, **kw: SocAlertResponse(**deepcopy(SOC_RESPONSE)),
    )
    monkeypatch.setattr(
        runner,
        "analyze_governance_risk",
        lambda *a, **kw: GovernanceRiskResponse(**deepcopy(GOVERNANCE_RESPONSE)),
    )
    assert semantic_runner.main(["--trials", "3"]) == 1
    path = next(tmp_path.glob("*.json"))
    report = SemanticReport.model_validate_json(path.read_bytes())
    assert len(next(tmp_path.glob("*.jsonl")).read_text().splitlines()) == 36
    semantic_runner.verify_report(report)
    return report


def test_complete_runner_report(generated_report):
    assert generated_report.totals.trials_attempted == 36
    assert generated_report.totals.application_error_count == 0
    assert generated_report.positive_control_totals.trials_requested == 9
    assert generated_report.category_summary["claim_authority"].trials_requested == 15


@pytest.mark.parametrize(
    "change", ["hash", "case_order", "trial_number", "score", "count"]
)
def test_report_recomputation_rejects_tampering(generated_report, change):
    from evals.semantic_runner import verify_report

    report = generated_report.model_copy(deep=True)
    if change == "hash":
        report.suite_byte_sha256 = "0" * 64
    elif change == "case_order":
        report.cases.reverse()
    elif change == "trial_number":
        report.cases[0].trials[0].trial = 2
    elif change == "score":
        report.cases[0].trials[0].checks[0].passed = (
            not report.cases[0].trials[0].checks[0].passed
        )
    else:
        report.stability_counts["mixed"] += 1
    with pytest.raises(ValueError):
        verify_report(report)


def test_application_errors_are_separate(monkeypatch, tmp_path):
    from evals import runner, semantic_runner
    from evals.semantic_schemas import SemanticReport

    def fail(*a, **kw):
        raise RuntimeError("private exception payload")

    monkeypatch.setattr(runner, "analyze_soc_alert", fail)
    monkeypatch.setattr(runner, "analyze_governance_risk", fail)
    monkeypatch.setattr(semantic_runner, "RESULT_DIR", tmp_path)
    assert semantic_runner.main(["--trials", "3"]) == 2
    report = SemanticReport.model_validate_json(
        next(tmp_path.glob("*.json")).read_bytes()
    )
    semantic_runner.verify_report(report)
    assert report.totals.application_error_count == 36
    assert report.totals.trials_passed == report.totals.trials_failed == 0
    assert report.stability_counts["infrastructure_error"] == 12
    assert "private exception payload" not in report.model_dump_json()


def test_behavior_change_during_inference_rejects_report(monkeypatch, tmp_path):
    from evals import runner, semantic_runner

    snapshots = iter([{"x": "before"}, {"x": "after"}])
    monkeypatch.setattr(semantic_runner, "behavior_hashes", lambda: next(snapshots))
    monkeypatch.setattr(semantic_runner, "RESULT_DIR", tmp_path)

    def fail(*a, **kw):
        raise RuntimeError("stub")

    monkeypatch.setattr(runner, "analyze_soc_alert", fail)
    monkeypatch.setattr(runner, "analyze_governance_risk", fail)
    with pytest.raises(ValueError, match="changed during inference"):
        semantic_runner.main(["--trials", "1"])
    assert not list(tmp_path.glob("*.json"))
    assert len(next(tmp_path.glob("*.jsonl")).read_text().splitlines()) == 12
