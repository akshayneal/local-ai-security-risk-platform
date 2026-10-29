"""Pure product helper tests need no server, inference or network."""

import json

import pytest
import requests
from test_schemas import GOVERNANCE_INPUT, GOVERNANCE_RESPONSE, SOC_INPUT, SOC_RESPONSE

from app.schemas import (
    GovernanceRiskRequest,
    GovernanceRiskResponse,
    SocAlertRequest,
    SocAlertResponse,
)
from app.ui_schemas import COMMON_CHECKS, SOC_CHECKS
from dashboard.api_client import (
    GENERIC_ERROR,
    POLICY_ERROR,
    UNAVAILABLE,
    get_data,
    post_analysis,
    safe_error,
)
from dashboard.evaluation_catalog import (
    CATALOG,
    COMPARISON_PATH,
    CROSS_VERSION_CAVEAT,
    ROOT,
    ArtifactUnavailable,
    catalog_rows,
    same_suite_comparison,
)
from dashboard.exports import DISCLAIMER, export_document, json_export, markdown_export
from dashboard.presentation import audit_rows, integrity_rows
from dashboard.sample_loader import (
    SampleLoadError,
    form_values,
    load_governance_samples,
    load_soc_samples,
    sample_labels,
    select_sample,
)


@pytest.mark.parametrize(
    "loader,count", [(load_soc_samples, 3), (load_governance_samples, 2)]
)
def test_bundled_samples_validate_and_selection_is_independent(loader, count):
    samples = loader()
    assert len(samples) == count
    assert len(set(sample_labels(samples))) == count
    for label, sample in zip(sample_labels(samples), samples, strict=True):
        selected = select_sample(samples, label)
        assert selected == sample and selected is not sample
        assert all(isinstance(v, str) for v in form_values(selected).values())
    with pytest.raises(SampleLoadError):
        select_sample(samples, "NOT A SAMPLE")


def test_soc_indicators_parse_as_json_lists():
    samples = load_soc_samples()
    assert samples[0].known_indicators == ["192.0.2.10"]
    assert samples[2].known_indicators == ["203.0.113.30", "payload.example.invalid"]
    assert (
        form_values(samples[2])["known_indicators"]
        == "203.0.113.30\npayload.example.invalid"
    )


@pytest.mark.parametrize(
    "loader,content",
    [
        (load_soc_samples, ""),
        (load_soc_samples, "alert_id,known_indicators\nx,not-json\n"),
        (load_soc_samples, 'alert_id,known_indicators\nx,"{}"\n'),
        (load_soc_samples, "wrong,fields\nx,y\n"),
        (load_governance_samples, "{}"),
        (load_governance_samples, "[]"),
        (load_governance_samples, "[{}]"),
        (load_governance_samples, "[null]"),
        (load_governance_samples, "[invalid"),
    ],
)
def test_malformed_samples_fail_cleanly(tmp_path, loader, content):
    path = tmp_path / "private-sample"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(SampleLoadError) as exc:
        loader(path)
    assert str(path) not in str(exc.value)


@pytest.mark.parametrize("loader", [load_soc_samples, load_governance_samples])
def test_missing_samples_fail_cleanly(tmp_path, loader):
    with pytest.raises(SampleLoadError):
        loader(tmp_path / "missing")


SOURCE = {
    "source_id": "DEMO-SOURCE",
    "title": "Demo guidance",
    "framework": "Local",
    "relevance": "Useful context",
}


@pytest.mark.parametrize("soc", [True, False])
def test_exports_contain_case_sections_sources_and_no_diagnostics(soc):
    request = (
        SocAlertRequest(**SOC_INPUT)
        if soc
        else GovernanceRiskRequest(**GOVERNANCE_INPUT)
    )
    response_model = SocAlertResponse if soc else GovernanceRiskResponse
    response = response_model(
        **{
            **(SOC_RESPONSE if soc else GOVERNANCE_RESPONSE),
            "source_references": [SOURCE],
            "analysis_trace": "SECRET",
            "internal_prompt": "SECRET",
        }
    )
    document = export_document(
        request, response, generated_at="2026-10-28T23:00:00+00:00"
    )
    text = markdown_export(document)
    encoded = json_export(document)
    assert json.loads(encoded) == document
    for value in SOURCE.values():
        assert value in text and value in encoded
    assert DISCLAIMER in text
    assert "2026-10-28T23:00:00+00:00" in text
    assert "Observed Evidence" in text if soc else "Required Controls" in text
    assert "None provided." in text
    assert "raw_log" not in encoded
    assert "SECRET" not in text + encoded
    assert "analysis_trace" not in text + encoded
    assert "internal_prompt" not in text + encoded


