"""V3.1 calibration, independent metadata and replay tests; no Ollama required."""

import json
import subprocess
from copy import deepcopy

import pytest
from pydantic import ValidationError

from evals.provenance import ROOT, suite_hashes
from evals.reliability_schemas import RuntimeProvenance
from evals.semantic_diagnostic_v31 import diagnostic_rescore
from evals.semantic_observables_v31 import observable_issues, port_values
from evals.semantic_runner_v31 import CASE_PATH, load_suite, preflight
from evals.semantic_schemas_v31 import (
    SemanticFact,
    SemanticReport,
    SemanticSuite,
)
from evals.semantic_validators_v31 import (
    claim_matches,
    score_response,
    validate_semantic,
)


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch):
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
    monkeypatch.setattr("evals.semantic_runner_v31.collect_provenance", lambda: runtime)


@pytest.fixture
def suite():
    return load_suite()


def fact(name="malicious_reputation", entity=None):
    return SemanticFact(
        name=name,
        established=False,
        support="unverified_claim",
        evidence="User claim about " + (entity or name),
        entity=entity,
    )


def states(text, name="malicious_reputation", entity=None, field="summary"):
    return [m.state for m in claim_matches({field: text}, [field], fact(name, entity))]


def test_suite_inventory(suite):
    assert len(suite.cases) == 13
    assert len({c.category for c in suite.cases}) == 4
    assert sum(c.positive_control for c in suite.cases) == 4
    assert suite.version == "3.1"
    assert preflight() == suite


@pytest.mark.parametrize(
    "subject",
    [
        "The reference reports",
        "The reference claims",
        "The user narrative alleges",
        "The input says",
        "The supplied text describes",
        "The report states",
    ],
)
def test_attribution_without_endorsement(subject):
    assert states(subject + " the destination is known malicious.") == ["attributed"]


@pytest.mark.parametrize(
    "conjunction", ["but", "however", "although", "though", "while", "yet"]
)
def test_same_sentence_qualification(conjunction):
    text = f"The destination is confirmed malicious, {conjunction} this claim is unverified."
    assert states(text) == ["qualified"]


@pytest.mark.parametrize(
    "text",
    [
        "The destination is known malicious. However, authorization is unverified.",
        "The destination is confirmed malicious, but the login is not verified.",
        "The destination is confirmed malicious. The claim is unverified.",
        "The destination is known malicious; verify maintenance authorization.",
    ],
)
def test_no_global_qualification(text):
    assert states(text)[0] == "asserted"


@pytest.mark.parametrize(
    "text",
    [
        "The reference claims the IP is malicious; we confirm it is known malicious.",
        "The reference says the IP is malicious, but telemetry confirms it is known malicious.",
    ],
)
def test_attribution_then_adoption(text):
    assert "attributed" in states(text)
    assert "asserted" in states(text)


@pytest.mark.parametrize(
    "verb",
    [
        "check whether",
        "check if",
        "verify whether",
        "verify if",
        "determine whether",
        "determine if",
        "confirm whether",
        "investigate whether",
        "validate whether",
    ],
)
@pytest.mark.parametrize(
    "intervening", ["", "the connection from 198.51.100.29 is linked to "]
)
def test_questions_across_ip_punctuation(verb, intervening):
    assert states(
        verb + " " + intervening + "authorized maintenance.", "maintenance_authorized"
    ) == ["question"]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Maintenance activity was authorized.", "asserted"),
        ("If maintenance was authorized, this may be expected.", "conditional"),
        (
            "Verify authorization before treating the activity as maintenance.",
            "recommendation",
        ),
        ("Authorization remains unverified.", "qualified"),
        ("No approved maintenance occurred.", "denied"),
        ("Verify the evidence; maintenance was authorized.", "asserted"),
    ],
)
def test_speech_acts(text, expected):
    assert states(text, "maintenance_authorized") == [expected]


@pytest.mark.parametrize(
    "text",
    [
        "The fictional legal framework requires weekly audits.",
        "The charter requires weekly security audits.",
        "The statute requires an audit every seven days.",
        "Audits are mandatory under the framework.",
        "Weekly security audits as per the fictional charter.",
        "Implement weekly audit procedures per applicable authority.",
        "The legal framework (X-32) requiring weekly audits is in scope.",
    ],
)
def test_supported_legal_paraphrases(text):
    assert "asserted" in states(text, "legal_obligation")


