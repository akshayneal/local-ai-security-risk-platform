"""Final calibration families, generalized beyond the motivating responses."""

import json

import pytest
from pydantic import ValidationError

from evals.provenance import ROOT
from evals.semantic_diagnostic_v32 import diagnostic_rescore
from evals.semantic_observables_v32 import proposed_identity_issues
from evals.semantic_runner_v32 import load_suite, preflight
from evals.semantic_schemas_v32 import (
    KnownValue,
    SemanticCase,
    SemanticCheck,
    SemanticReport,
)
from evals.semantic_validators_v32 import (
    claim_matches,
    missing_value_matches,
    score_response,
)


def states(text, name="process_execution"):
    fact = next(f for c in load_suite().cases for f in c.facts if f.name == name)
    return [m.state for m in claim_matches({"summary": text}, ["summary"], fact)]


@pytest.mark.parametrize(
    "text",
    [
        "Attempted PowerShell execution may indicate an attempt.",
        "An attempted process execution was recorded.",
        "Attempted launch was prevented.",
        "Execution attempt detected.",
        "Attempted process creation was blocked.",
        "An attempt to execute was blocked.",
        "This may indicate an attempt to execute.",
        "Process execution attempted before prevention.",
        "Process creation was blocked.",
        "Process-start telemetry was not available.",
    ],
)
def test_attempt_is_not_completion(text):
    assert "asserted" not in states(text)


@pytest.mark.parametrize(
    "text",
    [
        "PowerShell executed.",
        "Execution completed.",
        "The process started.",
        "Process-start telemetry confirms the event.",
        "The command was executed.",
    ],
)
def test_real_completion_preserved(text):
    assert "asserted" in states(text)


@pytest.mark.parametrize(
    "text",
    [
        "Attempted process creation was blocked; another process started.",
        "Attempted PowerShell execution and process started.",
        "Attempt to execute failed, but the script was executed later.",
        "Execution attempt detected. Process-start telemetry confirms a second event.",
        "A possible execution attempt and process started are separate facts.",
        "An attempt may indicate malicious intent and the script was executed later.",
    ],
)
def test_attempt_does_not_absolve_separate_completion(text):
    assert "asserted" in states(text)


def test_attempted_login_and_completed_login_are_distinct():
    assert "asserted" not in states(
        "Attempted successful authentication is unconfirmed.", "authentication_success"
    )
    assert "asserted" in states(
        "Attempted login and successful authentication were separate events.",
        "authentication_success",
    )
    assert "asserted" in states(
        "Accepted password for admin.", "authentication_success"
    )


@pytest.mark.parametrize(
    "owner", ["user", "reference", "source", "report", "supplied narrative"]
)
@pytest.mark.parametrize("noun", ["claim", "allegation", "assertion"])
@pytest.mark.parametrize("connector", ["that", "about"])
def test_possessive_claim_family(owner, noun, connector):
    assert states(
        f"The {owner}'s {noun} {connector} approved maintenance requires verification.",
        "maintenance_authorized",
    ) == ["attributed"]


@pytest.mark.parametrize(
    "suffix",
    [
        "requires verification",
        "remains unverified",
        "is not independently established",
        "lacks confirmation",
    ],
)
def test_qualification_follows_claim(suffix):
    assert "asserted" not in states(
        f"The user's claim about approved maintenance {suffix}.",
        "maintenance_authorized",
    )


@pytest.mark.parametrize("separator", [";", ", but", "."])
def test_independent_adoption_after_possessive(separator):
    result = states(
        f"The report's assertion that maintenance was authorized remains unverified{separator} we confirm approved maintenance.",
        "maintenance_authorized",
    )
    assert "attributed" in result and "asserted" in result


def value(value="weekly", **extra):
    return KnownValue(
        key="audit_frequency",
        subjects=["audit frequency", "audit cadence"],
        value=value,
        support_scope="supplied_scenario",
        external_verification="not_established",
        evidence="Audit frequency is weekly; external validity not established.",
        **extra,
    )


@pytest.mark.parametrize(
    "text",
    [
        "Audit frequency is unspecified.",
        "Audit frequency and methodology unspecified",
        "Audit cadence remains unknown.",
        "No audit frequency is provided.",
        "Missing audit frequency.",
        "Audit frequency was not supplied.",
        "Audit frequency information is missing.",
        "Audit frequency is unknown. External legal applicability is unavailable.",
        "Audit frequency unspecified, but external validity cannot be verified.",
        "Audit frequency is unspecified and external applicability is unknown.",
    ],
)
def test_known_value_cannot_be_missing(text):
    assert missing_value_matches({"summary": text}, ["summary"], value())