def test_export_empty_sources_and_markdown_escaping():
    response = SocAlertResponse(
        **{**SOC_RESPONSE, "summary": "[click](https://example.invalid) <script>"}
    )
    document = export_document(SocAlertRequest(**SOC_INPUT), response)
    text = markdown_export(document)
    assert "No source references returned." in text
    assert "\\[click\\]" in text and "\\<script\\>" in text
    assert document["generated_at"].endswith("+00:00")


def test_export_mismatched_workflows_rejected():
    with pytest.raises(TypeError):
        export_document(
            SocAlertRequest(**SOC_INPUT), GovernanceRiskResponse(**GOVERNANCE_RESPONSE)
        )


def test_catalog_all_versions_and_real_counts():
    rows, errors = catalog_rows()
    assert not errors and len(rows) == len(CATALOG) == 8
    assert [r["Official passes / valid"] for r in rows] == [
        "7/12",
        "7/12",
        "28/45",
        "43/44",
        "27/36",
        "37/39",
        "32/42",
        "37/41",
    ]
    assert [r["Application errors"] for r in rows] == [0, 0, 0, 1, 0, 0, 0, 1]
    assert "not directly comparable" in CROSS_VERSION_CAVEAT
    assert all((ROOT / p).is_file() for _, p, _, _ in CATALOG)
    assert (ROOT / COMPARISON_PATH).is_file()


def test_same_suite_metrics_and_cases_are_bounded_projections():
    comparison = same_suite_comparison()
    before, after = comparison["metrics"]
    assert before["Passes / valid"] == "32/42"
    assert after["Passes / valid"] == "37/41" and after["Passes / attempts"] == "37/42"
    assert [m["Application errors"] for m in comparison["metrics"]] == [0, 1]
    assert [m["Positive controls"] for m in comparison["metrics"]] == ["9/15", "13/15"]
    assert [m["Repair generations"] for m in comparison["metrics"]] == [4, 6]
    assert [m["Mean attempt seconds"] for m in comparison["metrics"]] == [65.31, 81.29]
    assert len(comparison["cases"]) == 14
    case = next(r for r in comparison["cases"] if r["Case ID"] == "V32-SOC-006")
    assert case["Treatment outcomes"] == "error / pass / pass"
    assert case["Stability transition"] == "mixed → stable_pass"
    assert "analysis_trace" not in json.dumps(comparison)
    assert "summary" not in json.dumps(comparison)


@pytest.mark.parametrize("content", [None, "{bad", "[]", "{}"])
def test_missing_corrupt_evidence_safe(tmp_path, content):
    if content is not None:
        for _, name, _, _ in CATALOG:
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    rows, errors = catalog_rows(tmp_path)
    assert not rows and len(errors) == 8
    assert str(tmp_path) not in str(errors)
    with pytest.raises(ArtifactUnavailable) as exc:
        same_suite_comparison(tmp_path)
    assert str(tmp_path) not in str(exc.value)


def test_mismatched_comparison_hash_fails_safely(tmp_path):
    for name in [
        COMPARISON_PATH,
        "evaluation_v3_2/semantic_baseline_3trial.json",
        "evaluation_v3_2/semantic_treatment_3trial.json",
    ]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads((ROOT / name).read_bytes())
        if name == COMPARISON_PATH:
            data["suite_byte_sha256"] = "different"
        path.write_text(json.dumps(data))
    with pytest.raises(ArtifactUnavailable):
        same_suite_comparison(tmp_path)