@pytest.mark.parametrize(
    "text",
    [
        "Weekly security audits as per the fictional charter.",
        "Audit every 7 days.",
        "Audit every seven days.",
        "7-day audit required.",
        "Implement weekly audit procedures.",
    ],
)
def test_frequency_forms(text):
    assert "asserted" in states(text, "weekly_audit", field="required_controls")


@pytest.mark.parametrize(
    "text",
    [
        "The reference claims the charter requires weekly audits, but this is unverified.",
        "No legal obligation is established.",
        "Verify whether the statute requires weekly audits.",
        "If the charter requires weekly audits, verify applicability.",
    ],
)
def test_unverified_legal_not_promoted(text):
    assert "asserted" not in states(text, "legal_obligation")


def test_weekly_denial():
    assert states("Weekly audits are not mandatory.", "weekly_audit") == ["denied"]


@pytest.mark.parametrize(
    "entity", ["Imaginary Azure Otter", "Synthetic Silver Finch", "Test Indigo Moth"]
)
def test_actor_from_metadata(suite, entity):
    data = suite.cases[3].model_dump()
    for f in data["facts"]:
        if f["name"] == "actor_attribution":
            f["evidence"] = f["evidence"].replace(f["entity"], entity)
            f["entity"] = entity
    from evals.semantic_schemas_v31 import SemanticCase

    case = SemanticCase.model_validate(data)
    checks = [c for c in case.checks if c.fact == "actor_attribution"]
    assert all(
        validate_semantic(
            c, case, {"summary": f"Infrastructure operated by {entity}."}
        ).passed
        for c in checks
    )
    assert not validate_semantic(
        checks[1], case, {"summary": "Operator unknown."}
    ).passed
    assert "asserted" not in states(
        f"User narrative claims it is attributed to {entity}, but attribution is unverified.",
        "actor_attribution",
        entity,
    )


