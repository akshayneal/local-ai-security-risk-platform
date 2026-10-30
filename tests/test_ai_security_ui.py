"""In-process third-workflow UI and safe export; no browser or real service."""

import copy
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from test_ai_security_contracts import case

from app import ai_security_analyzer as analyzer
from app import ai_security_api as api
from app.ai_security_contracts import AiSecurityEnvelope, AiSecurityRequest
from dashboard.ai_security import export_ai_security, markdown_ai_security

PAGE = Path(__file__).resolve().parents[1] / "dashboard/pages/ai_security_assessment.py"


def mock_api(monkeypatch):
    calls, audits = [], []
    row = case("RISK-2")
    monkeypatch.setattr(
        analyzer, "call_model_json", lambda **kw: copy.deepcopy(row["stub_output"])
    )
    monkeypatch.setattr(api, "write_audit_log", lambda **kw: audits.append(kw))

    def post(url, *, json, timeout):
        calls.append((url, json))
        with TestClient(api.app) as client:
            response = client.post("/ui/analyze/ai-security", json=json)
        return SimpleNamespace(
            ok=response.is_success, status_code=response.status_code, json=response.json
        )

    monkeypatch.setattr(requests, "post", post)
    return calls, audits


def button(page, label):
    return next(b for b in page.button if b.label == label)


def test_page_actual_route_stub_metadata_and_export_render(monkeypatch):
    calls, audits = mock_api(monkeypatch)
    page = AppTest.from_file(PAGE, default_timeout=15).run()
    assert not calls and not page.exception
    button(page, "Assess AI security").click().run()
    assert len(calls) == len(audits) == 1
    assert calls[0][0].endswith("/ui/analyze/ai-security")
    assert "local_knowledge" not in calls[0][1]
    assert len(page.get("download_button")) == 2 and not page.exception
    text = "\n".join(t.value for t in page.text)
    assert "candidate" in text and "not_verified" in text
    assert "local-ai-security-guidance-v1" in text
    assert "caller_supplied_unverified" in text
    assert any("gateway" in i.value.lower() for i in page.info)


def test_invalid_design_clears_prior_result_without_extra_generation(monkeypatch):
    calls, _ = mock_api(monkeypatch)
    page = AppTest.from_file(PAGE, default_timeout=15).run()
    button(page, "Assess AI security").click().run()
    page.text_area[0].set_value('{"access_scopes":["all"]}')
    button(page, "Assess AI security").click().run()
    assert len(calls) == 1 and page.error
    assert not page.get("download_button") and not page.exception


def test_insufficient_example_shows_no_generated_safety_verdict(monkeypatch):
    calls, _ = mock_api(monkeypatch)
    page = AppTest.from_file(PAGE, default_timeout=15).run()
    page.selectbox[0].set_value("Insufficient architecture").run()
    button(page, "Load synthetic design").click().run()
    button(page, "Assess AI security").click().run()
    assert len(calls) == 1
    assert "insufficient_information" in "\n".join(t.value for t in page.text)
    assert any("not evidence" in i.value for i in page.info)
    assert not page.exception


def test_export_escapes_untrusted_strings_and_rejects_wrong_binding(monkeypatch):
    row = case()
    row["input"]["application_name"] = (
        "<script>alert(1)</script> [link](https://example.invalid)"
    )
    monkeypatch.setattr(
        analyzer, "call_model_json", lambda **kw: copy.deepcopy(row["stub_output"])
    )
    request = AiSecurityRequest.model_validate(row["input"])
    envelope = analyzer.analyze_ai_security(request)
    document = export_ai_security(request, envelope)
    markdown = markdown_ai_security(document)
    assert "<script>" not in markdown and "[link](" not in markdown
    changed = envelope.model_dump(mode="json")
    changed["metadata"]["request_sha256"] = "0" * 64
    with pytest.raises(RuntimeError):
        export_ai_security(request, AiSecurityEnvelope.model_validate(changed))
