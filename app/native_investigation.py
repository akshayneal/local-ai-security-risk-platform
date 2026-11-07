"""Deterministic investigation aid over exact, unreviewed native observations.

This companion never interprets vendor labels as outcomes or joins source rows.
Every display and export is reconstructed from the current source/row/question.
"""

import hashlib
import json
import re
from html import escape
from typing import Literal

from pydantic import StrictBool, StrictInt, StrictStr

from app import native_observations as observations
from app.native_observations import (
    MAX_RESPONSE_BYTES,
    NativeObservationError,
    NativeObservationReport,
    NativeObservationRequest,
    TypedField,
)
from app.support_contracts import SupportModel

ENDPOINT = "/experimental/native-evidence/investigation/v1"
Question = Literal[
    "reported_event", "application_access", "network_blocking", "policy_authorization"
]
QUESTION_TEXT = {
    "reported_event": "What does this supplied network row report, and what is missing?",
    "application_access": "What evidence would establish application access?",
    "network_blocking": "What evidence would establish network-protection blocking?",
    "policy_authorization": "What evidence would establish policy authorization?",
}
ACCOUNT_FIELDS = (
    "InitiatingProcessAccountName",
    "InitiatingProcessAccountDomain",
    "InitiatingProcessAccountSid",
    "InitiatingProcessAccountObjectId",
    "InitiatingProcessUniqueId",
)
TEXT_FIELDS = {
    "ActionType",
    "ResultType",
    "Protocol",
    "RemoteUrl",
    "InitiatingProcessFileName",
    "InitiatingProcessCommandLine",
} | set(ACCOUNT_FIELDS)
COMPARE_FIELDS = (
    "Timestamp",
    "DeviceId",
    "DeviceName",
    "InitiatingProcessId",
    "InitiatingProcessCreationTime",
    "ActionType",
    "ResultType",
    "LocalIP",
    "LocalPort",
    "RemoteIP",
    "RemotePort",
    "Protocol",
)


class NativeInvestigationRequest(NativeObservationRequest):
    question: Question = "reported_event"

    def observation_request(self) -> NativeObservationRequest:
        return NativeObservationRequest.model_validate(
            self.model_dump(mode="json", exclude={"question"})
        )


class TableCoverage(SupportModel):
    table: StrictStr
    row_count: StrictInt
    selected_for_view: StrictBool


class RepresentationComparison(SupportModel):
    field: StrictStr
    selected_path: StrictStr
    other_paths: tuple[StrictStr, ...]
    state: Literal["same_representation", "different_representation", "not_comparable"]
    explanation: StrictStr


class EvidenceGap(SupportModel):
    code: StrictStr
    evidence_kind: StrictStr
    statement: StrictStr
    paths: tuple[StrictStr, ...]


class NextEvidence(SupportModel):
    code: StrictStr
    evidence_kind: StrictStr
    question: StrictStr
    basis_paths: tuple[StrictStr, ...]


class NativeInvestigationReport(SupportModel):
    schema_version: Literal["native-investigation-report/1"] = (
        "native-investigation-report/1"
    )
    request_fingerprint: StrictStr
    question: Question
    question_text: StrictStr
    observation: NativeObservationReport
    snapshot: tuple[TypedField, ...]
    tables: tuple[TableCoverage, ...]
    comparisons: tuple[RepresentationComparison, ...]
    gaps: tuple[EvidenceGap, ...]
    next_evidence: tuple[NextEvidence, ...]
    semantic_decision: Literal["MORE_EVIDENCE_REQUIRED"] = "MORE_EVIDENCE_REQUIRED"
    comparison_scope: Literal[
        "literal/type representation only; no event association"
    ] = "literal/type representation only; no event association"
    capability_status: Literal["experimental_off_by_default"] = (
        "experimental_off_by_default"
    )
    analyst_notes_status: Literal["not_collected"] = "not_collected"


class NativeInvestigationEnvelope(SupportModel):
    report: NativeInvestigationReport
    json_export: StrictStr
    markdown_export: StrictStr


def _canonical(value) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )


def _request(request) -> NativeInvestigationRequest:
    try:
        return NativeInvestigationRequest.model_validate(
            request.model_dump(mode="json", warnings=False)
        )
    except (ValueError, TypeError, AttributeError) as exc:
        raise NativeObservationError("invalid_investigation_request") from exc