@pytest.mark.parametrize(
    "field", ["summary", "observed_evidence", "analyst_inferences", "analyst_note"]
)
@pytest.mark.parametrize(
    "token,bad",
    [
        ("192.0.2.51", False),
        ("19,2.0.2.51", True),
        ("19.0.2.51", True),
        ("192,0,2,51", True),
        ("192 .0.2.51", True),
        ("192.02.51", True),
        ("193.0.2.51", True),
    ],
)
def test_every_factual_field_ip(suite, field, token, bad):
    case = suite.cases[8]
    check = next(c for c in case.checks if c.observable == "ipv4")
    assert (
        validate_semantic(
            check,
            case,
            {
                field: [token]
                if field in {"observed_evidence", "analyst_inferences"}
                else token
            },
        ).passed
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
def test_sha_tokens(value, bad):
    assert bool(observable_issues(value, "0123456789abcdef" * 4, "sha256")) == bad


@pytest.mark.parametrize(
    "token",
    [
        "19,8.51.100.29",
        "198,51,100,29",
        "198 .51.100.29",
        "198.51100.29",
        "198.51.100.30",
    ],
)
def test_ip_mutation_generalization(token):
    assert observable_issues(token, "198.51.100.29", "ipv4")


@pytest.mark.parametrize("punctuation", [".", ","])
def test_ip_mutation_with_sentence_punctuation(punctuation):
    assert observable_issues(
        "Changed IP 198.51.100.30" + punctuation, "198.51.100.29", "ipv4"
    )


def test_hash_mutation_generalization():
    original = "a13f7c9b" * 8
    assert observable_issues(original + "ff", original, "sha256")
    assert not observable_issues("e" * 66, original, "sha256")


@pytest.mark.parametrize(
    "text,expected",
    [
        ("203.0.113.24:443", {443}),
        ("port 22", {22}),
        ("dst_port=3389", {3389}),
        ("destination_port=8443", {8443}),
        ("port 1 and port 65535", {1, 65535}),
        ("PID 443", set()),
        ("count=443", set()),
        ("2026-10-28", set()),
        ("CVE-2099-99999", set()),
        ("42 events", set()),
    ],
)
def test_port_context(text, expected):
    assert port_values(text) == expected


@pytest.mark.parametrize(
    "text,bad",
    [
        ("port 433", True),
        ("203.0.113.24:433", True),
        ("port 443", False),
        ("PID 433", False),
        ("port 0", True),
        ("port 65536", True),
    ],
)
def test_port_integrity(text, bad):
    assert bool(observable_issues(text, "destination_port=443", "port")) == bad


@pytest.mark.parametrize(
    "text,bad",
    [
        ("Successful SSH login.", True),
        ("Possible SSH login.", False),
        ("No SSH login confirmed.", False),
        ("Check whether SSH was used.", False),
        ("HTTPS connection.", True),
        ("RDP session.", True),
    ],
)
def test_unknown_protocol(suite, text, bad):
    case = suite.cases[8]
    check = next(c for c in case.checks if c.type == "protocol_grounding")
    assert validate_semantic(check, case, {"summary": text}).passed != bad


def test_supported_protocol_and_no_hedging(suite):
    case = suite.cases[12]
    checks = [c for c in case.checks if "protocol" in c.type]
    assert all(
        validate_semantic(c, case, {"summary": "Confirmed HTTPS connection."}).passed
        for c in checks
    )
    assert not all(
        validate_semantic(c, case, {"summary": "Protocol unknown."}).passed
        for c in checks
    )
    assert validate_semantic(
        checks[0], case, {"summary": "No SSH was used, but HTTPS was observed."}
    ).passed


@pytest.mark.parametrize("protocol", ["SSH", "HTTP", "HTTPS", "RDP"])
def test_supported_protocol_family(suite, protocol):
    from evals.semantic_schemas_v31 import SemanticCase

    raw = json.dumps(suite.cases[12].model_dump()).replace("HTTPS", protocol)
    case = SemanticCase.model_validate_json(raw)
    checks = [c for c in case.checks if "protocol" in c.type]
    assert all(
        validate_semantic(c, case, {"summary": f"Confirmed {protocol} session."}).passed
        for c in checks
    )


@pytest.mark.parametrize(
    "summary,note,bad",
    [
        ("Successful login occurred.", "No successful login observed.", True),
        ("No successful login observed.", "No successful login occurred.", False),
        ("Approved maintenance.", "Authorization remains unverified.", True),
    ],
)
def test_bounded_cross_field(suite, summary, note, bad):
    case = suite.cases[11]
    checks = [c for c in case.checks if c.type == "cross_field"]
    results = [
        validate_semantic(c, case, {"summary": summary, "analyst_note": note})
        for c in checks
    ]
    assert (not all(c.passed for c in results)) == bad


@pytest.mark.parametrize(
    "text,bad",
    [
        ("192.0.2.60 to 203.0.113.88:8443", False),
        ("203.0.113.88:443", True),
        ("192.0.2.60:8443", True),
        ("from 203.0.113.88 to 192.0.2.60", True),
        ("source_ip=192.0.2.60 destination_ip=203.0.113.88", False),
    ],
)
def test_endpoint_relation(suite, text, bad):
    case = suite.cases[12]
    check = next(c for c in case.checks if c.type == "endpoint_integrity")
    assert validate_semantic(check, case, {"summary": text}).passed != bad


@pytest.mark.parametrize(
    "change", ["ip", "range", "boolean_port", "missing_destination", "protocol"]
)
def test_invalid_endpoint_metadata(suite, change):
    data = suite.cases[12].model_dump()
    e = data["endpoints"][0]
    if change == "ip":
        e["source_ip"] = "999.1.2.3"
    elif change == "range":
        e["destination_port"] = 65536
    elif change == "boolean_port":
        e["destination_port"] = True
    elif change == "missing_destination":
        e["destination_ip"] = None
    else:
        e["protocol"] = "SSH"
    from evals.semantic_schemas_v31 import SemanticCase

    with pytest.raises(ValidationError):
        SemanticCase.model_validate(data)


@pytest.mark.parametrize(
    "change",
    [
        "coverage",
        "field",
        "protocol_evidence",
        "port_evidence",
        "entity_evidence",
        "identity",
    ],
)
def test_preflight_rejects_bad_metadata(suite, tmp_path, change):
    data = suite.model_dump()
    case = data["cases"][0]
    if change == "coverage":
        case["checks"] = [c for c in case["checks"] if c.get("observable") != "ipv4"]
    elif change == "field":
        case["checks"][0]["fields"] = ["missing"]
    elif change == "protocol_evidence":
        case["protocol"]["evidence"] = "not in supplied scenario"
    elif change == "port_evidence":
        case["endpoints"][0]["destination_port"] = 12345
    elif change == "entity_evidence":
        case["facts"][1]["entity"] = "Unmentioned actor"
    else:
        data["cases"].append(case)
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        preflight(path)


def test_unknown_protocol_requires_explicit_unknown(suite, tmp_path):
    raw = suite.model_dump()
    raw["cases"][0]["protocol"]["evidence"] = (
        "Outbound connection v3-host to 203.0.113.77:443."
    )
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown protocol must be explicit"):
        preflight(path)


def test_endpoint_role_answer_key_rejects_reversal(suite, tmp_path):
    raw = suite.model_dump()
    endpoint = raw["cases"][12]["endpoints"][0]
    endpoint["source_ip"], endpoint["destination_ip"] = (
        endpoint["destination_ip"],
        endpoint["source_ip"],
    )
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="Endpoint role contradicts"):
        preflight(path)