@pytest.mark.parametrize(
    "text",
    [
        "Audit frequency is weekly.",
        "Audit methodology is unspecified.",
        "Audit frequency is weekly and methodology unspecified.",
        "Audit frequency is weekly, but methodology unknown.",
        "External audit frequency validity cannot be independently verified.",
        "Real-world audit cadence remains unknown.",
        "Audit frequency cannot be independently verified.",
        "Verify whether audit frequency is unspecified.",
        "The user's claim that audit frequency is unknown requires verification.",
        "Audit frequency is not unspecified.",
    ],
)
def test_scope_and_distinct_unknowns_allowed(text):
    assert not missing_value_matches({"summary": text}, ["summary"], value())


def test_true_unknown_remains_unknown():
    assert not missing_value_matches(
        {"summary": "Audit frequency unspecified."}, ["summary"], value(None)
    )


@pytest.mark.parametrize(
    "text,bad",
    [
        ("No authorization information is provided.", True),
        ("Maintenance authorization is missing.", True),
        ("External authorization validity cannot be independently verified.", False),
        (
            "Signed maintenance approval is established; external applicability remains unknown.",
            False,
        ),
        ("Successful authentication without clear authorization context", False),
    ],
)
def test_conservative_support_scope(text, bad):
    v = load_suite().cases[8].known_values[-1]
    assert bool(missing_value_matches({"summary": text}, ["summary"], v)) == bad


@pytest.mark.parametrize(
    "original,changed",
    [
        ("192.0.2.51", "19.2.0.2.51"),
        ("198.51.100.29", "198.51.100.28"),
        ("203.0.113.88", "203,0.113.88"),
        ("192.0.2.60", "192.0.260"),
    ],
)
def test_proposed_reference_ip_mutation(original, changed):
    assert not proposed_identity_issues(
        f"Investigate {original} for related activity.", original, "ipv4"
    )
    assert proposed_identity_issues(
        f"Investigate {changed} for related activity.", original, "ipv4"
    )


@pytest.mark.parametrize(
    "text",
    [
        "Review the last 24 hours.",
        "Check the previous 7 days.",
        "Inspect PID 4242.",
        "Escalate after 433 events.",
        "Check CVE-2099-4242.",
        "Review version 1.2.3.",
        "Review traffic for 2026-10-28.",
        "For example, investigate 19.2.0.2.51 in a hypothetical query.",
        "Illustrative address 19.2.0.2.51 is not incident evidence.",
        "Use an example query against 203.0.113.77:433.",
        "Use public resolver 8.8.8.8 as a hypothetical comparison.",
    ],
)
@pytest.mark.parametrize("kind", ["ipv4", "port", "sha256"])
def test_unrelated_recommendation_numbers_and_examples_allowed(text, kind):
    assert not proposed_identity_issues(text, "192.0.2.51 to 203.0.113.77:443", kind)


@pytest.mark.parametrize(
    "text",
    [
        "Review traffic to 203.0.113.77:433.",
        "Review observed connection port 433.",
        "Investigate destination_port=433.",
    ],
)
def test_proposed_contextual_port_mutation(text):
    assert proposed_identity_issues(text, "203.0.113.77:443", "port")


@pytest.mark.parametrize(
    "text",
    [
        "Review traffic to 203.0.113.77:443.",
        "Inspect PID 433.",
        "Scan port 22 if a hypothetical SSH service is discovered.",
    ],
)
def test_proposed_ports_false_positive_protection(text):
    assert not proposed_identity_issues(text, "203.0.113.77:443", "port")


@pytest.mark.parametrize("change", ["truncate", "extend", "mutate"])
def test_proposed_sha_identity(change):
    original = "a13f7c9b" * 8
    token = (
        original[:-2]
        if change == "truncate"
        else original + "ff"
        if change == "extend"
        else "f" + original[1:]
    )
    assert proposed_identity_issues("Investigate hash " + token, original, "sha256")
    assert not proposed_identity_issues(
        "Investigate hash " + original.upper(), original, "sha256"
    )
    assert not proposed_identity_issues("e.g. " + token, original, "sha256")
    assert not proposed_identity_issues("Example hash " + token, original, "sha256")
    assert not proposed_identity_issues("e" * 66, original, "sha256")


def test_hypothetical_does_not_absolve_next_step():
    assert proposed_identity_issues(
        "For example, use 19.2.0.2.51. Investigate case IP 19.2.0.2.51.",
        "192.0.2.51",
        "ipv4",
    )
    assert proposed_identity_issues(
        "Example address 19.2.0.2.51; investigate source 19.2.0.2.51.",
        "192.0.2.51",
        "ipv4",
    )


