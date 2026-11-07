"""Unreviewed native upload observations; no model, authority or action route.

Typed shapes describe supplied values. They never prove event truth, source
authentication, completed access, permission or security consequences.
"""

import hashlib
import ipaddress
import json
import re
from datetime import UTC
from html import escape
from typing import Annotated, Any, Literal

from pydantic import (
    Field,
    StrictBool,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)

from app.evidence_qualification import instant
from app.soc_inputs import (
    MicrosoftSocAdapter,
    SocInputError,
    canonical_bundle,
    parse_csv_bundle,
    parse_json_bundle,
)
from app.support_contracts import SupportModel

MAX_SOURCE_BYTES = 64_000
MAX_RESPONSE_BYTES = 4_000_000
PROFILE_VERSION = "microsoft-projected-native-observation/1"
CaseLabel = Annotated[StrictStr, Field(min_length=1, max_length=256)]
Scalar = StrictStr | StrictInt | None


class NativeObservationError(ValueError):
    """Safe fixed error code, never rejected source or exception bodies."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class NativeObservationRequest(SupportModel):
    source_text: StrictStr = Field(min_length=1, max_length=MAX_SOURCE_BYTES)
    source_format: Literal["microsoft_json", "microsoft_csv"]
    row_index: StrictInt = Field(default=0, ge=0, le=49)
    csv_table: Literal["DeviceNetworkEvents"] = "DeviceNetworkEvents"
    csv_case_id: CaseLabel | None = None

    @field_validator("source_text")
    @classmethod
    def bounded_utf8(cls, value):
        try:
            raw = value.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise ValueError("source_must_be_utf8") from exc
        if len(raw) > MAX_SOURCE_BYTES:
            raise ValueError("source_byte_budget")
        return value

    @field_validator("csv_case_id")
    @classmethod
    def nonblank_case(cls, value):
        if value is not None and not value.strip():
            raise ValueError("nonblank_case_label_required")
        return value

    @model_validator(mode="after")
    def csv_context(self):
        if self.source_format == "microsoft_csv" and self.csv_case_id is None:
            raise ValueError("csv_case_label_required")
        if self.source_format == "microsoft_json" and self.csv_case_id is not None:
            raise ValueError("csv_case_label_not_applicable_to_json")
        return self


class OriginalObservation(SupportModel):
    table: StrictStr
    row: StrictInt
    field: StrictStr
    original_path: StrictStr
    value: Any
    original_type: StrictStr
    assertion_status: Literal["supplied_unverified"] = "supplied_unverified"


class TypedField(SupportModel):
    name: StrictStr
    expected_path: StrictStr
    original_path: StrictStr | None
    present: StrictBool
    original_value: Any = None
    original_type: StrictStr | None
    status: Literal["valid_shape", "absent", "invalid_shape", "unverified"]
    normalized_value: Scalar
    normalization: StrictStr
    reason_code: StrictStr
    assertion_status: Literal["supplied_unverified"] = "supplied_unverified"


class NativeCoverage(SupportModel):
    total_rows: StrictInt
    selected_rows: StrictInt
    omitted_rows: StrictInt
    unsupported_rows: StrictInt
    duplicate_network_rows: StrictInt
    selected_field_count: StrictInt
    invalid_fields: tuple[StrictStr, ...]
    absent_fields: tuple[StrictStr, ...]
    unverified_fields: tuple[StrictStr, ...]
    unknown_vendor_fields: tuple[StrictStr, ...]


class NativeObservationReport(SupportModel):
    schema_version: Literal["native-observation-report/1"] = (
        "native-observation-report/1"
    )
    request_fingerprint: StrictStr
    upload_id: StrictStr
    source_sha256: StrictStr
    source_revision: StrictStr
    source_bytes: StrictInt
    source_format: Literal["microsoft_json", "microsoft_csv"]
    source_profile: Literal["microsoft-projected-native-observation/1"] = (
        PROFILE_VERSION
    )
    source_status: Literal["supplied_unverified"] = "supplied_unverified"
    currentness: Literal["submitted_snapshot_only"] = "submitted_snapshot_only"
    external_currentness: Literal["unchecked"] = "unchecked"
    authority: Literal["observation_only"] = "observation_only"
    review_status: Literal["not_reviewed"] = "not_reviewed"
    case_id: StrictStr
    case_label_status: Literal["supplied_unverified"] = "supplied_unverified"
    row_index: StrictInt
    row_identity: StrictStr
    row_identity_status: Literal["upload_locator; not authenticated event identity"] = (
        "upload_locator; not authenticated event identity"
    )
    reported_event_class: Literal["supplied_DeviceNetworkEvents_row"] = (
        "supplied_DeviceNetworkEvents_row"
    )
    original_source_text: StrictStr
    original_bundle: dict
    canonical_bundle: StrictStr
    observations: tuple[OriginalObservation, ...]
    selected_fields: tuple[TypedField, ...]
    coverage: NativeCoverage
    untrusted_authority_paths: tuple[StrictStr, ...]
    warnings: tuple[StrictStr, ...]
    unsupported_predicates: tuple[StrictStr, ...]
    execution_state: Literal["not_executed"] = "not_executed"
    comparator_invocations: StrictInt = 0
    association_state: Literal["not_assessed"] = "not_assessed"
    relationship: Literal["unassessable"] = "unassessable"
    reason_codes: tuple[StrictStr, ...] = ("native_semantics_unverified",)
    approval_granted: StrictBool = False
    action_status: Literal["no_actions_executed"] = "no_actions_executed"
    capability_status: Literal["experimental_off_by_default"] = (
        "experimental_off_by_default"
    )
    independent_review: Literal["PENDING"] = "PENDING"

    @model_validator(mode="after")
    def observation_boundary(self):
        if self.comparator_invocations != 0 or self.approval_granted is not False:
            raise ValueError("observation_cannot_compare_or_grant")
        if (
            self.coverage.selected_rows != 1
            or self.coverage.total_rows != self.coverage.omitted_rows + 1
        ):
            raise ValueError("coverage_invariant")
        return self


class NativeObservationEnvelope(SupportModel):
    report: NativeObservationReport
    json_export: StrictStr
    markdown_export: StrictStr


TIMES = {"Timestamp", "InitiatingProcessCreationTime"}
PIDS = {"ProcessId", "InitiatingProcessId"}
PORTS = {"LocalPort", "RemotePort"}
IPS = {"LocalIP", "RemoteIP"}
IDENTIFIERS = {"DeviceId", "DeviceName", "InitiatingProcessAccountUpn"}
PROFILE_FIELDS = (
    "Timestamp",
    "ActionType",
    "ResultType",
    "DeviceId",
    "DeviceName",
    "ReportId",
    "InitiatingProcessId",
    "InitiatingProcessCreationTime",
    "InitiatingProcessAccountUpn",
    "InitiatingProcessFileName",
    "InitiatingProcessCommandLine",
    "LocalIP",
    "LocalPort",
    "RemoteIP",
    "RemotePort",
    "Protocol",
    "RemoteUrl",
    "Severity",
    "ProcessId",
)
AUTHORITY_KEYS = frozenset(
    {
        "approved",
        "authorized",
        "permission",
        "approval_granted",
        "source_id",
        "source_revision",
        "authority",
        "review_status",
        "requirement_reviewed",
        "current",
        "granted_access",
        "actions_executed",
        "executed_action",
        "workflow",
        "policy_scope",
    }
)
UNSUPPORTED = (
    "completed_connection_or_handshake",
    "completed_data_transfer",
    "data_flow_source_destination",
    "permission_or_policy_authority",
    "process_or_event_causal_association",
    "https_from_port_443",
    "compromise_or_attacker_intent",
    "attack_technique",
    "control_effectiveness",
)


def _canonical(value) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _request(value: NativeObservationRequest) -> NativeObservationRequest:
    try:
        return NativeObservationRequest.model_validate(
            value.model_dump(mode="json", warnings=False)
        )
    except (ValueError, TypeError, AttributeError) as exc:
        raise NativeObservationError("invalid_request_contract") from exc


def request_fingerprint(request: NativeObservationRequest) -> str:
    request = _request(request)
    return _digest(_canonical(request.model_dump(mode="json")).encode("utf-8"))


def _number(value, limit, digits):
    if type(value) is int and 0 <= value <= limit:
        return value, "identity_integer"
    if isinstance(value, str) and re.fullmatch(r"[0-9]{1," + str(digits) + r"}", value):
        number = int(value)
        if number <= limit:
            return number, "decimal_string_to_integer"
    raise ValueError("invalid_numeric_shape")


def _shape(name, value):
    """Validate representation only; never assign native operation semantics."""
    if name in TIMES:
        if not isinstance(value, str):
            raise ValueError("invalid_timestamp_shape")
        normalized = instant(value).astimezone(UTC).isoformat().replace("+00:00", "Z")
        return normalized, "aware_time_to_utc", "aware_timestamp_shape_only"
    if name in PORTS:
        number, transformation = _number(value, 65535, 5)
        return number, transformation, "port_shape_only"
    if name in PIDS:
        number, transformation = _number(value, 2**32 - 1, 10)
        return number, transformation, "pid_shape_only_no_process_join"
    if name == "ReportId":
        number, transformation = _number(value, 2**63 - 1, 19)
        return number, transformation, "reported_number_not_unique_identity"
    if name in IPS:
        if not isinstance(value, str):
            raise ValueError("invalid_ip_shape")
        return (
            str(ipaddress.ip_address(value)),
            "canonical_ip_text",
            "endpoint_role_preserved_shape_only",
        )
    if name in IDENTIFIERS:
        if not isinstance(value, str) or not value.strip() or len(value) > 256:
            raise ValueError("invalid_identifier_shape")
        return value, "identity_text", "reported_identifier_not_authenticated"
    if name == "ActionType":
        if not isinstance(value, str) or not value.strip() or len(value) > 256:
            raise ValueError("invalid_label_shape")
        return value, "identity_text", "reported_label_native_semantics_unverified"
    return None, "not_normalized", "field_semantics_not_established"


def _typed_field(row, index, name):
    path = f"DeviceNetworkEvents[{index}].{name}"
    if name not in row:
        return TypedField(
            name=name,
            expected_path=path,
            original_path=None,
            present=False,
            original_type=None,
            status="absent",
            normalized_value=None,
            normalization="none",
            reason_code="not_supplied",
        )
    value = row[name]
    try:
        normalized, transformation, reason = _shape(name, value)
        status = (
            "unverified"
            if name == "ActionType"
            or name not in TIMES | PIDS | PORTS | IPS | IDENTIFIERS | {"ReportId"}
            else "valid_shape"
        )
    except (ValueError, TypeError, OverflowError):
        normalized, transformation, reason, status = (
            None,
            "none",
            "invalid_field_shape",
            "invalid_shape",
        )
    return TypedField(
        name=name,
        expected_path=path,
        original_path=path,
        present=True,
        original_value=value,
        original_type=type(value).__name__,
        status=status,
        normalized_value=normalized,
        normalization=transformation,
        reason_code=reason,
    )


def _authority_paths(bundle):
    paths = []
    pending = [(bundle, "")]
    while pending:
        value, path = pending.pop()
        if isinstance(value, dict):
            for key, child in value.items():
                pointer = path + "/" + key.replace("~", "~0").replace("/", "~1")
                if key.casefold() in AUTHORITY_KEYS:
                    paths.append(pointer)
                pending.append((child, pointer))
        elif isinstance(value, list):
            pending.extend(
                (child, f"{path}/{index}") for index, child in enumerate(value)
            )
    return tuple(sorted(paths))


def build_report(request: NativeObservationRequest) -> NativeObservationReport:
    """Preserve the upload and describe one row without source qualification."""
    request = _request(request)
    raw = request.source_text.encode("utf-8")
    try:
        bundle = (
            parse_json_bundle(raw)
            if request.source_format == "microsoft_json"
            else parse_csv_bundle(raw, request.csv_table, request.csv_case_id)
        )
        normalized = MicrosoftSocAdapter().normalize(bundle)
    except SocInputError as exc:
        raise NativeObservationError("invalid_or_unsupported_telemetry") from exc
    rows = bundle["tables"].get("DeviceNetworkEvents", [])
    if request.row_index >= len(rows):
        raise NativeObservationError("selected_network_row_unavailable")
    row = rows[request.row_index]
    selected = tuple(
        _typed_field(row, request.row_index, name)
        for name in (PROFILE_FIELDS + tuple(sorted(set(row) - set(PROFILE_FIELDS))))
    )
    total = sum(normalized.row_counts.values())
    coverage = NativeCoverage(
        total_rows=total,
        selected_rows=1,
        omitted_rows=total - 1,
        unsupported_rows=total - len(rows),
        duplicate_network_rows=len(rows) - len({_canonical(value) for value in rows}),
        selected_field_count=len(row),
        invalid_fields=tuple(
            field.expected_path for field in selected if field.status == "invalid_shape"
        ),
        absent_fields=tuple(
            field.expected_path for field in selected if field.status == "absent"
        ),
        unverified_fields=tuple(
            field.expected_path for field in selected if field.status == "unverified"
        ),
        unknown_vendor_fields=tuple(sorted(set(row) - set(PROFILE_FIELDS))),
    )
    claims = _authority_paths(bundle)
    warnings = (
        tuple(normalized.warnings)
        + (
            "Uploads are unreviewed supplied observations; source authenticity and external currentness are unchecked.",
            "Valid field shape does not establish source truth, completed access, permission or security consequences.",
            "No process/event association or authorization comparison was performed; unsupported native semantics remain explicit.",
        )
        + (
            (
                "Source-body authority/permission claims are preserved as untrusted data and grant nothing.",
            )
            if claims
            else ()
        )
    )
    digest = _digest(raw)
    upload_id = "UPLOAD-" + digest[:24]
    return NativeObservationReport(
        request_fingerprint=request_fingerprint(request),
        upload_id=upload_id,
        source_sha256=digest,
        source_revision="sha256:" + digest,
        source_bytes=len(raw),
        source_format=request.source_format,
        case_id=bundle["case_id"],
        row_index=request.row_index,
        row_identity=f"{upload_id}/DeviceNetworkEvents/{request.row_index}",
        original_source_text=request.source_text,
        original_bundle=bundle,
        canonical_bundle=canonical_bundle(bundle),
        observations=tuple(
            OriginalObservation(
                table=value.table,
                row=value.row,
                field=value.field,
                original_path=f"{value.table}[{value.row}].{value.field}",
                value=value.value,
                original_type=type(value.value).__name__,
            )
            for value in normalized.observations
        ),
        selected_fields=selected,
        coverage=coverage,
        untrusted_authority_paths=claims,
        warnings=warnings,
        unsupported_predicates=UNSUPPORTED,
    )


def _validate_report(request, report):
    raw = (
        report.model_dump(mode="json", warnings=False)
        if isinstance(report, NativeObservationReport)
        else report
    )
    original = _canonical(raw)
    validated = NativeObservationReport.model_validate(raw)
    expected = build_report(request)
    if original != _canonical(
        validated.model_dump(mode="json")
    ) or original != _canonical(expected.model_dump(mode="json")):
        raise NativeObservationError("report_or_source_snapshot_mutation")
    return validated


def export_json(
    request: NativeObservationRequest, report: NativeObservationReport
) -> str:
    report = _validate_report(request, report)
    return json.dumps(
        report.model_dump(mode="json"), ensure_ascii=True, indent=2, allow_nan=False
    )


def export_markdown(
    request: NativeObservationRequest, report: NativeObservationReport
) -> str:
    report = _validate_report(request, report)

    def safe(value):
        return (
            re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", escape(str(value)))
            .replace("\r", " ")
            .replace("\n", " ")
            .rstrip()
        )

    lines = [
        "# Experimental native network observations",
        "Uploaded telemetry is unreviewed; source authenticity and external currentness are unchecked.",
        "Native semantics remain unverified. No comparator ran. No permission or action is granted.",
        "Case label (supplied): " + safe(report.case_id),
        "Upload locator: " + safe(report.upload_id),
        "Original byte SHA-256: " + report.source_sha256,
        "Request fingerprint: " + report.request_fingerprint,
        "Profile: " + report.source_profile,
        "Currentness: submitted snapshot only; this hash does not authenticate the source.",
        "Selected row locator: " + safe(report.row_identity),
        "## Selected supplied fields",
    ]
    for field in report.selected_fields:
        lines.append(
            f"- {safe(field.expected_path)}: {safe(field.status)}; original {safe(json.dumps(field.original_value, ensure_ascii=True))}; "
            f"type {safe(field.original_type)}; normalized {safe(json.dumps(field.normalized_value, ensure_ascii=True))}; "
            f"{safe(field.normalization)}; {safe(field.reason_code)}"
        )
    lines += [
        "## Coverage",
        safe(report.coverage.model_dump_json()),
        "## Unsupported downstream claims",
    ]
    lines += ["- " + safe(predicate) for predicate in report.unsupported_predicates]
    lines += ["## Warnings"] + ["- " + safe(warning) for warning in report.warnings]
    lines += ["## Original upload as escaped data", safe(report.original_source_text)]
    lines += [
        "No actions executed. No approval granted. Independent human review PENDING."
    ]
    return "\n".join(lines) + "\n"


def build_response(request: NativeObservationRequest) -> NativeObservationEnvelope:
    report = build_report(request)
    response = NativeObservationEnvelope(
        report=report,
        json_export=export_json(request, report),
        markdown_export=export_markdown(request, report),
    )
    if (
        len(_canonical(response.model_dump(mode="json")).encode("utf-8"))
        > MAX_RESPONSE_BYTES
    ):
        raise NativeObservationError("response_byte_budget")
    return response


def validate_response(
    request: NativeObservationRequest, response
) -> NativeObservationEnvelope:
    raw = (
        response.model_dump(mode="json", warnings=False)
        if isinstance(response, NativeObservationEnvelope)
        else response
    )
    original = _canonical(raw)
    if len(original.encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise NativeObservationError("response_byte_budget")
    validated = NativeObservationEnvelope.model_validate(raw)
    expected = build_response(request)
    if original != _canonical(
        validated.model_dump(mode="json")
    ) or original != _canonical(expected.model_dump(mode="json")):
        raise NativeObservationError("response_or_export_mutation")
    return validated