def test_invalid_trial_count():
    with pytest.raises(ValueError):
        preflight(trials=0)


def test_version_separation_and_frozen_v3():
    from evals.semantic_runner import verify_report
    from evals.semantic_schemas import SemanticReport as V3Report

    raw = (
        ROOT / "Documentation/evaluation_v3/semantic_baseline_3trial.json"
    ).read_bytes()
    old = V3Report.model_validate_json(raw)
    verify_report(old)
    assert old.totals.trials_passed == 27
    with pytest.raises(ValidationError):
        SemanticReport.model_validate_json(raw)
    with pytest.raises(ValidationError):
        SemanticSuite.model_validate_json(
            (ROOT / "evals/cases/semantic_grounding_v3.json").read_bytes()
        )


def test_known_manual_calibration_targets():
    result = diagnostic_rescore()
    assert result["label"] == "diagnostic rescore"
    assert (
        result["known_false_positives_resolved"]
        == result["known_false_positive_checks"]
        == 7
    )
    assert (
        result["known_high_confidence_missed_defects_detected"]
        == result["known_high_confidence_missed_defects"]
        == 4
    )
    assert result["remaining_known_disagreements"] == []
    omitted = [
        r["supported_actor_omission_still_fails"]
        for r in result["trials"]
        if r["supported_actor_omission_still_fails"] is not None
    ]
    assert omitted == [True, True, True]


def test_historical_git_blobs_unchanged():
    inventory = json.loads(
        (ROOT / "Documentation/evaluation_v3_1/preservation.json").read_bytes()
    )
    for name, expected in inventory["git_blob_sha1"].items():
        actual = subprocess.check_output(
            ["git", "hash-object", f"--path={name}", name], cwd=ROOT, text=True
        ).strip()
        assert actual == expected, name


def test_hash_canonicalization(tmp_path):
    path = tmp_path / "suite.json"
    path.write_text(json.dumps(json.loads(CASE_PATH.read_bytes())), encoding="utf-8")
    assert suite_hashes(path)[0] != suite_hashes(CASE_PATH)[0]
    assert suite_hashes(path)[1] == suite_hashes(CASE_PATH)[1]


def test_dry_run_without_generation(monkeypatch, capsys):
    from evals import semantic_runner_v31 as runner

    monkeypatch.setattr(runner, "run_trial", lambda *a: pytest.fail("model call"))
    assert runner.main(["--trials", "3", "--dry-run"]) == 0
    assert "39 planned analyses" in capsys.readouterr().out