@pytest.mark.parametrize("repair", [False, True])
def test_integrity_panel_precise_labels(repair):
    metadata = {
        "checks": SOC_CHECKS,
        "integrity_status": "passed",
        "repair_attempted": repair,
        "repair_succeeded": True if repair else None,
    }
    rows = integrity_rows(metadata, soc=True)
    assert rows[0]["Status"] == "Passed"
    assert rows[-2]["Status"] == ("Successful repair" if repair else "Not required")
    assert rows[-1]["Status"] == "Required"
    assert any(r["Status"] == "Validated" for r in rows)


def test_governance_panel_does_not_claim_soc_contract():
    rows = integrity_rows({"checks": COMMON_CHECKS}, soc=False)
    assert len(rows) == 3
    assert "Critical identifiers" not in str(rows) and "Final contract" not in str(rows)
    assert all(r["Status"] == "Unavailable" for r in integrity_rows({}, soc=True)[:-1])


@pytest.mark.parametrize(
    "workflow,outcome,expected",
    [
        ("All", "All", 3),
        ("soc_alert", "All", 2),
        ("All", "Failure", 1),
        ("governance", "Success", 1),
        ("governance", "Failure", 0),
    ],
)
def test_audit_filtering_omits_errors(workflow, outcome, expected):
    logs = [
        {
            "mode": "soc_alert",
            "success": True,
            "source_ids": ["REF"],
            "error": "SECRET",
        },
        {
            "mode": "soc_alert",
            "success": False,
            "error": "SECRET",
            "result_summary": "SECRET",
        },
        {"mode": "governance", "success": True},
    ]
    rows = audit_rows(logs, workflow, outcome)
    assert len(rows) == expected
    assert "SECRET" not in json.dumps(rows) and "error" not in json.dumps(rows)
    assert audit_rows([]) == []


@pytest.mark.parametrize(
    "status,body,expected",
    [
        (
            500,
            {"detail": {"code": "integrity_validation_failed", "message": "SECRET"}},
            POLICY_ERROR,
        ),
        (500, {"detail": "SECRET"}, GENERIC_ERROR),
        (500, "SECRET", GENERIC_ERROR),
        (
            422,
            {"detail": [{"input": "SECRET"}]},
            "Some input fields are invalid or too long. Review the form and submit again.",
        ),
    ],
)
def test_safe_error_never_echoes_server_prose(status, body, expected):
    assert safe_error(status, body) == expected


@pytest.mark.parametrize(
    "exception", [requests.ConnectionError("SECRET"), requests.Timeout("SECRET")]
)
def test_api_transport_errors_safe(monkeypatch, exception):
    def fail(*args, **kwargs):
        raise exception

    monkeypatch.setattr(requests, "post", fail)
    monkeypatch.setattr(requests, "get", fail)
    result, error = post_analysis("http://local", "/ui/analyze/soc-alert", {})
    assert result is None and "SECRET" not in error
    assert get_data("http://local", "/logs") == (None, UNAVAILABLE)


@pytest.mark.parametrize(
    "status,body",
    [
        (500, {"detail": "SECRET"}),
        (200, []),
        (200, {}),
        (200, {"analysis": [], "metadata": {}}),
    ],
)
def test_api_malformed_or_error_body_is_generic(monkeypatch, status, body):
    class Response:
        ok = status == 200
        status_code = status

        def json(self):
            return body

    monkeypatch.setattr(requests, "post", lambda *a, **kw: Response())
    assert post_analysis("http://local", "/ui/analyze/soc-alert", {}) == (
        None,
        GENERIC_ERROR,
    )


def test_api_non_json_response_is_safe(monkeypatch):
    class Response:
        def json(self):
            raise ValueError("SECRET HTML")

    monkeypatch.setattr(requests, "post", lambda *a, **kw: Response())
    assert post_analysis("http://local", "/ui/analyze/soc-alert", {}) == (
        None,
        GENERIC_ERROR,
    )


@pytest.mark.parametrize("results", [None, {}, [None], ["SECRET"]])
def test_structurally_corrupt_v1_results_are_safe(tmp_path, results):
    path = tmp_path / CATALOG[0][1]
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"total_cases": 12, "passed": 7, "results": results}))
    rows, errors = catalog_rows(tmp_path)
    assert not rows and len(errors) == 8 and "SECRET" not in str(errors)
