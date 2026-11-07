"""Prospective execution/association contract; all v1 source stays unchanged.

The baseline is an event-only v1 observation, not a claimed replay of a v1
multi-authorization report. Only the explicit comparison branch invokes a
comparator. Source eligibility still means reviewed synthetic assertions only.
"""

import json
import re
from html import escape
from typing import Literal

from pydantic import Field, StrictBool, StrictInt, StrictStr, model_validator

from app import adaptive_reports
from app import qualified_soc as v1
from app.evidence_qualification import (
    QualificationError,
    QualificationScope,
    SourceReview,
    decode_json,
    instant,
    qualify_source,
)
from app.support_contracts import SupportModel


class CandidateAssociation(SupportModel):
    ordinal: StrictInt = Field(ge=1, le=8)
    source_id: StrictStr
    source_revision: StrictStr
    source_sha256: StrictStr
    state: Literal["complete", "plausible_incomplete", "unrelated"]
    reason_codes: tuple[StrictStr, ...]
    checked_paths: tuple[StrictStr, ...]


class QualifiedSocReportV2(SupportModel):
    schema_version: Literal["qualified-soc-report/2"] = "qualified-soc-report/2"
    case_id: StrictStr
    question_id: StrictStr
    processing_state: Literal[
        "source_refused",
        "observations_projected",
        "association_resolved",
        "comparison_returned",
        "comparison_failed",
    ]
    execution_state: Literal["not_executed", "completed", "failed"]
    comparator_invocations: StrictInt = Field(ge=0, le=1)
    relationship: Literal[
        "declared_alignment",
        "declared_mismatch",
        "underdetermined",
        "conflicting_claims",
        "not_applicable",
        "projection_unavailable",
        "unassessable",
    ]
    association_state: Literal[
        "not_assessed",
        "missing",
        "no_match",
        "incomplete",
        "ambiguous",
        "conflicting",
        "unique",
    ] = "not_assessed"
    reason_codes: tuple[StrictStr, ...]
    sources: tuple[v1.SourceSnapshot, ...] = Field(default=(), max_length=9)
    candidates: tuple[CandidateAssociation, ...] = Field(default=(), max_length=8)
    observations: tuple[v1.Observation, ...] = ()
    lineage: tuple[v1.FieldLineage, ...] = ()
    baseline: v1.QualifiedSocReport
    baseline_provenance: Literal["event_only_v1", "native_v1"]
    comparison: adaptive_reports.AdaptiveReport | None = None
    capability_status: Literal["experimental_internal_off_by_default"] = (
        "experimental_internal_off_by_default"
    )
    source_status: Literal[
        "application reviewed synthetic assertions; authenticity unverified"
    ] = "application reviewed synthetic assertions; authenticity unverified"
    approval_granted: StrictBool = False
    action_status: Literal["no_actions_executed"] = "no_actions_executed"
    independent_review: Literal["PENDING"] = "PENDING"

    @model_validator(mode="after")
    def consistent_stages(self):
        if self.approval_granted is not False:
            raise ValueError("approval_cannot_be_granted")
        if (
            self.case_id != self.baseline.case_id
            or self.question_id != self.baseline.question_id
        ):
            raise ValueError("baseline_case_binding")
        if self.execution_state == "completed":
            if (
                self.comparator_invocations != 1
                or self.comparison is None
                or self.processing_state != "comparison_returned"
                or self.association_state != "unique"
                or self.relationship != self.comparison.assessment.outcome
                or self.relationship == "projection_unavailable"
                or self.comparison.assessment.case_id != self.case_id
                or self.comparison.assessment.pillar != "soc"
                or self.baseline_provenance != "event_only_v1"
            ):
                raise ValueError("completed_comparison_invariant")
        elif self.execution_state == "failed":
            if (
                self.comparator_invocations != 1
                or self.comparison is not None
                or self.processing_state != "comparison_failed"
                or self.relationship != "projection_unavailable"
                or self.association_state != "unique"
                or self.baseline_provenance != "event_only_v1"
            ):
                raise ValueError("failed_comparison_invariant")
        elif (
            self.comparator_invocations != 0
            or self.comparison is not None
            or self.processing_state in {"comparison_returned", "comparison_failed"}
        ):
            raise ValueError("not_executed_invariant")
        if self.baseline.comparison is not None:
            raise ValueError("baseline_must_not_include_comparison")
        if (
            self.baseline.status == "unavailable"
            and self.processing_state != "source_refused"
        ):
            raise ValueError("unavailable_baseline_invariant")
        if self.processing_state == "source_refused" and (
            self.execution_state != "not_executed"
            or self.relationship != "projection_unavailable"
            or self.association_state != "not_assessed"
        ):
            raise ValueError("refusal_invariant")
        if self.processing_state == "observations_projected" and (
            self.baseline_provenance != "native_v1"
            or self.execution_state != "not_executed"
            or self.relationship != "unassessable"
            or self.association_state != "not_assessed"
        ):
            raise ValueError("native_observation_invariant")
        if self.processing_state == "association_resolved":
            expected = (
                "conflicting_claims"
                if self.association_state == "conflicting"
                else "underdetermined"
            )
            if (
                self.execution_state != "not_executed"
                or self.relationship != expected
                or self.association_state
                not in {"missing", "no_match", "incomplete", "ambiguous", "conflicting"}
                or self.baseline_provenance != "event_only_v1"
            ):
                raise ValueError("association_relationship_invariant")
        if self.association_state != "not_assessed":
            if len(self.sources) != len(self.candidates) + 1:
                raise ValueError("candidate_inventory_invariant")
            for ordinal, candidate in enumerate(self.candidates, 1):
                source = self.sources[ordinal]
                if (
                    candidate.ordinal != ordinal
                    or candidate.source_id != source.source_id
                    or candidate.source_revision != source.revision
                    or candidate.source_sha256 != source.raw_sha256
                ):
                    raise ValueError("candidate_source_binding")
            plausible = [
                candidate
                for candidate in self.candidates
                if candidate.state != "unrelated"
            ]
            incomplete = [
                candidate
                for candidate in plausible
                if candidate.state == "plausible_incomplete"
            ]
            valid_association = {
                "missing": not self.candidates,
                "no_match": bool(self.candidates) and not plausible,
                "incomplete": len(plausible) == len(incomplete) == 1,
                "ambiguous": len(plausible) > 1,
                "conflicting": len(plausible) > 1 and not incomplete,
                "unique": len(plausible) == 1 and not incomplete,
            }
            if not valid_association[self.association_state]:
                raise ValueError("candidate_association_state_invariant")
        return self