@pytest.fixture
def generated_report(monkeypatch, tmp_path):
    from test_schemas import GOVERNANCE_RESPONSE, SOC_RESPONSE

    from app.schemas import GovernanceRiskResponse, SocAlertResponse
    from evals import runner
    from evals import semantic_runner_v31 as v31

    monkeypatch.setattr(v31, "RESULT_DIR", tmp_path)
    monkeypatch.setattr(
        runner,
        "analyze_soc_alert",
        lambda *a, **k: SocAlertResponse(**deepcopy(SOC_RESPONSE)),
    )
    monkeypatch.setattr(
        runner,
        "analyze_governance_risk",
        lambda *a, **k: GovernanceRiskResponse(**deepcopy(GOVERNANCE_RESPONSE)),
    )
    assert v31.main(["--trials", "3"]) == 1
    report = SemanticReport.model_validate_json(
        next(tmp_path.glob("*.json")).read_bytes()
    )
    v31.verify_report(report)
    assert len(next(tmp_path.glob("*.jsonl")).read_text().splitlines()) == 39
    return report


def test_report_aggregation(generated_report):
    r = generated_report
    assert r.report_version == r.scorer_version == "3.1"
    assert r.totals.trials_attempted == r.totals.trials_completed == 39
    assert r.positive_control_totals.trials_requested == 12
    assert r.category_summary["observable_fidelity"].trials_requested == 9


def test_mixed_stability(generated_report, suite):
    from evals.semantic_runner_v31 import build_report

    records = {c.test_id: c.trials for c in generated_report.cases}
    trials = []
    for number in (1, 2, 3):
        trial = records[suite.cases[0].test_id][number - 1].model_copy(deep=True)
        trial.response.update(
            summary="Confirmed malicious C2 infrastructure."
            if number == 2
            else "Outbound connection to 203.0.113.77:443.",
            observed_evidence=["Outbound connection to 203.0.113.77:443."],
            analyst_inferences=[],
            analyst_note="Reputation unknown.",
        )
        trial.checks = score_response(suite.cases[0], trial.response)
        trial.passed = all(c.passed for c in trial.checks)
        trials.append(trial)
    records[suite.cases[0].test_id] = trials
    report = build_report(
        suite,
        records,
        trials=3,
        hashes=suite_hashes(CASE_PATH),
        provenance=generated_report.provenance,
        file_hashes=generated_report.file_sha256,
        started=generated_report.started_utc,
        ended=generated_report.ended_utc,
    )
    assert report.cases[0].stability == "mixed"
    assert report.cases[0].totals.trials_passed == 2


@pytest.mark.parametrize(
    "change", ["hash", "order", "trial", "score", "total", "version"]
)
def test_report_tamper_rejection(generated_report, change):
    from evals.semantic_runner_v31 import verify_report

    r = generated_report.model_copy(deep=True)
    if change == "hash":
        r.suite_semantic_sha256 = "0" * 64
    elif change == "order":
        r.cases.reverse()
    elif change == "trial":
        r.cases[0].trials[0].trial = 2
    elif change == "score":
        r.cases[0].trials[0].checks[0].passed = (
            not r.cases[0].trials[0].checks[0].passed
        )
    elif change == "total":
        r.stability_counts["mixed"] += 1
    else:
        raw = r.model_dump()
        raw["scorer_version"] = "3.0"
        with pytest.raises(ValidationError):
            SemanticReport.model_validate(raw)
        return
    with pytest.raises(ValueError):
        verify_report(r)


def test_application_errors_separate(monkeypatch, tmp_path):
    from evals import runner
    from evals import semantic_runner_v31 as v31

    def fail(*a, **k):
        raise RuntimeError("private payload")

    monkeypatch.setattr(runner, "analyze_soc_alert", fail)
    monkeypatch.setattr(runner, "analyze_governance_risk", fail)
    monkeypatch.setattr(v31, "RESULT_DIR", tmp_path)
    assert v31.main(["--trials", "3"]) == 2
    r = SemanticReport.model_validate_json(next(tmp_path.glob("*.json")).read_bytes())
    v31.verify_report(r)
    assert r.totals.application_error_count == 39
    assert r.totals.trials_failed == 0
    assert r.stability_counts["infrastructure_error"] == 13
    assert "private payload" not in r.model_dump_json()
