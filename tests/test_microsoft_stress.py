import copy
import hashlib
import json
from pathlib import Path

from test_schemas import GOVERNANCE_RESPONSE, SOC_RESPONSE

from evals.microsoft_stress.runner import (
    deterministic_checks,
    load_cases,
    preflight,
    run,
)


def test_selected_live_artifact_identity_and_narrow_checks():
    from app.reference_loader import get_reference_ids, get_relevant_references
    from app.retrieval.storage import fingerprint

    directory = Path(__file__).resolve().parents[1] / "Documentation/microsoft_stress"
    raw = (directory / "selected_live_baseline.json").read_bytes()
    report = json.loads(raw)
    manifest = json.loads((directory / "provenance.json").read_bytes())
    assert hashlib.sha256(raw).hexdigest() == manifest["baseline_byte_sha256"]
    assert (
        report["application_sha"]
        == manifest["application_sha"]
        == "0f90fd543614e68609f6aedfc0e9d9440e9c368c"
    )
    assert (
        report["suite_sha256"] == manifest["suite_sha256"] == fingerprint(load_cases())
    )
    assert not report["git_dirty"] and report["trials_per_case"] == 1
    assert report["retrieval_backend"] == "legacy" and report["seed"] is None
    assert len(report["results"]) == 4
    assert sum(r["error"] is not None for r in report["results"]) == 1
    cases = {c["case_id"]: c for c in load_cases()}
    for row in report["results"]:
        case = row["case"]
        assert case == cases[case["case_id"]]
        assert row["preflight"] == preflight(case)
        if row["result"] is not None:
            request_json = json.dumps(case["request"], separators=(",", ":"))
            refs = get_relevant_references(
                case["workflow"],
                request_json,
                5 if case["workflow"] == "soc_alert" else 6,
            )
            assert row["deterministic_checks"] == deterministic_checks(
                case, row["result"], get_reference_ids(refs)
            )


def test_stress_preflight_all_cases_no_model():
    cases = load_cases()
    assert len(cases) == 14
    assert sum(c["workflow"] == "soc_alert" for c in cases) == 8
    assert sum(c["workflow"] == "governance" for c in cases) == 6
    assert all(all(preflight(c).values()) for c in cases)
    assert (
        len({c["category"] for c in cases}) == 13
    )  # Positive control in both workflows.
    assert run(selected=[cases[0]["case_id"]])["trials_per_case"] == 0


def test_stress_checks_detect_invention_canary_and_source_fabrication():
    case = load_cases()[2]
    response = copy.deepcopy(SOC_RESPONSE)
    response.update(
        observed_evidence=["198.51.100.250 COMPROMISED-CANARY"],
        source_references=[{"source_id": "FAKE"}],
    )
    checks = deterministic_checks(case, response, {"ALLOWED"})
    assert not checks["ipv4_membership"]
    assert not checks["injection_canary_absent"]
    assert not checks["source_ids_supplied"]
    assert checks["nonempty_observations"]
    faq = next(c for c in load_cases() if c["case_id"] == "MSAI-005-faq")
    response = {**GOVERNANCE_RESPONSE, "summary": "ALLOWED", "source_references": []}
    assert not deterministic_checks(faq, response, {"ALLOWED"})[
        "source_ids_absent_from_prose"
    ]


def test_live_harness_mock_capture_exercises_existing_analyzers(monkeypatch):
    from app.schemas import GovernanceRiskResponse, SocAlertResponse
    from evals.microsoft_stress import runner

    soc = dict(SOC_RESPONSE, observed_evidence=["Supplied event"], source_references=[])
    gov = dict(GOVERNANCE_RESPONSE, source_references=[])
    monkeypatch.setattr(
        runner, "analyze_soc_alert", lambda request, trace: SocAlertResponse(**soc)
    )
    monkeypatch.setattr(
        runner,
        "analyze_governance_risk",
        lambda request, trace: GovernanceRiskResponse(**gov),
    )
    monkeypatch.delenv("RETRIEVAL_BACKEND", raising=False)
    report = run(live=True)
    assert len(report["results"]) == 14
    assert all(r["error"] is None for r in report["results"])
    assert all(all(r["deterministic_checks"].values()) for r in report["results"])

    def fail(*a, **kw):
        raise ValueError("not included in artifact")

    monkeypatch.setattr(runner, "analyze_soc_alert", fail)
    report = run(live=True, selected=[load_cases()[0]["case_id"]])
    assert report["results"][0]["error"] == "ValueError"
    assert report["results"][0]["result"] is None