def _qualify_authorizations(raw_sources, scope, event_source):
    if len(raw_sources) > 8:
        raise QualificationError("authorization_count_bound")
    qualified = []
    seen = {}
    for raw, review in raw_sources:
        source = qualify_source(
            raw,
            review,
            scope,
            expected_role="authorization_assertion",
            expected_format="synthetic_authorization",
        )
        if source.review.source_id == event_source.source_id:
            raise QualificationError("self_asserted_authorization")
        snapshot = source.review.model_dump_json()
        previous = seen.get(source.review.source_id)
        if previous is not None and previous != snapshot:
            raise QualificationError("conflicting_source_snapshot")
        seen[source.review.source_id] = snapshot
        assertion = v1.SyntheticAuthorization.model_validate(decode_json(raw))
        start, end = (
            assertion.authorization.window_start,
            assertion.authorization.window_end,
        )
        for value in (start, end):
            if value is not None:
                instant(value)
        if start is not None and end is not None and instant(start) > instant(end):
            raise QualificationError("inverted_authorization_window")
        qualified.append((source, assertion))
    return qualified


def _association(event, auth, scope, source, ordinal):
    """Known mismatch wins; absent identity is plausible rather than discarded."""
    checks = [
        ("event_id", event.event_id, auth.event_id),
        ("process_id", event.process_id, auth.process_id),
        (
            "process_created_at",
            instant(event.process_created_at),
            instant(auth.process_created_at),
        ),
        (
            "event_time",
            instant(event.event.time) if event.event.time is not None else None,
            instant(auth.event_time),
        ),
        ("question_id", scope.question_id, auth.question_id),
    ]
    checks += [
        (field, getattr(event.event, field), getattr(auth.authorization, field))
        for field in ("principal", "asset", "endpoint")
    ]
    missing = tuple(
        name + "_unknown"
        for name, left, right in checks
        if left is None or right is None
    )
    different = tuple(
        name + "_differs"
        for name, left, right in checks
        if left is not None
        and right is not None
        and (type(left) is not type(right) or left != right)
    )
    state = (
        "unrelated" if different else "plausible_incomplete" if missing else "complete"
    )
    return CandidateAssociation(
        ordinal=ordinal,
        source_id=source.review.source_id,
        source_revision=source.review.revision,
        source_sha256=source.raw_sha256,
        state=state,
        reason_codes=different or missing or ("identity_scope_complete",),
        checked_paths=(
            "/event_id",
            "/process_id",
            "/process_created_at",
            "/event_time",
            "/question_id",
            "/authorization/principal",
            "/authorization/asset",
            "/authorization/endpoint",
        ),
    )


