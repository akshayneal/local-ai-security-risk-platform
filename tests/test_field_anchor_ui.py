from copy import deepcopy
from types import SimpleNamespace

import pytest
import requests
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from test_analyst_correction_ui import save, widget
from test_dashboard import button, open_page
from test_field_anchors import field_report
from test_schemas import SOC_RESPONSE

from app import main, soc_analyzer
from dashboard.evidence_inspector import MAX_FIELD_CHOICES, field_label

SCRIPT = """
import streamlit as st
from test_field_anchors import field_report
from app.evidence_inspector import inspector_export
from dashboard.evidence_inspector import display_evidence_inspector,correction_history
rows=[{f'Field{j:02}':'PRIVATE-LARGE-VALUE' for j in range(50)} for i in range(5)] if st.session_state.get('large') else None
request,analysis,report=field_report(st.session_state.get('case','FIELD-CASE'),rows)
parsed,reviews=display_evidence_inspector(report.model_dump(mode='json'),prefix='test',submitted_input=request.model_dump(mode='json'))
st.session_state['export']=inspector_export(parsed,reviews,corrections=correction_history(parsed,prefix='test'))
st.session_state['original']=analysis.model_dump(mode='json')
"""


def test_precise_account_anchor_revision_privacy_and_case_reset(monkeypatch):
    def forbidden(*a, **kw):
        pytest.fail(
            "Field selection and correction editing must not call APIs or models"
        )

    monkeypatch.setattr(requests, "post", forbidden)
    monkeypatch.setattr(soc_analyzer, "call_model_json", forbidden)
    app = AppTest.from_string(SCRIPT).run()
    _, _, report = field_report()
    claim = next(c for c in report.claims if c.response_field == "summary")
    widget(app, "selectbox", "Claim to review").set_value(claim.claim_id).run()
    anchor = next(
        a
        for a in report.field_anchors
        if a.row_index == 1 and a.field_name == "UserPrincipalName"
    )
    assert "PRIVATE-SERVICE" not in field_label(anchor)
    assert "PRIVATE-SERVICE" not in str(
        widget(app, "multiselect", "Supplied field evidence").options
    )
    original = deepcopy(app.session_state["original"])
    widget(app, "multiselect", "Supplied field evidence").set_value(
        [anchor.evidence_id]
    )
    save(app, "The successful sign-in belongs to a different supplied account.")
    history = app.session_state["export"]["correction_history"]["revisions"]
    assert history[0]["evidence_ids"] == [anchor.evidence_id]
    assert not any("PRIVATE-SERVICE" in t.value for t in app.text)
    assert not next(
        c for c in app.checkbox if c.label == "Inspect a selected submitted value"
    ).value
    save(app, "Revised attribution, still unverified.")
    history = app.session_state["export"]["correction_history"]["revisions"]
    assert len(history) == 2 and history[1]["evidence_ids"] == [anchor.evidence_id]
    assert app.session_state["original"] == original
    app.session_state["case"] = "CHANGED-CASE"
    app.run()
    assert not app.exception and "correction_history" not in app.session_state["export"]


def test_large_field_picker_labels_coverage_and_retains_filtered_linked_fields():
    app = AppTest.from_string(SCRIPT)
    app.session_state["large"] = True
    app.run()
    assert (
        len(widget(app, "multiselect", "Supplied field evidence").options)
        == MAX_FIELD_CHOICES
    )
    assert any(
        "showing 200 of 250" in c.value and "Incomplete" in c.value for c in app.caption
    )
    widget(app, "text_input", "Filter supplied field anchors").input("Row 4").run()
    assert len(widget(app, "multiselect", "Supplied field evidence").options) == 50
    _, _, report = field_report(
        rows=[
            {f"Field{j:02}": "PRIVATE-LARGE-VALUE" for j in range(50)} for i in range(5)
        ]
    )
    anchor = next(a for a in report.field_anchors if a.row_index == 4)
    widget(app, "multiselect", "Supplied field evidence").set_value(
        [anchor.evidence_id]
    )
    save(app)
    widget(app, "text_input", "Filter supplied field anchors").input("").run()
    assert any("previously linked fields outside" in c.value for c in app.caption)
    save(app, "Retain the existing link while revising the wording.")
    assert app.session_state["export"]["correction_history"]["revisions"][-1][
        "evidence_ids"
    ] == [anchor.evidence_id]
    assert "PRIVATE-LARGE-VALUE" not in str(app.session_state["export"])
    assert not app.exception


def test_real_microsoft_workspace_exports_field_summary_without_extra_calls(
    monkeypatch,
):
    calls, generations, audits = [], [], []
    client = TestClient(main.app)
    monkeypatch.setattr(main, "write_audit_log", lambda **kw: audits.append(kw))

    def post(url, *, json, timeout):
        calls.append(json)
        raw = {
            **deepcopy(SOC_RESPONSE),
            "alert_id": json["alert_id"],
            "source_references": [],
            "observed_evidence": ["Supplied event requires analyst review."],
        }
        monkeypatch.setattr(
            soc_analyzer,
            "call_model_json",
            lambda **kw: generations.append(kw) or deepcopy(raw),
        )
        response = client.post("/ui/analyze/soc-alert", json=json)
        return SimpleNamespace(ok=response.is_success, json=response.json)

    monkeypatch.setattr(requests, "post", post)
    monkeypatch.setattr(
        requests,
        "get",
        lambda *a, **kw: SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"status": "ok", "model": "fixture", "version": "fixture"},
        ),
    )
    app = open_page()
    app.selectbox(key="soc_input_profile").select("Microsoft Security telemetry").run()
    button(app, "Load Microsoft sample").click().run()
    button(app, "Analyze Microsoft telemetry").click().run()
    assert not app.exception
    report = app.session_state["ms_result"]["envelope"]["metadata"][
        "evidence_inspector"
    ]
    anchor = report["field_anchors"][0]
    widget(app, "multiselect", "Supplied field evidence").set_value(
        [anchor["evidence_id"]]
    )
    save(app)
    doc = app.session_state["ms_result"]["document"]
    assert (
        doc["evidence_inspector"]["review_summary"]["claims"][0]["evidence_linked"]
        is True
    )
    assert doc["evidence_inspector"]["field_anchors"] == [anchor]
    assert len(app.get("download_button")) == 2
    assert len(calls) == len(generations) == len(audits) == 1
    app.text_area(key="ms_json").input("{}").run()
    assert (
        not app.get("download_button")
        and "ms_evidence_reviews" not in app.session_state
    )
