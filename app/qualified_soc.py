"""Internal synthetic qualification slice; no analyzer, model, or action route.

Native Microsoft rows are observations. Their ActionType is deliberately not
translated into the synthetic comparator's operation or completion predicates.
"""

import json
import re
from html import escape
from typing import Annotated, Any, Literal

from pydantic import Field, StrictInt, StrictStr, ValidationError, field_validator

from app import adaptive_reports, adaptive_semantics
from app.evidence_qualification import (
    QualificationError,
    QualificationScope,
    QualifiedSource,
    SourceReview,
    decode_json,
    qualify_source,
)
from app.evidence_qualification import (
    instant as _instant,
)
from app.soc_inputs import (
    MicrosoftSocAdapter,
    SocInputError,
    canonical_bundle,
    parse_csv_bundle,
    parse_json_bundle,
)
from app.support_contracts import SupportModel

Text = Annotated[StrictStr, Field(min_length=1, max_length=256)]
Identifier = Annotated[StrictStr, Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")]


class SyntheticEvent(SupportModel):
    schema_version: Literal["qualified-event/1"]
    event_id: Identifier
    process_id: Annotated[StrictInt, Field(ge=0, le=2**32 - 1)]
    process_created_at: Text
    event: adaptive_semantics.Event
    annotations: tuple[Annotated[StrictStr, Field(max_length=500)], ...] = Field(
        default=(), max_length=8
    )

    @field_validator("process_created_at")
    @classmethod
    def aware_creation(cls, value):
        _instant(value)
        return value


class SyntheticAuthorization(SupportModel):
    schema_version: Literal["qualified-authorization/1"]
    event_id: Identifier
    process_id: Annotated[StrictInt, Field(ge=0, le=2**32 - 1)]
    process_created_at: Text
    event_time: Text
    question_id: Identifier
    authorization: adaptive_semantics.Authorization

    @field_validator("process_created_at", "event_time")
    @classmethod
    def aware_time(cls, value):
        _instant(value)
        return value


class SourceSnapshot(SupportModel):
    source_id: StrictStr
    revision: StrictStr
    role: StrictStr
    source_format: StrictStr
    source_path: StrictStr
    raw_sha256: StrictStr
    raw_text: StrictStr
    review: SourceReview
    scope: QualificationScope
    assertion_status: Literal["supplied_unverified"] = "supplied_unverified"
    eligibility_status: Literal["application_reviewed_synthetic_only"] = (
        "application_reviewed_synthetic_only"
    )


class Observation(SupportModel):
    source_id: StrictStr
    source_revision: StrictStr
    original_path: StrictStr
    value: Any
    original_type: StrictStr
    semantic_status: Literal["supplied_unverified"] = "supplied_unverified"


class FieldLineage(SupportModel):
    target_path: StrictStr
    source_id: StrictStr | None
    source_revision: StrictStr | None
    original_path: StrictStr | None
    state: Literal["unverified", "unknown", "not_supplied", "not_applicable"]
    transformation: StrictStr


class Coverage(SupportModel):
    total_rows: StrictInt = 0
    selected_rows: StrictInt = 0
    omitted_rows: StrictInt = 0
    unsupported_rows: StrictInt = 0
    invalid_fields: tuple[StrictStr, ...] = ()
    unknown_fields: tuple[StrictStr, ...] = ()


class QualifiedSocReport(SupportModel):
    schema_version: Literal["qualified-soc-report/1"] = "qualified-soc-report/1"
    case_id: StrictStr
    question_id: StrictStr
    status: Literal["assessed", "unassessable", "unavailable", "conflicting"]
    relationship: Literal[
        "declared_alignment",
        "declared_mismatch",
        "underdetermined",
        "conflicting_claims",
        "not_applicable",
        "projection_unavailable",
        "unassessable",
    ]
    reason_codes: tuple[StrictStr, ...]
    association_status: Literal[
        "not_assessed", "missing", "no_match", "associated", "ambiguous", "conflicting"
    ] = "not_assessed"
    sources: tuple[SourceSnapshot, ...] = ()
    canonical_bundle: StrictStr | None = None
    original_bundle: dict | None = None
    observations: tuple[Observation, ...] = ()
    lineage: tuple[FieldLineage, ...] = ()
    coverage: Coverage = Coverage()
    comparison: adaptive_reports.AdaptiveReport | None = None
    comparator_source_status: Literal["not_used", "derived_synthetic_projection"] = (
        "not_used"
    )
    capability_status: Literal["experimental_internal_off_by_default"] = (
        "experimental_internal_off_by_default"
    )
    source_authenticity: Literal["unverified; hashes do not authenticate"] = (
        "unverified; hashes do not authenticate"
    )
    approval_granted: Literal[False] = False
    action_status: Literal["no_actions_executed"] = "no_actions_executed"
    independent_review: Literal["PENDING"] = "PENDING"


def _snapshot(source: QualifiedSource) -> SourceSnapshot:
    return SourceSnapshot(
        source_id=source.review.source_id,
        revision=source.review.revision,
        role=source.review.role,
        source_format=source.review.source_format,
        source_path=source.review.source_path,
        raw_sha256=source.raw_sha256,
        raw_text=source.raw_text,
        review=source.review,
        scope=source.scope,
    )


def _observation(source, path, value):
    return Observation(
        source_id=source.review.source_id,
        source_revision=source.review.revision,
        original_path=path,
        value=value,
        original_type=type(value).__name__,
    )


def _lineage(
    source, target, original, *, state="unverified", transformation="identity"
):
    return FieldLineage(
        target_path=target,
        source_id=source.review.source_id if source else None,
        source_revision=source.review.revision if source else None,
        original_path=original,
        state=state,
        transformation=transformation,
    )


def _native(source, scope, row_index, csv_table, csv_case_id):
    raw = source.raw_text.encode("utf-8")
    if source.review.source_format == "microsoft_json":
        decode_json(raw, allow_finite_floats=True)
        bundle = parse_json_bundle(raw)
    else:
        bundle = parse_csv_bundle(raw, csv_table, csv_case_id or scope.case_id)
        # The CSV parser keeps strings exact. A JSON-shaped cell is never decoded.
        decode_json(canonical_bundle(bundle).encode("utf-8"), allow_finite_floats=True)
    normalized = MicrosoftSocAdapter().normalize(bundle)
    if bundle["case_id"] != scope.case_id:
        raise QualificationError("case_scope_mismatch")
    rows = bundle["tables"].get("DeviceNetworkEvents", [])
    if type(row_index) is not int or not 0 <= row_index < len(rows):
        raise QualificationError("selected_row_unavailable")
    row = rows[row_index]
    observations = tuple(
        _observation(source, f"{o.table}[{o.row}].{o.field}", o.value)
        for o in normalized.observations
    )
    invalid = []
    for field in ("InitiatingProcessId", "ProcessId", "LocalPort", "RemotePort"):
        if field in row:
            value = row[field]
            # CSV numbers remain string assertions with explicit parsing only.
            valid = type(value) is int or (
                isinstance(value, str) and re.fullmatch(r"[0-9]{1,10}", value)
            )
            limit = 65535 if field.endswith("Port") else 2**32 - 1
            if not valid or not 0 <= int(value) <= limit:
                invalid.append(f"DeviceNetworkEvents[{row_index}].{field}")
    for field in ("Timestamp", "InitiatingProcessCreationTime"):
        if field in row:
            try:
                _instant(row[field])
            except (TypeError, ValueError):
                invalid.append(f"DeviceNetworkEvents[{row_index}].{field}")
    total = sum(normalized.row_counts.values())
    coverage = Coverage(
        total_rows=total,
        selected_rows=1,
        omitted_rows=total - 1,
        unsupported_rows=total - len(rows),
        invalid_fields=tuple(invalid),
        unknown_fields=tuple(
            f"DeviceNetworkEvents[{row_index}].{name}"
            for name in (
                "Timestamp",
                "InitiatingProcessId",
                "InitiatingProcessCreationTime",
            )
            if name not in row
        ),
    )
    lineage = tuple(
        _lineage(
            None,
            "/event/" + name,
            None,
            state=state,
            transformation="not mapped: native field semantics do not establish this predicate",
        )
        for name, state in (
            ("operation", "unknown"),
            ("result", "unknown"),
            ("source", "not_applicable"),
            ("destination", "not_applicable"),
            ("amount", "not_supplied"),
        )
    )
    return bundle, observations, coverage, lineage


def _associated(event, auth, scope):
    if event.event.time is None:
        return False
    if any(
        getattr(event.event, field) is None
        for field in ("principal", "asset", "endpoint")
    ):
        return False
    return (
        event.event_id == auth.event_id
        and event.process_id == auth.process_id
        and _instant(event.process_created_at) == _instant(auth.process_created_at)
        and _instant(event.event.time) == _instant(auth.event_time)
        and auth.question_id == scope.question_id
        and all(
            getattr(event.event, field) == getattr(auth.authorization, field)
            for field in ("principal", "asset", "endpoint")
        )
    )


def _comparison(event, authorization, scope):
    envelope = {
        "schema_version": "adaptive-security/1",
        "case_id": scope.case_id,
        "pillar": "soc",
        "source": {"id": "DERIVED_PROJECTION", "revision": "derived-1"},
        "data": {
            "event": event.event.model_dump(mode="json"),
            "authorization": authorization.model_dump(mode="json"),
        },
        "counterclaims": [],
        "annotations": [],
    }
    raw = json.dumps(envelope, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    context = adaptive_semantics.ReviewedContext(
        case_id=scope.case_id,
        pillar="soc",
        input_path="raw_log",
        raw_sha256=adaptive_semantics.sha(raw),
        requirement_reviewed=True,
        sources=(
            adaptive_semantics.ReviewedSource(
                id="DERIVED_PROJECTION",
                revision="derived-1",
                scope=scope.case_id,
                classification="public_synthetic",
                authority="synthetic_caller_assertion",
                current=True,
            ),
        ),
    )
    return adaptive_reports.build_report(raw, context)


def _contradictory(event, associated, scope):
    """Different incomplete contexts are ambiguous, not automatically contrary."""
    authorizations = [auth.authorization for _, auth in associated]
    statuses = {auth.status for auth in authorizations if auth.status != "unknown"}
    operations = {
        auth.operation for auth in authorizations if auth.operation is not None
    }
    if len(statuses) > 1 or len(operations) > 1:
        return True
    outcomes = {
        _comparison(event, auth, scope).assessment.outcome for auth in authorizations
    }
    return {"declared_alignment", "declared_mismatch"} <= outcomes


def build_qualified_report(
    raw: bytes,
    review: SourceReview,
    scope: QualificationScope,
    *,
    authorization_sources: tuple[tuple[bytes, SourceReview], ...] = (),
    row_index: int = 0,
    csv_table: str = "DeviceNetworkEvents",
    csv_case_id: str | None = None,
) -> QualifiedSocReport:
    """Revalidate application reviews and exact bytes on every call; no fallback.

    Synthetic event and authorization inputs are separate sources. A qualified
    source is still an assertion, never proof that any real permission exists.
    """
    base = {"case_id": "unavailable", "question_id": "unavailable"}
    snapshots = []
    try:
        scope = QualificationScope.model_validate(scope.model_dump(mode="json"))
        base = {"case_id": scope.case_id, "question_id": scope.question_id}
        if scope.workflow != "soc_investigation":
            raise QualificationError("unsupported_soc_workflow")
        source = qualify_source(
            raw,
            review,
            scope,
            expected_role="event_observation",
            expected_format=review.source_format,
        )
        if review.source_format not in {
            "microsoft_json",
            "microsoft_csv",
            "synthetic_event",
        }:
            raise QualificationError("unsupported_source_format")
        snapshots.append(_snapshot(source))
        if len(authorization_sources) > 8:
            raise QualificationError("authorization_count_bound")
        qualified = []
        seen_sources = {}
        for auth_raw, auth_review in authorization_sources:
            auth_source = qualify_source(
                auth_raw,
                auth_review,
                scope,
                expected_role="authorization_assertion",
                expected_format="synthetic_authorization",
            )
            if auth_source.review.source_id == source.review.source_id:
                raise QualificationError("self_asserted_authorization")
            identity = (auth_source.review.revision, auth_source.raw_sha256)
            previous = seen_sources.get(auth_source.review.source_id)
            if previous is not None and previous != identity:
                raise QualificationError("conflicting_source_identity")
            seen_sources[auth_source.review.source_id] = identity
            auth = SyntheticAuthorization.model_validate(decode_json(auth_raw))
            for value in (
                auth.authorization.window_start,
                auth.authorization.window_end,
            ):
                if value is not None:
                    _instant(value)
            if (
                auth.authorization.window_start is not None
                and auth.authorization.window_end is not None
                and _instant(auth.authorization.window_start)
                > _instant(auth.authorization.window_end)
            ):
                raise QualificationError("inverted_authorization_window")
            qualified.append((auth_source, auth))
            snapshots.append(_snapshot(auth_source))
        if review.source_format in {"microsoft_json", "microsoft_csv"}:
            bundle, observations, coverage, lineage = _native(
                source, scope, row_index, csv_table, csv_case_id
            )
            return QualifiedSocReport(
                **base,
                status="unassessable",
                relationship="unassessable",
                reason_codes=("unsupported_native_operation_outcome",)
                + (
                    ("invalid_native_field_semantics",)
                    if coverage.invalid_fields
                    else ()
                ),
                sources=tuple(snapshots),
                canonical_bundle=canonical_bundle(bundle),
                original_bundle=bundle,
                observations=observations,
                coverage=coverage,
                lineage=lineage,
            )
        original_event = decode_json(raw)
        event = SyntheticEvent.model_validate(original_event)
        if event.event.time is not None:
            _instant(event.event.time)
            if _instant(event.process_created_at) > _instant(event.event.time):
                raise QualificationError("process_created_after_event")
        event_dump = event.model_dump(mode="json")
        observations = tuple(
            _observation(source, "/" + key, event_dump[key])
            for key in (
                "schema_version",
                "event_id",
                "process_id",
                "process_created_at",
                "annotations",
            )
            if key in original_event
        ) + tuple(
            _observation(source, "/event/" + key, value)
            for key, value in event_dump["event"].items()
        )
        coverage = Coverage(total_rows=1, selected_rows=1)
        lineage = tuple(
            _lineage(
                source,
                "/data/event/" + key,
                "/event/" + key,
                state="unknown"
                if value is None or key == "result" and value == "unknown"
                else "unverified",
            )
            for key, value in event_dump["event"].items()
        )
        observations += tuple(
            _observation(auth_source, "/" + key, value)
            for auth_source, auth in qualified
            for key, value in decode_json(auth_source.raw_text.encode("utf-8")).items()
        )
        shared = {
            **base,
            "sources": tuple(snapshots),
            "observations": observations,
            "coverage": coverage,
            "lineage": lineage,
        }
        if not qualified:
            return QualifiedSocReport(
                **shared,
                status="unassessable",
                relationship="underdetermined",
                reason_codes=("eligible_authorization_not_supplied",),
                association_status="missing",
            )
        associated = [(s, a) for s, a in qualified if _associated(event, a, scope)]
        if not associated:
            return QualifiedSocReport(
                **shared,
                status="unassessable",
                relationship="underdetermined",
                reason_codes=("association_not_established",),
                association_status="no_match",
            )
        if len(associated) > 1:
            contradictory = _contradictory(event, associated, scope)
            return QualifiedSocReport(
                **shared,
                status="conflicting" if contradictory else "unassessable",
                relationship="conflicting_claims"
                if contradictory
                else "underdetermined",
                reason_codes=(
                    "conflicting_eligible_authorizations"
                    if contradictory
                    else "ambiguous_authorization_association",
                ),
                association_status="conflicting" if contradictory else "ambiguous",
            )
        auth_source, auth = associated[0]
        comparison = _comparison(event, auth.authorization, scope)
        auth_lineage = tuple(
            _lineage(
                auth_source,
                "/data/authorization/" + field,
                "/authorization/" + field,
                state="unknown"
                if value is None or field == "status" and value == "unknown"
                else "unverified",
            )
            for field, value in auth.authorization.model_dump(mode="json").items()
        )
        shared["lineage"] = lineage + auth_lineage
        outcome = comparison.assessment.outcome
        return QualifiedSocReport(
            **shared,
            status="assessed" if outcome.startswith("declared_") else "unassessable",
            relationship=outcome,
            reason_codes=comparison.assessment.reason_codes,
            association_status="associated",
            comparison=comparison,
            comparator_source_status="derived_synthetic_projection",
        )
    except QualificationError as exc:
        code = exc.code
    except (
        SocInputError,
        ValidationError,
        ValueError,
        TypeError,
        AttributeError,
        UnicodeError,
    ):
        code = "malformed_or_unknown_semantics"
    return QualifiedSocReport(
        **base,
        status="unavailable",
        relationship="projection_unavailable",
        reason_codes=(code,),
    )


def _validated(raw, review, scope, report, kwargs):
    # JSON serialization preserves literal types (unlike Python True == 1).
    original_json = report.model_dump_json()
    validated = QualifiedSocReport.model_validate(report.model_dump(mode="json"))
    expected = build_qualified_report(raw, review, scope, **kwargs)
    if (
        original_json != validated.model_dump_json()
        or original_json != expected.model_dump_json()
    ):
        raise ValueError("canonical_report_or_source_snapshot_mutation")
    return validated


def export_json(raw, review, scope, report, **kwargs) -> str:
    return json.dumps(
        _validated(raw, review, scope, report, kwargs).model_dump(mode="json"),
        ensure_ascii=True,
        indent=2,
    )


def export_markdown(raw, review, scope, report, **kwargs) -> str:
    report = _validated(raw, review, scope, report, kwargs)

    def safe(value):
        return re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", escape(str(value))).replace(
            "\n", " "
        ).replace("\r", " ")

    lines = [
        "# Experimental qualified SOC observation",
        f"Status: {safe(report.status)}; relationship: {safe(report.relationship)}.",
        "Reasons: " + safe(", ".join(report.reason_codes)),
        "Application review establishes synthetic evidence eligibility only.",
        "All source assertions remain unverified. Hashes do not authenticate sources.",
        f"Association: {safe(report.association_status)}.",
        "## Source snapshots",
    ]
    for source in report.sources:
        lines += [
            f"- {safe(source.source_id)} revision {safe(source.revision)}; {safe(source.raw_sha256)}",
            safe(source.raw_text),
        ]
    lines += [
        "## Coverage",
        safe(report.coverage.model_dump_json()),
        "## Field lineage",
    ]
    lines += [safe(item.model_dump_json()) for item in report.lineage]
    if report.comparison is not None:
        lines += [
            "## Derived synthetic comparison",
            "Comparator premise identities belong to the derived envelope; original sources are bound by the field lineage above.",
            safe(report.comparison.assessment.report_sentence),
        ]
    lines += [
        "No actions executed. No approval granted. Independent human review PENDING."
    ]
    return "\n".join(lines) + "\n"
