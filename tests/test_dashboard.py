"""Deterministic product smoke tests using Streamlit's in-process harness."""

from pathlib import Path
from types import SimpleNamespace

import pytest
import requests
from streamlit.testing.v1 import AppTest
from test_schemas import GOVERNANCE_RESPONSE, SOC_RESPONSE

from app.ui_schemas import COMMON_CHECKS, SOC_CHECKS
from dashboard.api_client import POLICY_ERROR

ENTRY = Path(__file__).resolve().parents[1] / "dashboard/streamlit_app.py"
PAGES = {
    "Overview": "pages/overview.py",
    "SOC Investigation": "pages/soc_investigation.py",
    "AI System Risk Review": "pages/ai_system_risk_review.py",
    "Platform Evaluation": "pages/platform_evaluation.py",
    "Activity": "pages/activity.py",
    "About": "pages/about.py",
}


def open_page(page="SOC Investigation"):
    app = AppTest.from_file(ENTRY, default_timeout=15).run()
    if page != "Overview":
        app.switch_page(PAGES[page]).run()
    return app


def button(app, label):
    return next(item for item in app.button if item.label == label)


def fake_post(monkeypatch, *, soc=True, repair=False):
    calls = []
    result = {**(SOC_RESPONSE if soc else GOVERNANCE_RESPONSE), "source_references": []}
    if soc:
        result.update(
            observed_evidence=["Failed login recorded."],
            analyst_inferences=["Possible credential misuse."],
        )
    metadata = {
        "model": "qwen3:8b",
        "checks": list(SOC_CHECKS if soc else COMMON_CHECKS),
    }
    if soc:
        metadata.update(
            integrity_status="passed",
            repair_attempted=repair,
            repair_succeeded=True if repair else None,
        )

    def post(url, *, json, timeout):
        calls.append((url, json, timeout))
        return SimpleNamespace(
            ok=True, json=lambda: {"analysis": result, "metadata": metadata}
        )

    monkeypatch.setattr(requests, "post", post)
    return calls


@pytest.mark.parametrize("repair", [False, True])
def test_soc_dashboard_displays_findings_integrity_exports_and_preserves_result(
    monkeypatch, repair
):
    calls = fake_post(monkeypatch, repair=repair)
    app = open_page()
    button(app, "Analyze SOC alert").click().run()
    assert not app.exception
    headings = [item.value for item in app.subheader]
    assert (
        headings.index("Observed Evidence")
        < headings.index("Analyst Inferences")
        < headings.index("Analyst Note")
    )
    text = "\n".join(item.value for item in app.text)
    assert "Failed login recorded." in text and "Possible credential misuse." in text
    assert len(app.get("download_button")) == 2
    assert len(calls) == 1 and calls[0][0].endswith("/ui/analyze/soc-alert")
    assert calls[0][1]["known_indicators"] == ["192.0.2.10"]
    if repair:
        assert "Successful repair" in app.dataframe[0].value["Status"].tolist()
    app.run()
    assert len(calls) == 1 and len(app.get("download_button")) == 2


@pytest.mark.parametrize(
    "page",
    list(PAGES),
)
def test_every_page_loads_without_model_or_available_backend(monkeypatch, page):
    def unavailable(*args, **kwargs):
        raise requests.ConnectionError("SECRET")

    def no_post(*args, **kwargs):
        pytest.fail("Navigating must not analyze")

    monkeypatch.setattr(requests, "get", unavailable)
    monkeypatch.setattr(requests, "post", no_post)
    app = open_page(page)
    assert not app.exception
    if page == "Platform Evaluation":
        assert len(app.dataframe) == 4
        assert not any("unavailable" in item.value for item in app.warning)
    if page == "Activity":
        assert any("FastAPI is unavailable" in item.value for item in app.info)


@pytest.mark.parametrize("soc", [True, False])
def test_sample_loading_populates_each_form_and_analysis_uses_selected_sample(
    monkeypatch, soc
):
    calls = fake_post(monkeypatch, soc=soc)
    app = open_page()
    if not soc:
        app.switch_page(PAGES["AI System Risk Review"]).run()
    sample_widget = next(w for w in app.selectbox if w.label == "Synthetic sample")
    label = sample_widget.options[-1]
    sample_widget.select(label).run()
    button(app, "Load sample").click().run()
    assert not app.exception
    field = "soc_alert_id" if soc else "gov_system_name"
    assert app.text_input(key=field).value == label
    button(app, "Analyze SOC alert" if soc else "Review AI system").click().run()
    assert not app.exception and len(calls) == 1
    assert calls[0][1]["alert_id" if soc else "system_name"] == label
    assert len(app.get("download_button")) == 2
    if not soc:
        assert "Validation" in [w.value for w in app.subheader]
        assert "Response checks" not in [w.value for w in app.subheader]
    button(app, "Load sample").click().run()
    assert not app.get("download_button")


def test_fail_closed_clears_previous_result_and_never_shows_internal_details(
    monkeypatch,
):
    fake_post(monkeypatch)
    app = open_page()
    button(app, "Analyze SOC alert").click().run()
    assert len(app.get("download_button")) == 2
    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **kw: SimpleNamespace(
            ok=False,
            status_code=500,
            json=lambda: {
                "detail": {"code": "integrity_validation_failed", "message": "SECRET"}
            },
        ),
    )
    button(app, "Analyze SOC alert").click().run()
    assert not app.exception and not app.get("download_button")
    assert app.error[0].value == POLICY_ERROR


def test_source_empty_lists_and_older_result_render_cleanly():
    app = AppTest.from_string("""
from dashboard.workflows import soc_result, display_source_references
soc_result({"severity": "low"})
display_source_references({})
""").run()
    assert not app.exception
    assert any("No source references" in i.value for i in app.info)


def test_activity_filters_and_hides_stored_errors(monkeypatch):
    logs = [
        {"mode": "soc_alert", "success": False, "error": "SECRET", "source_ids": []},
        {"mode": "governance", "success": True, "source_ids": ["REF"]},
    ]
    monkeypatch.setattr(
        requests,
        "get",
        lambda *a, **kw: SimpleNamespace(
            raise_for_status=lambda: None, json=lambda: {"logs": logs}
        ),
    )
    app = open_page()
    app.switch_page(PAGES["Activity"]).run()
    assert len(app.dataframe[0].value) == 2
    assert "SECRET" not in app.dataframe[0].value.to_json()
    next(w for w in app.selectbox if w.label == "Outcome").select("Failure").run()
    assert len(app.dataframe[0].value) == 1
    assert not app.exception