def _snapshot_field(row, index, name) -> TypedField:
    field = observations._typed_field(row, index, name)
    if name not in TEXT_FIELDS or not field.present:
        return field
    value = field.original_value
    limit = 256 if name == "ActionType" else 4096
    valid = isinstance(value, str) and bool(value.strip()) and len(value) <= limit
    return field.model_copy(
        update={
            "status": "unverified" if valid else "invalid_shape",
            "normalized_value": value if valid else None,
            "normalization": "identity_text" if valid else "none",
            "reason_code": "bounded_text_shape_semantics_unverified"
            if valid
            else "invalid_text_shape",
        }
    )


def _comparisons(report, snapshot):
    rows = report.original_bundle["tables"]["DeviceNetworkEvents"]
    fields = {field.name: field for field in snapshot}
    result = []
    for name in COMPARE_FIELDS:
        selected = fields[name]
        others = [(i, row) for i, row in enumerate(rows) if i != report.row_index]
        paths = tuple(
            f"DeviceNetworkEvents[{i}].{name}" for i, row in others if name in row
        )
        valid_others = [
            row
            for i, row in others
            if _snapshot_field(row, i, name).status not in {"absent", "invalid_shape"}
        ]
        state = "not_comparable"
        explanation = "No complete set of valid supplied representations for this field across the selected and other rows. Missing or invalid values remain unknown."
        if valid_others and selected.status not in {"absent", "invalid_shape"}:
            same = all(
                _canonical(row[name]) == _canonical(selected.original_value)
                for row in valid_others
            )
            if not same:
                state = "different_representation"
                explanation = "At least one other supplied network row has a different literal value or JSON type; different events may legitimately differ."
            elif len(valid_others) == len(others):
                state = "same_representation"
                explanation = "All other supplied network rows have the same literal value and JSON type."
        incomplete = len(others) - len(valid_others)
        if incomplete:
            explanation += f" {incomplete} other rows have absent or invalid representations and were not compared."
        explanation += " This establishes no causal/process association or contradiction about one real event."
        result.append(
            RepresentationComparison(
                field=name,
                selected_path=selected.expected_path,
                other_paths=paths,
                state=state,
                explanation=explanation,
            )
        )
    return tuple(result)