def _applicable_status(event, auth):
    """Only complete known claims concerning this actual operation/instant vote."""
    assertion = auth.authorization
    if (
        event.event.operation is None
        or assertion.operation != event.event.operation
        or assertion.status == "unknown"
        or assertion.window_start is None
        or assertion.window_end is None
        or event.event.time is None
    ):
        return None
    if (
        not instant(assertion.window_start)
        <= instant(event.event.time)
        <= instant(assertion.window_end)
    ):
        return None
    return assertion.status


def _auth_observations(qualified):
    return tuple(
        v1._observation(source, "/" + key, value)
        for source, _ in qualified
        for key, value in decode_json(source.raw_text.encode("utf-8")).items()
    )


def _auth_lineage(source, authorization):
    return tuple(
        v1._lineage(
            source,
            "/data/authorization/" + field,
            "/authorization/" + field,
            state="unknown"
            if value is None or field == "status" and value == "unknown"
            else "unverified",
        )
        for field, value in authorization.model_dump(mode="json").items()
    )


def _resolve_synthetic(baseline, raw, scope, raw_authorizations):
    qualified = _qualify_authorizations(raw_authorizations, scope, baseline.sources[0])
    event = v1.SyntheticEvent.model_validate(decode_json(raw))
    candidates = tuple(
        _association(event, auth, scope, source, index)
        for index, (source, auth) in enumerate(qualified, 1)
    )
    common = {
        "case_id": baseline.case_id,
        "question_id": baseline.question_id,
        "baseline": baseline,
        "baseline_provenance": "event_only_v1",
        "sources": baseline.sources
        + tuple(v1._snapshot(source) for source, _ in qualified),
        "observations": baseline.observations + _auth_observations(qualified),
        "lineage": baseline.lineage,
        "candidates": candidates,
    }
    plausible = [
        candidate for candidate in candidates if candidate.state != "unrelated"
    ]
    partial = [
        candidate
        for candidate in plausible
        if candidate.state == "plausible_incomplete"
    ]
    if not plausible:
        state = "missing" if not candidates else "no_match"
        reason = (
            "eligible_authorization_not_supplied"
            if not candidates
            else "association_not_established"
        )
    elif partial:
        state = "incomplete" if len(plausible) == 1 else "ambiguous"
        reason = (
            "plausible_identity_incomplete"
            if state == "incomplete"
            else "plausible_competitor_incomplete"
        )
    elif len(plausible) > 1:
        statuses = {
            _applicable_status(event, qualified[candidate.ordinal - 1][1])
            for candidate in plausible
        }
        conflict = {"reported_authorized", "reported_denied"} <= statuses
        state = "conflicting" if conflict else "ambiguous"
        reason = (
            "opposed_complete_applicable_assertions"
            if conflict
            else "multiple_plausible_authorizations"
        )
    else:
        candidate = plausible[0]
        source, auth = qualified[candidate.ordinal - 1]
        common["lineage"] += _auth_lineage(source, auth.authorization)
        # This is the sole comparator dispatch in the v2 path. Increment before
        # invocation so an exception cannot masquerade as no attempt.
        try:
            comparison = v1._comparison(event, auth.authorization, scope)
            comparison = adaptive_reports.AdaptiveReport.model_validate(
                comparison.model_dump(mode="json")
            )
            if comparison.assessment.outcome == "projection_unavailable":
                return QualifiedSocReportV2(
                    **common,
                    processing_state="comparison_failed",
                    execution_state="failed",
                    comparator_invocations=1,
                    relationship="projection_unavailable",
                    association_state="unique",
                    reason_codes=("comparator_projection_unavailable",)
                    + comparison.assessment.reason_codes,
                )
        except (
            ValueError,
            TypeError,
            AttributeError,
            RuntimeError,
            RecursionError,
            LookupError,
        ):
            return QualifiedSocReportV2(
                **common,
                processing_state="comparison_failed",
                execution_state="failed",
                comparator_invocations=1,
                relationship="projection_unavailable",
                association_state="unique",
                reason_codes=("comparator_failed",),
            )
        return QualifiedSocReportV2(
            **common,
            processing_state="comparison_returned",
            execution_state="completed",
            comparator_invocations=1,
            relationship=comparison.assessment.outcome,
            association_state="unique",
            reason_codes=comparison.assessment.reason_codes,
            comparison=comparison,
        )
    return QualifiedSocReportV2(
        **common,
        processing_state="association_resolved",
        execution_state="not_executed",
        comparator_invocations=0,
        relationship="conflicting_claims"
        if state == "conflicting"
        else "underdetermined",
        association_state=state,
        reason_codes=(reason,),
    )


