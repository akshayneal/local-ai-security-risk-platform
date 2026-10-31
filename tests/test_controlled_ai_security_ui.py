"""Compact stub -> real route -> Streamlit/export; no browser or provider."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from test_controlled_ai_security import design, generation

from app import ai_security_analyzer as analyzer
from app import ai_security_api as api
from app.ai_security_contracts import AiSecurityEnvelope, AiSecurityRequest
from app.retrieval.storage import fingerprint
from dashboard.ai_security import export_ai_security, markdown_ai_security

PAGE = Path(__file__).resolve().parents[1] / "dashboard/pages/ai_security_assessment.py"
BASE_URL = "http://127.0.0.1:8273"


def assess(page):
    next(b for b in page.button if b.label == "Assess AI security").click().run()


def rendered_compact_page(monkeypatch, *, findings=True, hostile=False):
    request_data = design().model_dump(mode="json")
    raw = generation(findings=findings)
    if hostile:
        request_data["application_name"] = (
            "<script>alert(1)</script> [outside](https://example.invalid)"
        )
        raw["findings"][0]["hypothesis"] = (
            "If separation fails, <b>untrusted</b> [outside](https://example.invalid) "
            "may enter a draft."
        )
    request = AiSecurityRequest.model_validate(request_data)
    state = SimpleNamespace(
        request=request, generations=[], posts=[], audits=[], body=None
    )
    monkeypatch.setenv("API_BASE_URL", BASE_URL)
    monkeypatch.setattr(api, "write_audit_log", lambda **row: state.audits.append(row))

    def generate(**kwargs):
        assert set(kwargs["response_schema"]["properties"]) == {
            "findings",
            "evidence_gaps",
            "human_review_requirements",
        }
        state.generations.append(kwargs)
        return copy.deepcopy(raw)

    monkeypatch.setattr(analyzer, "call_model_json", generate)

    def post(url, *, json, timeout):
        assert url == BASE_URL + "/ui/analyze/ai-security" and timeout == 300
        state.posts.append(copy.deepcopy(json))
        with TestClient(api.app) as client:
            response = client.post("/ui/analyze/ai-security", json=json)
        assert response.status_code == 200, response.json()
        state.body = response.json()
        AiSecurityEnvelope.model_validate(state.body)
        return SimpleNamespace(ok=True, status_code=200, json=response.json)

    monkeypatch.setattr(requests, "post", post)
    page = AppTest.from_file(PAGE, default_timeout=15).run()
    assert not page.exception and not state.posts and not state.generations
    page.text_area[0].set_value(request.model_dump_json())
    assess(page)
    return page, state


@pytest.mark.parametrize("findings", [True, False])
def test_compact_current_ui_preserves_public_metadata_and_exports(
    monkeypatch, findings
):
    page, state = rendered_compact_page(monkeypatch, findings=findings)
    assert not page.exception and not page.error
    assert len(state.posts) == len(state.generations) == len(state.audits) == 1
    assert state.audits[0]["success"]
    assert len(page.get("download_button")) == 2
    envelope = AiSecurityEnvelope.model_validate(state.body)
    assert envelope.analysis.coverage_status == "advisory_returned"
    assert len(envelope.analysis.findings) == int(findings)
    assert envelope.metadata.request_sha256 == fingerprint(state.request)
    assert envelope.metadata.claim_status == "unassessed"
    assert envelope.analysis.action_status == "no_actions_executed"
    assert envelope.analysis.verification_status == "not_verified"
    assert len(envelope.metadata.sources) == 6
    assert sum(bool(s.cited_by_finding_ids) for s in envelope.metadata.sources) == int(
        findings
    )
    text = "\n".join(t.value for t in page.text)
    assert "advisory_returned" in text and "not proof of safety" in text
    assert "local-ai-security-guidance-v1" in text
    assert envelope.metadata.design_provenance == "caller_supplied_unverified"
    if findings:
        assert "candidate / not_verified" in text
    else:
        assert any("not evidence" in item.value for item in page.info)
    document = export_ai_security(state.request, envelope)
    assert document["format"] == "ai-security-advisory-v1"
    assert document["analysis"] == state.body["analysis"]
    assert document["metadata"] == state.body["metadata"]
    assert document["submitted_design_summary"]["verification_status"] == "not_verified"
    assert "not redacted" in document["sharing_notice"]
    assert "source_path" not in json.dumps(document)


def test_invalid_edit_clears_compact_result_without_extra_generation(monkeypatch):
    page, state = rendered_compact_page(monkeypatch)
    assert len(page.get("download_button")) == 2
    page.text_area[0].set_value('{"access_scopes":["all"]}')
    assess(page)
    assert not page.exception and page.error
    assert not page.get("download_button")
    assert len(state.posts) == len(state.generations) == len(state.audits) == 1
    assert "advisory_returned" not in "\n".join(t.value for t in page.text)


def test_compact_ui_and_export_keep_hostile_strings_as_data(monkeypatch):
    page, state = rendered_compact_page(monkeypatch, hostile=True)
    assert not page.exception and not page.error
    assert len(page.get("download_button")) == 2
    assert "<b>untrusted</b>" in "\n".join(t.value for t in page.text)
    envelope = AiSecurityEnvelope.model_validate(state.body)
    document = export_ai_security(state.request, envelope)
    markdown = markdown_ai_security(document)
    assert document["application_name"] == state.request.application_name
    assert "<script>" not in markdown and "<b>" not in markdown
    assert "[outside](" not in markdown
    changed = envelope.model_dump(mode="json")
    changed["metadata"]["request_sha256"] = "0" * 64
    with pytest.raises(RuntimeError):
        export_ai_security(state.request, AiSecurityEnvelope.model_validate(changed))
