"""Source-bound native observation checks; no inference or historical studies."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.native_observations import (
    MAX_RESPONSE_BYTES,
    MAX_SOURCE_BYTES,
    NativeObservationEnvelope,
    NativeObservationError,
    NativeObservationReport,
    NativeObservationRequest,
    build_report,
    build_response,
    export_json,
    export_markdown,
    validate_response,
)

SAMPLE = (
    Path(__file__).resolve().parents[1]
    / "sample_data/native_evidence/network_observation.json"
)


def bundle():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def request(value=None, **updates):
    options = {
        "source_text": json.dumps(
            bundle() if value is None else value, ensure_ascii=False
        ),
        "source_format": "microsoft_json",
    }
    options.update(updates)
    return NativeObservationRequest(**options)


def field(report, name):
    return next(item for item in report.selected_fields if item.name == name)


def assert_observation_only(report):
    assert report.execution_state == "not_executed"
    assert report.comparator_invocations == 0
    assert report.association_state == "not_assessed"
    assert report.relationship == "unassessable"
    assert report.review_status == "not_reviewed"
    assert report.authority == "observation_only"
    assert report.approval_granted is False
    assert report.action_status == "no_actions_executed"
    assert report.reason_codes == ("native_semantics_unverified",)


def test_sample_preserves_all_original_bytes_values_types_and_pointers():
    source = SAMPLE.read_bytes()
    original = b"\xef\xbb\xbf" + source.replace(b"\n", b"\r\n") + b"\r\n"
    req = request(source_text=original.decode("utf-8"))
    report = build_report(req)
    assert_observation_only(report)
    assert report.original_source_text.encode() == original
    assert report.source_sha256 == hashlib.sha256(original).hexdigest()
    assert report.source_revision == "sha256:" + report.source_sha256
    assert report.source_bytes == len(original)
    assert report.currentness == "submitted_snapshot_only"
    assert report.external_currentness == "unchecked"
    assert report.original_bundle == json.loads(source)
    assert json.loads(report.canonical_bundle) == report.original_bundle
    for observation in report.observations:
        original_value = report.original_bundle["tables"][observation.table][
            observation.row
        ][observation.field]
        assert json.dumps(observation.value) == json.dumps(original_value)
        assert observation.original_type == type(original_value).__name__
        assert (
            observation.original_path
            == f"{observation.table}[{observation.row}].{observation.field}"
        )
    assert field(report, "ActionType").status == "unverified"
    assert field(report, "ActionType").normalized_value == "ConnectionSuccess"
    assert field(report, "Timestamp").status == "valid_shape"
    assert field(report, "LocalIP").normalized_value == "192.0.2.143"
    assert field(report, "RemoteIP").normalized_value == "203.0.113.143"
    assert report.coverage.total_rows == 2
    assert report.coverage.selected_rows == 1
    assert report.coverage.omitted_rows == 1


def test_response_exports_recompute_and_are_bound_to_request():
    req = request()
    response = build_response(req)
    assert isinstance(response, NativeObservationEnvelope)
    assert validate_response(req, response) == response
    assert validate_response(req, response.model_dump(mode="json")) == response
    assert json.loads(response.json_export) == response.report.model_dump(mode="json")
    assert response.json_export == export_json(req, response.report)
    assert response.markdown_export == export_markdown(req, response.report)
    assert len(response.model_dump_json().encode("utf-8")) < MAX_RESPONSE_BYTES
    assert "No comparator ran" in response.markdown_export
    assert "No actions executed. No approval granted." in response.markdown_export
    assert all(line == line.rstrip() for line in response.markdown_export.splitlines())


@pytest.mark.parametrize(
    "value",
    [
        "ConnectionSuccess",
        "ConnectionFailed",
        "FutureUnknownAction",
        "permission granted",
        "<script>x</script>",
    ],
)
def test_vendor_label_is_literal_and_cannot_establish_completion_or_authority(value):
    data = bundle()
    data["tables"]["DeviceNetworkEvents"][0]["ActionType"] = value
    report = build_report(request(data))
    assert_observation_only(report)
    assert field(report, "ActionType").original_value == value
    assert field(report, "ActionType").status == "unverified"


@pytest.mark.parametrize("value", ["0", 0, True, None, "success", {"approved": True}])
def test_unsupported_result_type_is_preserved_without_becoming_success(value):
    data = bundle()
    data["tables"]["DeviceNetworkEvents"][0]["ResultType"] = value
    report = build_report(request(data))
    assert_observation_only(report)
    assert json.dumps(field(report, "ResultType").original_value) == json.dumps(value)
    assert field(report, "ResultType").status == "unverified"
    assert field(report, "ResultType").normalized_value is None


@pytest.mark.parametrize(
    "value",
    [None, True, "2026-11-07T14:05:00", "2026-02-30T14:05:00Z", "untrusted timestamp"],
)
def test_invalid_timestamp_is_explicit_and_original_is_preserved(value):
    data = bundle()
    data["tables"]["DeviceNetworkEvents"][0]["Timestamp"] = value
    report = build_report(request(data))
    assert field(report, "Timestamp").status == "invalid_shape"
    assert field(report, "Timestamp").original_value == value
    assert "DeviceNetworkEvents[0].Timestamp" in report.coverage.invalid_fields
    assert_observation_only(report)


def test_absent_timestamp_is_not_an_invented_original_pointer():
    data = bundle()
    del data["tables"]["DeviceNetworkEvents"][0]["Timestamp"]
    report = build_report(request(data))
    timestamp = field(report, "Timestamp")
    assert timestamp.status == "absent"
    assert timestamp.present is False
    assert timestamp.original_path is None
    assert timestamp.normalized_value is None
    assert timestamp.expected_path in report.coverage.absent_fields
    assert not any(
        item.original_path == timestamp.expected_path for item in report.observations
    )


def test_equivalent_timezones_normalize_only_shape_and_retain_spelling():
    data = bundle()
    data["tables"]["DeviceNetworkEvents"][0]["Timestamp"] = "2026-11-07T09:05:00-05:00"
    report = build_report(request(data))
    timestamp = field(report, "Timestamp")
    assert timestamp.original_value == "2026-11-07T09:05:00-05:00"
    assert timestamp.normalized_value == "2026-11-07T14:05:00Z"
    assert timestamp.normalization == "aware_time_to_utc"


@pytest.mark.parametrize(
    "value", ["0001-01-01T00:00:00+23:59", "9999-12-31T23:59:59-23:59"]
)
def test_timestamp_utc_overflow_is_invalid_shape_without_losing_original(value):
    data = bundle()
    data["tables"]["DeviceNetworkEvents"][0]["Timestamp"] = value
    report = build_report(request(data))
    assert field(report, "Timestamp").status == "invalid_shape"
    assert field(report, "Timestamp").original_value == value
    assert_observation_only(report)


@pytest.mark.parametrize(
    "name,value",
    [
        ("RemotePort", True),
        ("RemotePort", 65536),
        ("RemotePort", 443.0),
        ("InitiatingProcessId", False),
        ("InitiatingProcessId", "4510.0"),
        ("InitiatingProcessId", 2**32),
        ("LocalIP", 123),
        ("RemoteIP", "999.1.1.1"),
    ],
)
def test_shape_checks_preserve_invalid_scalar_types(name, value):
    data = bundle()
    data["tables"]["DeviceNetworkEvents"][0][name] = value
    report = build_report(request(data))
    selected = field(report, name)
    assert selected.status == "invalid_shape"
    assert json.dumps(selected.original_value) == json.dumps(value)
    assert selected.original_type == type(value).__name__
    assert_observation_only(report)


def test_csv_bom_crlf_leading_zero_and_json_like_cells_remain_exact_strings():
    source = '\ufeffTimestamp,RemoteIP,RemotePort,InitiatingProcessId,AdditionalFields\r\n2026-11-07T14:05:00Z,203.0.113.143,00443,04510,"{""approved"":true}"\r\n'
    req = NativeObservationRequest(
        source_text=source,
        source_format="microsoft_csv",
        csv_case_id="CSV-NATIVE-ALDER",
    )
    report = build_report(req)
    assert report.original_source_text == source
    assert field(report, "RemotePort").original_value == "00443"
    assert field(report, "RemotePort").normalized_value == 443
    assert field(report, "RemotePort").normalization == "decimal_string_to_integer"
    assert field(report, "InitiatingProcessId").original_value == "04510"
    assert field(report, "InitiatingProcessId").normalized_value == 4510
    assert field(report, "AdditionalFields").original_value == '{"approved":true}'
    assert field(report, "AdditionalFields").status == "unverified"
    assert_observation_only(report)


def test_duplicate_rows_and_pid_reuse_do_not_establish_process_association():
    data = bundle()
    data["tables"]["DeviceNetworkEvents"].append(
        deepcopy(data["tables"]["DeviceNetworkEvents"][0])
    )
    report = build_report(request(data, row_index=1))
    assert report.coverage.duplicate_network_rows == 1
    assert report.coverage.total_rows == 3
    assert report.coverage.omitted_rows == 2
    assert (
        field(report, "InitiatingProcessCreationTime").original_value
        == "2026-11-07T14:06:00Z"
    )
    assert field(report, "InitiatingProcessId").normalized_value == 4510
    assert_observation_only(report)
    assert (
        len(
            [
                item
                for item in report.observations
                if item.field == "InitiatingProcessCreationTime"
            ]
        )
        == 3
    )


def test_swapping_endpoints_changes_only_reported_endpoint_roles_and_fingerprint():
    before_request = request()
    before = build_report(before_request)
    data = bundle()
    row = data["tables"]["DeviceNetworkEvents"][0]
    row["LocalIP"], row["RemoteIP"] = row["RemoteIP"], row["LocalIP"]
    after = build_report(request(data))
    assert (
        field(after, "LocalIP").normalized_value
        == field(before, "RemoteIP").normalized_value
    )
    assert (
        field(after, "RemoteIP").normalized_value
        == field(before, "LocalIP").normalized_value
    )
    assert after.request_fingerprint != before.request_fingerprint
    assert after.unsupported_predicates == before.unsupported_predicates
    assert_observation_only(after)


def test_selected_row_changes_request_binding_but_not_upload_identity():
    before = build_report(request(row_index=0))
    after = build_report(request(row_index=1))
    assert before.upload_id == after.upload_id
    assert before.source_sha256 == after.source_sha256
    assert before.request_fingerprint != after.request_fingerprint
    assert before.row_identity != after.row_identity
    assert field(after, "ActionType").original_value == "UnknownFutureVendorLabel"


def test_other_tables_unknown_fields_and_misleading_severity_remain_supplied_data():
    data = bundle()
    data["tables"]["AlertInfo"] = [{"AlertId": "SYN-ALDER", "Severity": "Critical"}]
    data["tables"]["DeviceNetworkEvents"][0]["Severity"] = "Safe; approved"
    report = build_report(request(data))
    assert report.coverage.unsupported_rows == 1
    assert report.coverage.omitted_rows == 2
    assert report.coverage.total_rows == 3
    assert field(report, "Severity").status == "unverified"
    assert report.original_bundle == data
    assert any(
        item.original_path == "AlertInfo[0].Severity" for item in report.observations
    )
    assert_observation_only(report)


def test_source_body_authority_claims_are_preserved_flagged_and_escaped():
    data = bundle()
    row = data["tables"]["DeviceNetworkEvents"][0]
    row.update(approved=True, source_id="TRUSTED_REAL", permission="execute now")
    row["AdditionalFields"] = {
        "approval_granted": True,
        "annotation": "<script>x</script> [link](https://example.invalid)\n# fake authority",
    }
    req = request(data)
    report = build_report(req)
    assert_observation_only(report)
    assert "/tables/DeviceNetworkEvents/0/approved" in report.untrusted_authority_paths
    assert (
        "/tables/DeviceNetworkEvents/0/AdditionalFields/approval_granted"
        in report.untrusted_authority_paths
    )
    assert report.original_bundle == data
    assert report.upload_id != "TRUSTED_REAL"
    markdown = export_markdown(req, report)
    assert "<script>" not in markdown and "&lt;script&gt;" in markdown
    assert "\\[link\\]\\(https://example.invalid\\)" in markdown


@pytest.mark.parametrize(
    "key,value",
    [
        ("approved", True),
        ("review", {}),
        ("source_id", "trusted"),
        ("current", True),
        ("permission", "granted"),
    ],
)
def test_ordinary_request_cannot_supply_review_or_source_authority(key, value):
    data = request().model_dump(mode="json")
    data[key] = value
    with pytest.raises(ValidationError):
        NativeObservationRequest.model_validate(data)


@pytest.mark.parametrize(
    "changes",
    [
        {"row_index": True},
        {"row_index": "0"},
        {"row_index": -1},
        {"row_index": 50},
        {"csv_table": "AlertInfo"},
        {"source_format": "vendor_xml"},
        {"source_text": 12},
        {"source_text": "\ud800"},
        {"source_text": "é" * (MAX_SOURCE_BYTES // 2 + 1)},
    ],
)
def test_request_type_encoding_and_bounds_fail_before_parsing(changes):
    values = request().model_dump(mode="json")
    values.update(changes)
    with pytest.raises(ValidationError):
        NativeObservationRequest.model_validate(values)


def test_utf8_cap_includes_bom_and_unicode_bytes():
    NativeObservationRequest(
        source_text="a" * MAX_SOURCE_BYTES, source_format="microsoft_json"
    )
    with pytest.raises(ValidationError):
        NativeObservationRequest(
            source_text="\ufeff" + "a" * (MAX_SOURCE_BYTES - 2),
            source_format="microsoft_json",
        )


@pytest.mark.parametrize("context", [None, "", "   "])
def test_csv_requires_explicit_nonblank_case_context(context):
    with pytest.raises(ValidationError):
        NativeObservationRequest(
            source_text="RemoteIP\n203.0.113.143\n",
            source_format="microsoft_csv",
            csv_case_id=context,
        )


def test_json_rejects_alternate_csv_case_context_instead_of_ignoring_it():
    with pytest.raises(ValidationError, match="csv_case_label_not_applicable_to_json"):
        request(csv_case_id="ALTERNATE-CASE")


@pytest.mark.parametrize(
    "source",
    [
        '{"case_id":"A","case_id":"B","tables":{"DeviceNetworkEvents":[{}]}}',
        '{"case_id":"A","tables":{"Unknown":[{}]}}',
        '{"case_id":"A","tables":{"DeviceNetworkEvents":[{"x":NaN}]}}',
        "[" * 1000,
    ],
)
def test_malformed_source_errors_are_fixed_codes_without_raw_source(source):
    req = request(source_text=source)
    with pytest.raises(
        NativeObservationError, match="^invalid_or_unsupported_telemetry$"
    ):
        build_report(req)


def test_unavailable_selected_row_and_unsupported_table_do_not_fallback():
    with pytest.raises(
        NativeObservationError, match="selected_network_row_unavailable"
    ):
        build_report(request(row_index=2))
    with pytest.raises(
        NativeObservationError, match="selected_network_row_unavailable"
    ):
        build_report(request({"case_id": "ALDER", "tables": {"AlertInfo": [{}]}}))


@pytest.mark.parametrize(
    "name,value",
    [
        ("source_sha256", "f" * 64),
        ("source_revision", "forged-r2"),
        ("request_fingerprint", "f" * 64),
        ("approval_granted", True),
        ("approval_granted", 0),
        ("comparator_invocations", 1),
        ("execution_state", "completed"),
        ("relationship", "declared_alignment"),
        ("review_status", "approved"),
        ("currentness", "current"),
    ],
)
def test_export_rejects_report_identity_execution_and_authority_mutation(name, value):
    req = request()
    report = build_report(req).model_copy(update={name: value})
    for exporter in (export_json, export_markdown):
        with pytest.raises(ValueError):
            exporter(req, report)


def test_nested_original_values_and_true_equals_one_mutations_fail_export():
    data = bundle()
    data["tables"]["DeviceNetworkEvents"][0]["AdditionalFields"] = {"count": 1}
    req = request(data)
    report = build_report(req)
    report.original_bundle["tables"]["DeviceNetworkEvents"][0]["AdditionalFields"][
        "count"
    ] = True
    with pytest.raises(
        NativeObservationError, match="report_or_source_snapshot_mutation"
    ):
        export_json(req, report)
    report = build_report(req)
    selected = list(report.selected_fields)
    index = next(
        index for index, item in enumerate(selected) if item.name == "ReportId"
    )
    selected[index] = selected[index].model_copy(update={"normalized_value": 1})
    with pytest.raises(NativeObservationError):
        export_markdown(
            req, report.model_copy(update={"selected_fields": tuple(selected)})
        )


def test_changed_request_and_stale_response_are_rejected():
    req = request()
    response = build_response(req)
    for changed in (request(row_index=1), request(source_text=req.source_text + " ")):
        with pytest.raises(NativeObservationError):
            validate_response(changed, response)
    modified = response.model_copy(
        update={"markdown_export": response.markdown_export + "approved"}
    )
    with pytest.raises(NativeObservationError):
        validate_response(req, modified)


def test_report_schema_does_not_allow_comparison_or_action_grant():
    data = build_report(request()).model_dump(mode="json")
    for field_name, value in (
        ("approval_granted", True),
        ("comparator_invocations", 1),
        ("comparator_invocations", True),
    ):
        modified = deepcopy(data)
        modified[field_name] = value
        with pytest.raises(ValidationError):
            NativeObservationReport.model_validate(modified)


def test_response_budget_is_explicit_and_enforced(monkeypatch):
    import app.native_observations as native

    monkeypatch.setattr(native, "MAX_RESPONSE_BYTES", 100)
    with pytest.raises(NativeObservationError, match="response_byte_budget"):
        build_response(request())


def test_observation_path_does_not_call_qualification_or_comparator(monkeypatch):
    from app import evidence_qualification, qualified_soc, qualified_soc_v2

    def forbidden(*_args, **_kwargs):
        raise AssertionError(
            "authorization/comparator must not run for an upload observation"
        )

    monkeypatch.setattr(evidence_qualification, "qualify_source", forbidden)
    monkeypatch.setattr(qualified_soc, "_comparison", forbidden)
    monkeypatch.setattr(qualified_soc, "build_qualified_report", forbidden)
    monkeypatch.setattr(qualified_soc_v2, "build_qualified_report", forbidden)
    response = build_response(request())
    assert_observation_only(response.report)