def build_qualified_report(
    raw: bytes,
    review: SourceReview,
    scope: QualificationScope,
    *,
    authorization_sources: tuple[tuple[bytes, SourceReview], ...] = (),
    row_index: int = 0,
    csv_table: str = "DeviceNetworkEvents",
    csv_case_id: str | None = None,
) -> QualifiedSocReportV2:
    """Derive an internal v2 report without changing or rescoring v1 history."""
    options = {
        "row_index": row_index,
        "csv_table": csv_table,
        "csv_case_id": csv_case_id,
    }
    baseline = v1.build_qualified_report(raw, review, scope, **options)
    provenance = "event_only_v1"
    if baseline.sources and baseline.sources[0].source_format in {
        "microsoft_json",
        "microsoft_csv",
    }:
        provenance = "native_v1"
        baseline = v1.build_qualified_report(
            raw, review, scope, authorization_sources=authorization_sources, **options
        )
    common = {
        "case_id": baseline.case_id,
        "question_id": baseline.question_id,
        "baseline": baseline,
        "baseline_provenance": provenance,
        "sources": baseline.sources,
        "observations": baseline.observations,
        "lineage": baseline.lineage,
        "execution_state": "not_executed",
        "comparator_invocations": 0,
    }
    if baseline.status == "unavailable":
        return QualifiedSocReportV2(
            **common,
            processing_state="source_refused",
            relationship="projection_unavailable",
            reason_codes=baseline.reason_codes,
        )
    if provenance == "native_v1":
        return QualifiedSocReportV2(
            **common,
            processing_state="observations_projected",
            relationship="unassessable",
            reason_codes=baseline.reason_codes,
        )
    try:
        # The baseline revalidated scope; use that exact bound scope rather than
        # trusting a possibly mutated caller object again.
        return _resolve_synthetic(
            baseline, raw, baseline.sources[0].scope, authorization_sources
        )
    except QualificationError as exc:
        code = exc.code
    except (ValueError, TypeError, AttributeError, UnicodeError):
        code = "malformed_authorization_context"
    return QualifiedSocReportV2(
        **common,
        processing_state="source_refused",
        relationship="projection_unavailable",
        reason_codes=(code,),
    )


def _validated(raw, review, scope, report, kwargs):
    original = report.model_dump_json(warnings=False)
    validated = QualifiedSocReportV2.model_validate(
        report.model_dump(mode="json", warnings=False)
    )
    expected = build_qualified_report(raw, review, scope, **kwargs)
    if (
        original != validated.model_dump_json()
        or original != expected.model_dump_json()
    ):
        raise ValueError("canonical_v2_report_or_snapshot_mutation")
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
        return (
            re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", escape(str(value)))
            .replace("\r", " ")
            .replace("\n", " ")
            .rstrip()
        )

    lines = [
        "# Experimental qualified SOC contract v2",
        "Execution: "
        + safe(report.execution_state)
        + "; comparator calls: "
        + str(report.comparator_invocations),
        "Processing: " + safe(report.processing_state),
        "Relationship: " + safe(report.relationship),
        "Association: " + safe(report.association_state),
        "Reasons: " + safe(", ".join(report.reason_codes)),
        "Baseline provenance: " + safe(report.baseline_provenance),
        "The baseline is a v1 observation path, not an original aggregate v1 comparison report.",
        "Application review supplies synthetic eligibility only; authenticity and live permission remain unverified.",
        "## Original sources and reviewed eligibility",
    ]
    for ordinal, source in enumerate(report.sources):
        lines += [
            f"Source ordinal {ordinal}: "
            + safe(source.source_id)
            + " revision "
            + safe(source.revision),
            safe(source.review.model_dump_json()),
            safe(source.scope.model_dump_json()),
            safe(source.raw_text),
        ]
    lines += ["## Association evidence"] + [
        safe(candidate.model_dump_json()) for candidate in report.candidates
    ]
    lines += ["## Field lineage"] + [
        safe(item.model_dump_json()) for item in report.lineage
    ]
    if report.comparison is not None:
        lines += [
            "## Derived synthetic comparison",
            safe(report.comparison.assessment.report_sentence),
        ]
    lines += [
        "No actions executed. No approval granted. Independent human review PENDING."
    ]
    return "\n".join(lines) + "\n"