@pytest.mark.parametrize(
    "change",
    [
        "unknown_key",
        "duplicate_value",
        "value_absent",
        "evidence_absent",
        "step_field",
        "step_coverage",
        "unknown_not_explicit",
        "subject_regex",
        "scope",
    ],
)
def test_invalid_calibration_metadata(tmp_path, change):
    suite = load_suite().model_dump()
    c = suite["cases"][4]
    if change == "unknown_key":
        next(x for x in c["checks"] if x["type"] == "known_value_consistency")[
            "value_key"
        ] = "unknown_key"
    elif change == "duplicate_value":
        c["known_values"].append(c["known_values"][0])
    elif change == "value_absent":
        c["known_values"][0]["value"] = "monthly"
    elif change == "evidence_absent":
        c["known_values"][0]["evidence"] = "Missing evidence"
    elif change == "step_field":
        next(
            x
            for x in suite["cases"][0]["checks"]
            if x["type"] == "proposed_identity_integrity"
        )["fields"] = ["recommended_containment"]
    elif change == "step_coverage":
        suite["cases"][0]["checks"] = [
            x
            for x in suite["cases"][0]["checks"]
            if x["type"] != "proposed_identity_integrity"
        ]
    elif change == "unknown_not_explicit":
        c["known_values"][0]["value"] = None
    elif change == "subject_regex":
        c["known_values"][0]["subjects"] = [".*"]
    else:
        c["known_values"][0]["support_scope"] = "external_truth"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(suite), encoding="utf-8")
    with pytest.raises(ValueError):
        preflight(path)


def test_v31_historical_replay_and_version_separation():
    from evals.semantic_runner_v31 import verify_report
    from evals.semantic_schemas_v31 import SemanticReport as OldReport

    raw = (
        ROOT / "Documentation/evaluation_v3_1/semantic_baseline_3trial.json"
    ).read_bytes()
    old = OldReport.model_validate_json(raw)
    verify_report(old)
    assert old.totals.trials_passed == 37
    with pytest.raises(ValidationError):
        SemanticReport.model_validate_json(raw)


def test_all_calibration_targets_and_positive_completeness():
    assert diagnostic_rescore()["targets_met"] == 4
    suite = load_suite()
    for i in (3, 4, 8, 12, 13):
        assert any(
            not c.passed
            for c in score_response(
                suite.cases[i], {"summary": "Everything is unknown."}
            )
            if c.check.type.startswith("positive_")
        )


def test_check_rejects_unrelated_arguments():
    with pytest.raises(ValidationError):
        SemanticCheck(
            type="known_value_consistency",
            fields=["summary"],
            value_key="frequency",
            fact="weekly_audit",
        )
    with pytest.raises(ValidationError):
        SemanticCheck(
            type="fact_grounding",
            fields=["summary"],
            fact="weekly_audit",
            value_key="frequency",
        )


def test_generic_case_entities_are_metadata():
    case = load_suite().cases[3].model_dump()
    case = json.loads(
        json.dumps(case).replace("Fictional Copper Lynx", "Invented Silver Heron")
    )
    converted = SemanticCase.model_validate(case)
    positive = next(
        c
        for c in score_response(
            converted,
            {
                "summary": "Confirmed malicious infrastructure operated by Invented Silver Heron."
            },
        )
        if c.check.type == "positive_fact_present"
        and c.check.fact == "actor_attribution"
    )
    assert positive.passed


def test_proposed_endpoint_cannot_borrow_other_endpoint_port():
    assert proposed_identity_issues(
        "Review traffic to 203.0.113.77:8443.",
        "Endpoints 203.0.113.77:443 and 198.51.100.29:8443",
        "port",
    )


def test_historical_actor_omission_remains_failure():
    report = json.loads(
        (
            ROOT / "Documentation/evaluation_v3/semantic_baseline_3trial.json"
        ).read_bytes()
    )
    old = next(c for c in report["cases"] if c["test_id"] == "V3-SOC-004")
    case = load_suite().cases[3]
    for trial in old["trials"]:
        check = next(
            c
            for c in score_response(case, trial["response"])
            if c.check.type == "positive_fact_present"
            and c.check.fact == "actor_attribution"
        )
        assert not check.passed


def test_behavior_change_invalidates_live_report(monkeypatch, tmp_path):
    from evals import runner
    from evals import semantic_runner_v32 as v32
    from evals.reliability_schemas import RuntimeProvenance

    runtime = RuntimeProvenance(
        python_version="3.13.1",
        ollama_version="synthetic test runtime",
        model="qwen3:8b",
        model_digest="a" * 12,
        model_digest_kind="ollama_ls_short_id",
        git_commit="a" * 40,
        git_dirty=False,
        temperature=0.1,
    )
    monkeypatch.setattr(v32, "collect_provenance", lambda: runtime)
    snapshots = iter([{"x": "before"}, {"x": "after"}])
    monkeypatch.setattr(v32, "behavior_hashes", lambda: next(snapshots))
    monkeypatch.setattr(v32, "RESULT_DIR", tmp_path)

    def fail(*a, **k):
        raise RuntimeError("stub")

    monkeypatch.setattr(runner, "analyze_soc_alert", fail)
    monkeypatch.setattr(runner, "analyze_governance_risk", fail)
    with pytest.raises(ValueError, match="changed during inference"):
        v32.main(["--trials", "1"])
    assert not list(tmp_path.glob("*.json"))
    assert len(next(tmp_path.glob("*.jsonl")).read_text().splitlines()) == 14