def _evidence_questions(report, snapshot, question):
    fields = {field.name: field for field in snapshot}
    gaps = [
        EvidenceGap(
            code="source_and_collection_unverified",
            evidence_kind="event",
            statement="Source authenticity, external currentness and collection completeness are unchecked. A missing field or row does not establish that activity never happened.",
            paths=(f"DeviceNetworkEvents[{report.row_index}]",),
        )
    ]
    next_items = []
    families = (
        (
            "event_time",
            "event",
            ("Timestamp",),
            "Obtain the original event timestamp with an explicit timezone and collection context.",
        ),
        (
            "device_context",
            "event",
            ("DeviceId", "DeviceName"),
            "Confirm the selected row's device identifiers against the original collection and asset context.",
        ),
        (
            "process_identity",
            "process_identity",
            ("InitiatingProcessId", "InitiatingProcessCreationTime"),
            "Obtain device-bound process identity and creation time before associating any process records; a shared PID or name alone is insufficient.",
        ),
        (
            "endpoint_context",
            "event",
            ("LocalIP", "LocalPort", "RemoteIP", "RemotePort"),
            "Confirm the same-row local/remote endpoint context, including any proxy or translation; these labels do not establish data-flow direction or application protocol.",
        ),
    )
    for code, kind, names, prompt in families:
        paths = tuple(fields[name].expected_path for name in names)
        missing = tuple(
            fields[name].expected_path
            for name in names
            if fields[name].status in {"absent", "invalid_shape"}
        )
        if missing:
            gaps.append(
                EvidenceGap(
                    code=code + "_incomplete",
                    evidence_kind=kind,
                    statement="Required representations for this context are absent or invalid in the selected row; they cannot be filled from another row.",
                    paths=missing,
                )
            )
        next_items.append(
            NextEvidence(
                code=code,
                evidence_kind=kind,
                question=prompt,
                basis_paths=missing or paths,
            )
        )
    invalid = tuple(
        field.expected_path for field in snapshot if field.status == "invalid_shape"
    )
    if invalid:
        next_items.append(
            NextEvidence(
                code="invalid_representation",
                evidence_kind="event",
                question="Check the original export/schema for the listed malformed values; preserve the supplied originals rather than guessing a replacement.",
                basis_paths=invalid,
            )
        )
    special = {
        "reported_event": (
            "native_outcome_unverified",
            "event",
            "Vendor labels and endpoint shapes do not establish handshake completion, transfer, application access, protection outcome or policy permission.",
            "If an outcome decision is needed, first select its investigation question and seek the corresponding independent evidence.",
        ),
        "application_access": (
            "application_access_unverified",
            "application_access",
            "Application-layer access or data transfer is not established by this row or by the presence of other supplied telemetry tables.",
            "Seek application/server-side request, authentication and transaction records with device/principal/time/resource context before asserting access or transfer. These records have not been checked here.",
        ),
        "network_blocking": (
            "network_protection_unverified",
            "network_protection",
            "A ConnectionSuccess label can coexist with later network-protection blocking. This view has no associated protection disposition evidence.",
            "Seek the relevant network-protection disposition, such as DeviceEvents ExploitGuardNetworkProtectionBlocked or ExploitGuardNetworkProtectionAudited, with collection and association context. DeviceEvents is outside this upload profile and was not supplied, checked or joined here; an audited event alone is not a block.",
        ),
        "policy_authorization": (
            "policy_authority_unavailable",
            "control_policy",
            "No separately controlled current reviewed policy authority or proven event-to-permission association is available. Uploaded approval text cannot grant authorization.",
            "Seek independently controlled current reviewed policy/approval with principal, resource, operation and effective window, plus a proven association contract. This workflow cannot perform that authorization comparison.",
        ),
    }
    code, kind, statement, prompt = special[question]
    paths = tuple(
        fields[name].expected_path for name in ("ActionType", "ResultType", "Protocol")
    )
    gaps.append(
        EvidenceGap(code=code, evidence_kind=kind, statement=statement, paths=paths)
    )
    next_items.append(
        NextEvidence(code=code, evidence_kind=kind, question=prompt, basis_paths=paths)
    )
    if report.coverage.omitted_rows:
        next_items.append(
            NextEvidence(
                code="inspect_other_rows",
                evidence_kind="event",
                question="Inspect other supplied rows separately, including repeated rows or differing representations. Their presence does not establish that they concern this event.",
                basis_paths=tuple(
                    f"{name}[{i}]"
                    for name, rows in sorted(report.original_bundle["tables"].items())
                    for i in range(len(rows))
                    if name != "DeviceNetworkEvents" or i != report.row_index
                ),
            )
        )
    return tuple(gaps), tuple(next_items)


def build_report(request: NativeInvestigationRequest) -> NativeInvestigationReport:
    request = _request(request)
    observation = observations.build_report(request.observation_request())
    row = observation.original_bundle["tables"]["DeviceNetworkEvents"][
        request.row_index
    ]
    snapshot = tuple(
        _snapshot_field(row, request.row_index, name)
        for name in observations.PROFILE_FIELDS + ACCOUNT_FIELDS
    )
    gaps, next_evidence = _evidence_questions(observation, snapshot, request.question)
    return NativeInvestigationReport(
        request_fingerprint=hashlib.sha256(
            _canonical(request.model_dump(mode="json")).encode()
        ).hexdigest(),
        question=request.question,
        question_text=QUESTION_TEXT[request.question],
        observation=observation,
        snapshot=snapshot,
        tables=tuple(
            TableCoverage(
                table=name,
                row_count=len(rows),
                selected_for_view=name == "DeviceNetworkEvents",
            )
            for name, rows in sorted(observation.original_bundle["tables"].items())
        ),
        comparisons=_comparisons(observation, snapshot),
        gaps=gaps,
        next_evidence=next_evidence,
    )


def _validate_report(request, report):
    raw = (
        report.model_dump(mode="json", warnings=False)
        if isinstance(report, NativeInvestigationReport)
        else report
    )
    original = _canonical(raw)
    validated = NativeInvestigationReport.model_validate(raw)
    if original != _canonical(
        validated.model_dump(mode="json")
    ) or original != _canonical(build_report(request).model_dump(mode="json")):
        raise NativeObservationError("investigation_report_or_source_mutation")
    return validated


