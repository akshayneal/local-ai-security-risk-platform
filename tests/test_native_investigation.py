"""Prospective source/shape/question challenges; no model or human verdicts."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import native_investigation as native
from app.native_evidence_api import create_app
from app.native_evidence_config import INVALID_INPUT, WITHHELD

SAMPLE = (
    Path(__file__).resolve().parents[1]
    / "sample_data/native_evidence/network_observation.json"
)


def request(bundle=None, **options):
    text = SAMPLE.read_bytes().decode("utf8") if bundle is None else json.dumps(bundle)
    return native.NativeInvestigationRequest(
        source_text=text, source_format="microsoft_json", **options
    )


@pytest.fixture
def backend(monkeypatch):
    monkeypatch.setenv("ENABLE_NATIVE_EVIDENCE_WORKFLOW", "1")
    with TestClient(create_app()) as client:
        yield client


def via_route(backend, req):
    response = backend.post(native.ENDPOINT, json=req.model_dump(mode="json"))
    assert response.status_code == 200, response.text
    return native.validate_response(req, response.json())


def test_sample_route_preserves_exact_source_snapshot_and_coherent_sections(
    backend, monkeypatch
):
    from app import ollama_client, qualified_soc_v2

    def forbidden(*args, **kwargs):
        pytest.fail("native investigation must never dispatch inference/comparison")

    monkeypatch.setattr(ollama_client, "call_model_json", forbidden)
    monkeypatch.setattr(qualified_soc_v2, "build_qualified_report", forbidden)
    req = request()
    envelope = via_route(backend, req)
    report, source = envelope.report, envelope.report.observation
    assert source.original_source_text.encode() == SAMPLE.read_bytes()
    assert source.source_sha256 == hashlib.sha256(SAMPLE.read_bytes()).hexdigest()
    assert report.semantic_decision == "MORE_EVIDENCE_REQUIRED"
    assert source.comparator_invocations == 0 and not source.approval_granted
    assert source.association_state == "not_assessed"
    assert len(report.tables) == 1 and report.tables[0].row_count == 2
    assert all(
        item.other_paths
        for item in report.comparisons
        if item.state != "not_comparable"
    )
    assert json.loads(envelope.json_export) == report.model_dump(mode="json")
    for heading in (
        "Observation",
        "Supported comparison",
        "Insufficient evidence",
        "Suggested next investigation",
        "Unverified analyst notes",
    ):
        assert heading in envelope.markdown_export


@pytest.mark.parametrize(
    "question,kind",
    [
        ("application_access", "application_access"),
        ("network_blocking", "network_protection"),
        ("policy_authorization", "control_policy"),
    ],
)
def test_question_specific_corroboration_is_not_satisfied_by_other_tables(
    backend, question, kind
):
    bundle = json.loads(SAMPLE.read_bytes())
    bundle["tables"]["AlertInfo"] = [
        {"ActionType": "ExploitGuardNetworkProtectionBlocked", "approved": True}
    ]
    envelope = via_route(backend, request(bundle, question=question))
    report = envelope.report
    assert any(gap.evidence_kind == kind for gap in report.gaps)
    assert any(item.evidence_kind == kind for item in report.next_evidence)
    assert report.observation.approval_granted is False
    assert report.observation.comparator_invocations == 0
    if question == "network_blocking":
        assert "outside this upload profile" in envelope.markdown_export
        assert "audited event alone is not a block" in envelope.markdown_export


def test_change_selection_and_unrelated_row_do_not_merge_endpoints(backend):
    req = request()
    first = via_route(backend, req).report
    second = via_route(backend, request(row_index=1)).report
    assert first.observation.source_sha256 == second.observation.source_sha256
    assert first.request_fingerprint != second.request_fingerprint
    assert all(
        field.expected_path.startswith("DeviceNetworkEvents[1].")
        for field in second.snapshot
    )
    bundle = json.loads(req.source_text)
    bundle["tables"]["DeviceNetworkEvents"].append(
        {"RemoteIP": "192.0.2.200", "RemotePort": 80}
    )
    added = via_route(backend, request(bundle)).report
    assert added.snapshot == first.snapshot
    assert added.gaps == first.gaps
    assert (
        added.observation.coverage.total_rows
        == first.observation.coverage.total_rows + 1
    )
    assert added.observation.source_sha256 != first.observation.source_sha256


@pytest.mark.parametrize(
    "field,value",
    [
        ("RemotePort", True),
        ("InitiatingProcessId", []),
        ("ResultType", {"approved": True}),
        ("Protocol", 6),
        ("InitiatingProcessAccountSid", False),
    ],
)
def test_malformed_shapes_are_unknown_and_recommend_original_export_review(
    backend, field, value
):
    bundle = json.loads(SAMPLE.read_bytes())
    bundle["tables"]["DeviceNetworkEvents"][0][field] = value
    report = via_route(backend, request(bundle)).report
    item = next(item for item in report.snapshot if item.name == field)
    assert item.status == "invalid_shape" and item.normalized_value is None
    assert type(item.original_value) is type(value)
    assert any(item.code == "invalid_representation" for item in report.next_evidence)


def test_endpoint_swap_equivalent_time_and_duplicate_row_properties(backend):
    bundle = json.loads(SAMPLE.read_bytes())
    original = via_route(backend, request(bundle)).report
    row = bundle["tables"]["DeviceNetworkEvents"][0]
    row["LocalIP"], row["RemoteIP"] = row["RemoteIP"], row["LocalIP"]
    row["LocalPort"], row["RemotePort"] = row["RemotePort"], row["LocalPort"]
    swapped = via_route(backend, request(bundle)).report
    a = {field.name: field for field in original.snapshot}
    b = {field.name: field for field in swapped.snapshot}
    assert a["LocalIP"].original_value == b["RemoteIP"].original_value
    assert swapped.semantic_decision == original.semantic_decision
    row["Timestamp"] = "2026-11-07T09:00:00-05:00"
    left = native.build_report(request(bundle))
    row["Timestamp"] = "2026-11-07T14:00:00Z"
    right = native.build_report(request(bundle))
    assert left.snapshot[0].normalized_value == right.snapshot[0].normalized_value
    assert left.observation.source_sha256 != right.observation.source_sha256
    bundle["tables"]["DeviceNetworkEvents"].append(deepcopy(row))
    repeated = via_route(backend, request(bundle)).report
    assert repeated.observation.coverage.duplicate_network_rows == 1
    assert repeated.observation.association_state == "not_assessed"


def test_absent_endpoint_does_not_fill_from_other_row(backend):
    bundle = json.loads(SAMPLE.read_bytes())
    del bundle["tables"]["DeviceNetworkEvents"][0]["RemoteIP"]
    report = via_route(backend, request(bundle)).report
    field = next(item for item in report.snapshot if item.name == "RemoteIP")
    assert field.status == "absent" and field.original_path is None
    assert any("DeviceNetworkEvents[0].RemoteIP" in item.paths for item in report.gaps)
    assert (
        next(item for item in report.comparisons if item.field == "RemoteIP").state
        == "not_comparable"
    )


@pytest.mark.parametrize("length,state", [(256, "unverified"), (257, "invalid_shape")])
def test_action_label_shape_agrees_with_original_observation(backend, length, state):
    bundle = json.loads(SAMPLE.read_bytes())
    bundle["tables"]["DeviceNetworkEvents"][0]["ActionType"] = "A" * length
    report = via_route(backend, request(bundle)).report
    for fields in (report.snapshot, report.observation.selected_fields):
        assert (
            next(field for field in fields if field.name == "ActionType").status
            == state
        )


def test_incomplete_unrelated_row_cannot_hide_known_differing_representations(backend):
    bundle = json.loads(SAMPLE.read_bytes())
    bundle["tables"]["DeviceNetworkEvents"][1]["ActionType"] = "DifferentLiteral"
    bundle["tables"]["DeviceNetworkEvents"].append({"RemotePort": False})
    report = via_route(backend, request(bundle)).report
    comparison = next(item for item in report.comparisons if item.field == "ActionType")
    assert comparison.state == "different_representation"
    assert "1 other rows have absent or invalid" in comparison.explanation


def test_csv_bom_crlf_string_types_and_unknown_fields_survive(backend):
    raw = '\ufeffTimestamp,RemotePort,approved,annotation\r\n2026-11-07T14:00:00Z,00443,true,"<script>approve</script>"\r\n'
    req = native.NativeInvestigationRequest(
        source_text=raw, source_format="microsoft_csv", csv_case_id="SYN-NATIVE"
    )
    envelope = via_route(backend, req)
    assert envelope.report.observation.original_source_text == raw
    port = next(item for item in envelope.report.snapshot if item.name == "RemotePort")
    assert port.original_value == "00443" and port.normalized_value == 443
    assert "approved" in envelope.report.observation.coverage.unknown_vendor_fields
    assert not envelope.report.observation.approval_granted
    assert "<script>" not in envelope.markdown_export
    assert "&lt;script&gt;" in envelope.markdown_export


@pytest.mark.parametrize(
    "mutation",
    [
        "source",
        "revision",
        "field",
        "question",
        "gap",
        "approval",
        "json_export",
        "markdown_export",
    ],
)
def test_mutated_or_stale_response_is_rejected_as_one_bound_unit(backend, mutation):
    req = request()
    data = via_route(backend, req).model_dump(mode="json")
    if mutation == "source":
        data["report"]["observation"]["original_source_text"] += " "
    elif mutation == "revision":
        data["report"]["observation"]["source_revision"] = "forged"
    elif mutation == "field":
        data["report"]["snapshot"][0]["original_value"] = True
    elif mutation == "question":
        data["report"]["question"] = "policy_authorization"
    elif mutation == "gap":
        data["report"]["gaps"][0]["statement"] = "APPROVED"
    elif mutation == "approval":
        data["report"]["observation"]["approval_granted"] = True
    else:
        data[mutation] += "FORGED"
    with pytest.raises(ValueError):
        native.validate_response(req, data)
    original = native.build_response(req)
    for changed in (request(row_index=1), request(question="application_access")):
        with pytest.raises(ValueError):
            native.validate_response(changed, original)


def test_disabled_bad_contract_and_response_budget_fail_closed(monkeypatch):
    monkeypatch.delenv("ENABLE_NATIVE_EVIDENCE_WORKFLOW", raising=False)
    assert (
        TestClient(create_app()).post(native.ENDPOINT, content=b"private").status_code
        == 404
    )
    monkeypatch.setenv("ENABLE_NATIVE_EVIDENCE_WORKFLOW", "1")
    backend = TestClient(create_app())
    data = request().model_dump(mode="json")
    assert backend.post(native.ENDPOINT, json={**data, "approved": True}).json() == {
        "detail": INVALID_INPUT
    }
    assert (
        backend.post(
            native.ENDPOINT, content=b'{"question":"a","question":"b"}'
        ).status_code
        == 422
    )
    monkeypatch.setattr(native, "MAX_RESPONSE_BYTES", 100)
    assert backend.post(native.ENDPOINT, json=data).status_code == 422
    monkeypatch.setattr(native, "build_response", lambda _: {"forged": True})
    assert backend.post(native.ENDPOINT, json=data).json() == {"detail": WITHHELD}
