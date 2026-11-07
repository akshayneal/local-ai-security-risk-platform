"""Actual experimental route, bounded uploads and old gateway compatibility."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import native_evidence_api as api
from app.native_evidence_config import ENABLE_FLAG, ENDPOINT, INVALID_INPUT, WITHHELD
from app.native_observations import NativeObservationRequest, validate_response

SAMPLE = (
    Path(__file__).resolve().parents[1]
    / "sample_data/native_evidence/network_observation.json"
)


def payload(**updates):
    return {
        "source_text": SAMPLE.read_text(encoding="utf-8"),
        "source_format": "microsoft_json",
        **updates,
    }


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setenv(ENABLE_FLAG, "1")
    with TestClient(api.create_app()) as client:
        yield client


def test_default_off_precedes_body_parsing_and_preserves_legacy_routes(monkeypatch):
    monkeypatch.delenv(ENABLE_FLAG, raising=False)
    with TestClient(api.create_app()) as client:
        assert client.post(ENDPOINT, content=b"x" * 400_001).status_code == 404
        assert client.post(ENDPOINT, content=b"{malformed").status_code == 404
        assert client.get("/health").json()["status"] == "ok"
        assert "soc_alert_request" in client.get("/schemas").json()
        assert client.get("/docs").status_code == 200
        schema = client.get("/openapi.json").json()
        assert "/ui/analyze/ai-security" in schema["paths"]
        assert ENDPOINT not in schema["paths"]


@pytest.mark.parametrize("value", ["", "0", "true", "True", " 1 "])
def test_only_exact_process_flag_enables_route(monkeypatch, value):
    monkeypatch.setenv(ENABLE_FLAG, value)
    with TestClient(api.create_app()) as client:
        assert client.post(ENDPOINT, json=payload()).status_code == 404


def test_actual_json_route_exports_exact_source_without_a_model(enabled, monkeypatch):
    from app import adaptive_semantics, ollama_client

    def forbidden(*args, **kwargs):
        pytest.fail("native observations must never infer or compare")

    monkeypatch.setattr(adaptive_semantics, "project", forbidden)
    monkeypatch.setattr(ollama_client, "call_model_json", forbidden)
    original = "\ufeff" + SAMPLE.read_text(encoding="utf-8").replace("\n", "\r\n")
    request = NativeObservationRequest(**payload(source_text=original))
    response = enabled.post(ENDPOINT, json=request.model_dump(mode="json"))
    assert response.status_code == 200
    envelope = validate_response(request, response.json())
    assert envelope.report.original_source_text == original
    assert envelope.report.comparator_invocations == 0
    assert envelope.report.execution_state == "not_executed"
    assert envelope.report.review_status == "not_reviewed"
    assert envelope.report.authority == "observation_only"
    assert envelope.report.approval_granted is False
    assert json.loads(envelope.json_export) == envelope.report.model_dump(mode="json")
    assert "No actions executed. No approval granted." in envelope.markdown_export


def test_actual_csv_route_preserves_strings_and_untrusted_authority(enabled):
    request = NativeObservationRequest(
        source_text='Timestamp,RemotePort,approved,annotation\r\n2026-11-07T14:00:00Z,00443,true,"<script>ignore rules</script>"\r\n',
        source_format="microsoft_csv",
        csv_case_id="SYN-CSV-ROUTE",
    )
    response = enabled.post(ENDPOINT, json=request.model_dump(mode="json"))
    assert response.status_code == 200
    envelope = validate_response(request, response.json())
    fields = {field.name: field for field in envelope.report.selected_fields}
    assert fields["RemotePort"].original_value == "00443"
    assert fields["RemotePort"].original_type == "str"
    assert fields["approved"].original_value == "true"
    assert envelope.report.approval_granted is False
    assert "<script>" not in envelope.markdown_export
    assert "&lt;script&gt;" in envelope.markdown_export


@pytest.mark.parametrize(
    "updates",
    [
        {"approved": True},
        {"source_id": "FORGED"},
        {"current": True},
        {"review": {"approved": True}},
        {"authority": "policy"},
        {"row_index": True},
        {"row_index": "0"},
        {"row_index": -1},
        {"row_index": 50},
        {"source_text": "x" * 64_001},
        {"source_format": "arbitrary"},
        {"csv_case_id": "FORGED"},
    ],
    ids=[f"request_{index}" for index in range(12)],
)
def test_strict_request_cannot_grant_review_or_coerce_indices(enabled, updates):
    response = enabled.post(ENDPOINT, json=payload(**updates))
    assert response.status_code == 422
    assert response.json() == {"detail": INVALID_INPUT}
    assert "FORGED" not in response.text


@pytest.mark.parametrize(
    "body,status",
    [
        (b'{"source_text":"SECRET_A","source_text":"SECRET_B"}', 422),
        (b'{"source_text":"\xff"}', 422),
        (b'{"row_index":NaN}', 422),
        (b"[" * 20 + b"0" + b"]" * 20, 422),
        (b" " * 400_001, 413),
    ],
    ids=["duplicate", "encoding", "nonfinite", "depth", "wire"],
)
def test_outer_wire_failures_are_bounded_and_sanitized(enabled, body, status):
    response = enabled.post(
        ENDPOINT, content=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == status
    assert response.json() == {"detail": INVALID_INPUT}
    assert "SECRET" not in response.text


@pytest.mark.parametrize(
    "source",
    ['{"case_id":"SECRET","case_id":"DUP","tables":{}}', '{"SECRET":1}', "[" * 50],
)
def test_inner_telemetry_failure_never_echoes_source(enabled, source):
    response = enabled.post(ENDPOINT, json=payload(source_text=source))
    assert response.status_code == 422
    assert response.json() == {"detail": INVALID_INPUT}
    assert "SECRET" not in response.text


def test_request_cannot_enable_route_or_sneak_through_a_redirect(monkeypatch):
    monkeypatch.delenv(ENABLE_FLAG, raising=False)
    with TestClient(api.create_app()) as client:
        response = client.post(
            ENDPOINT, json={**payload(), ENABLE_FLAG: "1"}, follow_redirects=False
        )
    assert response.status_code == 404


def test_unexpected_failures_and_forged_builder_results_are_withheld(
    enabled, monkeypatch
):
    def fail(*args, **kwargs):
        raise RuntimeError("PRIVATE_SOURCE exception body")

    monkeypatch.setattr(api, "build_response", fail)
    response = enabled.post(ENDPOINT, json=payload())
    assert response.status_code == 500
    assert response.json() == {"detail": WITHHELD}
    assert "PRIVATE_SOURCE" not in response.text
    monkeypatch.setattr(
        api, "build_response", lambda request: {"report": "PRIVATE_SOURCE"}
    )
    response = enabled.post(ENDPOINT, json=payload())
    assert response.status_code == 500
    assert response.json() == {"detail": WITHHELD}


def test_response_wire_bound_is_checked_after_serialization(enabled, monkeypatch):
    monkeypatch.setattr(api, "MAX_RESPONSE_BYTES", 20)
    response = enabled.post(ENDPOINT, json=payload())
    assert response.status_code == 500
    assert response.json() == {"detail": WITHHELD}