def export_json(request, report) -> str:
    return json.dumps(
        _validate_report(request, report).model_dump(mode="json"),
        ensure_ascii=True,
        indent=2,
        allow_nan=False,
    )


def _safe(value) -> str:
    return (
        re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", escape(str(value)))
        .replace("\r", " ")
        .replace("\n", " ")
    )


def export_markdown(request, report) -> str:
    report = _validate_report(request, report)
    source = report.observation
    lines = [
        "# Native Evidence Investigation (Experimental)",
        "Unreviewed supplied telemetry. Zero model calls. Independent human review PENDING.",
        "Question: " + report.question_text,
        "Case label: " + _safe(source.case_id),
        "Selected row: " + _safe(source.row_identity),
        "Original byte SHA-256: " + source.source_sha256,
        "Request fingerprint (source, selection and question): "
        + report.request_fingerprint,
        "Currentness: submitted snapshot only; hashes do not authenticate sources.",
        "## Observation — reported event snapshot",
    ]
    for field in report.snapshot:
        lines.append(
            f"- {_safe(field.expected_path)}: {_safe(field.status)}; original {_safe(_canonical(field.original_value))}; type {_safe(field.original_type)}; normalized {_safe(_canonical(field.normalized_value))}; {_safe(field.normalization)}; {_safe(field.reason_code)}"
        )
    lines += ["## Supplied coverage and relevance"]
    lines += [
        f"- {_safe(table.table)}: {table.row_count} supplied rows; selected-row view: {table.selected_for_view}. Presence does not establish corroboration."
        for table in report.tables
    ]
    lines += [
        f"Repeated network rows retained: {source.coverage.duplicate_network_rows}.",
        "## Supported comparison — representation only",
        report.comparison_scope,
    ]
    lines += [
        f"- {_safe(item.selected_path)} versus {_safe(', '.join(item.other_paths) or 'no other supplied field')}: {item.state}. {item.explanation}"
        for item in report.comparisons
    ]
    lines += [
        "## Insufficient evidence",
        "Semantic decision: MORE_EVIDENCE_REQUIRED. Comparator not_executed (0 calls); association not_assessed.",
    ]
    lines += [
        f"- {_safe(item.statement)} Context paths (may be absent): {_safe(', '.join(item.paths))}."
        for item in report.gaps
    ]
    lines += [
        "## Suggested next investigation",
        "Recommended evidence to seek; no integration/source check or action has been performed.",
    ]
    lines += [
        f"- {_safe(item.question)} Basis paths (may be absent): {_safe(', '.join(item.basis_paths))}."
        for item in report.next_evidence
    ]
    lines += [
        "## Unverified analyst notes",
        "Not collected by this workflow.",
        "## Source-bound original observation appendix",
    ]
    # The unchanged v1 appendix also retains unknown fields, exact source, warnings
    # and complete row/field observations. Its exporter independently revalidates.
    lines += [observations.export_markdown(request.observation_request(), source)]
    return "\n\n".join(lines).rstrip("\n") + "\n"


def build_response(request: NativeInvestigationRequest) -> NativeInvestigationEnvelope:
    request = _request(request)
    report = build_report(request)
    envelope = NativeInvestigationEnvelope(
        report=report,
        json_export=export_json(request, report),
        markdown_export=export_markdown(request, report),
    )
    if len(_canonical(envelope.model_dump(mode="json")).encode()) > MAX_RESPONSE_BYTES:
        raise NativeObservationError("response_byte_budget")
    return envelope


def validate_response(
    request: NativeInvestigationRequest, response
) -> NativeInvestigationEnvelope:
    raw = (
        response.model_dump(mode="json", warnings=False)
        if isinstance(response, NativeInvestigationEnvelope)
        else response
    )
    original = _canonical(raw)
    if len(original.encode()) > MAX_RESPONSE_BYTES:
        raise NativeObservationError("response_byte_budget")
    validated = NativeInvestigationEnvelope.model_validate(raw)
    if original != _canonical(
        validated.model_dump(mode="json")
    ) or original != _canonical(build_response(request).model_dump(mode="json")):
        raise NativeObservationError("investigation_response_or_export_mutation")
    return validated
