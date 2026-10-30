"""Request-local evidence provenance and explicit unassessed model claims."""

import hashlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, StrictInt, model_validator

from app.microsoft_evidence import microsoft_evidence
from app.retrieval.contracts import EvidenceRecord, RetrievalQuery
from app.retrieval.filtering import filter_records
from app.retrieval.importers import LEGACY_WORKFLOWS, load_curated_records
from app.schemas import GovernanceRiskRequest, SocAlertRequest
from app.support_assessor import source_provenance
from app.support_contracts import (
    AssessmentOrigin,
    ClaimKind,
    EvidenceSupportAssessment,
    Relationship,
    SourceSupportProvenance,
    SupportModel,
)

MAX_INSPECTED_CLAIMS = 60
MAX_EXCERPT = 600


def fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class InspectorSource(SupportModel):
    provenance: SourceSupportProvenance
    cited: bool
    excerpt: str = Field(max_length=MAX_EXCERPT)
    excerpt_truncated: bool


class InputInventoryRow(SupportModel):
    observation_id: str
    table: str
    row_index: int | None
    field_names: tuple[str, ...]
    status: Literal["supplied field inventory; values not reproduced"] = (
        "supplied field inventory; values not reproduced"
    )


class InspectorClaim(SupportModel):
    claim_id: str
    response_field: str
    kind: ClaimKind
    text: str = Field(max_length=4096)
    text_truncated: bool
    assessment: EvidenceSupportAssessment


class SuppliedFieldAnchor(SupportModel):
    evidence_id: str
    request_sha256: str
    table: str
    row_index: StrictInt = Field(ge=0)
    field_name: str
    parent_observation_id: str
    value_presence: Literal["empty", "nonempty"]
    provenance: Literal["supplied field; not independently verified"] = (
        "supplied field; not independently verified"
    )


class EvidenceInspectorReport(SupportModel):
    inspector_id: str
    request_sha256: str
    query_sha256: str | None
    workflow: Literal["soc_alert", "governance"]
    retrieval_status: Literal["captured", "not_observed", "unavailable", "partial"]
    sources: tuple[InspectorSource, ...] = ()
    input_inventory: tuple[InputInventoryRow, ...] = ()
    field_anchors: tuple[SuppliedFieldAnchor, ...] = ()
    claims: tuple[InspectorClaim, ...] = ()
    total_claims: int
    evidence_gaps: tuple[str, ...] = ()
    review_required: Literal[True] = True
    limitations: tuple[str, ...] = (
        "Retrieved guidance is not binding policy; a requirement is not evidence it is implemented.",
        "Model assertions are unassessed. Citations and source eligibility do not prove claim entailment.",
        "Input inventory shows supplied fields and row provenance, not verified event truth or complete forensic coverage.",
    )

    @model_validator(mode="after")
    def field_paths_match_inventory(self):
        rows = {r.observation_id: r for r in self.input_inventory}
        seen = set()
        for anchor in self.field_anchors:
            row = rows.get(anchor.parent_observation_id)
            if (
                self.workflow != "soc_alert"
                or row is None
                or anchor.request_sha256 != self.request_sha256
                or anchor.table != row.table
                or anchor.row_index != row.row_index
                or anchor.field_name not in row.field_names
                or anchor.parent_observation_id
                != fingerprint([self.request_sha256, anchor.table, anchor.row_index])
                or anchor.evidence_id
                != fingerprint(
                    [
                        self.request_sha256,
                        anchor.table,
                        anchor.row_index,
                        anchor.field_name,
                        "supplied-field-v1",
                    ]
                )
                or anchor.evidence_id in seen
            ):
                raise ValueError(
                    "Field anchors must match this request's supplied row/field inventory"
                )
            seen.add(anchor.evidence_id)
        return self


class AnalystEvidenceReview(SupportModel):
    inspector_id: str
    claim_id: str
    relationship: Relationship
    evidence_ids: tuple[str, ...] = ()
    note: str = Field(default="", max_length=1000)
    provenance: Literal["analyst_recorded"] = "analyst_recorded"
    verification_status: Literal["not_verified"] = "not_verified"
    reviewer_identity: Literal[
        "local user entry; identity not independently authenticated"
    ] = "local user entry; identity not independently authenticated"


class CorrectionCategory(StrEnum):
    FACT = "Unsupported factual claim"
    INCIDENT = "Unsupported incident inference"
    AUTHORITY = "Incorrect policy/authority claim"
    IMPLEMENTATION = "Incorrect implementation/compliance claim"
    EVIDENCE = "Missing or mischaracterized evidence"
    OTHER = "Other clarification"


class AnalystCorrection(SupportModel):
    inspector_id: str
    claim_id: str
    original_response_field: str
    original_claim_fingerprint: str
    correction_id: str
    revision_id: str
    revision: StrictInt = Field(ge=1)
    supersedes_revision_id: str | None
    category: CorrectionCategory
    proposed_text: str = Field(min_length=1, max_length=4096)
    rationale: str = Field(min_length=1, max_length=2000)
    evidence_ids: tuple[str, ...] = ()
    provenance: Literal["analyst_recorded"] = "analyst_recorded"
    verification_status: Literal["not_verified"] = "not_verified"
    reviewer_identity: Literal[
        "local user entry; identity not independently authenticated"
    ] = "local user entry; identity not independently authenticated"

    @model_validator(mode="after")
    def validate_content(self):
        if not self.proposed_text.strip() or not self.rationale.strip():
            raise ValueError("Correction wording and rationale must be nonblank")
        if self.revision_id != fingerprint(
            self.model_dump(mode="json", exclude={"revision_id"})
        ):
            raise ValueError("Correction revision fingerprint does not match")
        return self


def validate_correction_history(
    report: EvidenceInspectorReport, history: tuple[AnalystCorrection, ...]
) -> tuple[AnalystCorrection, ...]:
    report = EvidenceInspectorReport.model_validate(report.model_dump(mode="json"))
    claims = {c.claim_id: c for c in report.claims}
    allowed = (
        {s.provenance.evidence_id for s in report.sources}
        | {r.observation_id for r in report.input_inventory}
        | {a.evidence_id for a in report.field_anchors}
    )
    latest: dict[str, AnalystCorrection] = {}
    for item in history:
        item = AnalystCorrection.model_validate(item.model_dump(mode="json"))
        claim = claims.get(item.claim_id)
        if (
            item.inspector_id != report.inspector_id
            or claim is None
            or item.original_response_field != claim.response_field
            or item.original_claim_fingerprint
            != fingerprint(claim.model_dump(mode="json"))
            or item.correction_id
            != fingerprint(
                [report.inspector_id, item.claim_id, "analyst-correction-v1"]
            )
            or not set(item.evidence_ids) <= allowed
        ):
            raise ValueError("Correction must bind to this claim and eligible evidence")
        previous = latest.get(item.claim_id)
        if item.revision != (previous.revision + 1 if previous else 1) or (
            item.supersedes_revision_id != (previous.revision_id if previous else None)
        ):
            raise ValueError("Correction revisions must form one ordered claim lineage")
        latest[item.claim_id] = item
    return history


def append_analyst_correction(
    report: EvidenceInspectorReport,
    history: tuple[AnalystCorrection, ...],
    *,
    claim_id: str,
    category: CorrectionCategory,
    proposed_text: str,
    rationale: str,
    evidence_ids: tuple[str, ...] = (),
) -> tuple[AnalystCorrection, ...]:
    validate_correction_history(report, history)
    claim = next((c for c in report.claims if c.claim_id == claim_id), None)
    if claim is None:
        raise ValueError("Unknown claim in this Inspector result")
    previous = next((r for r in reversed(history) if r.claim_id == claim_id), None)
    payload = {
        "inspector_id": report.inspector_id,
        "claim_id": claim_id,
        "original_response_field": claim.response_field,
        "original_claim_fingerprint": fingerprint(claim.model_dump(mode="json")),
        "correction_id": fingerprint(
            [report.inspector_id, claim_id, "analyst-correction-v1"]
        ),
        "revision": previous.revision + 1 if previous else 1,
        "supersedes_revision_id": previous.revision_id if previous else None,
        "category": category,
        "proposed_text": proposed_text,
        "rationale": rationale,
        "evidence_ids": evidence_ids,
        "provenance": "analyst_recorded",
        "verification_status": "not_verified",
        "reviewer_identity": "local user entry; identity not independently authenticated",
    }
    item = AnalystCorrection(**payload, revision_id=fingerprint(payload))
    return validate_correction_history(report, (*history, item))


def validate_analyst_review(
    report: EvidenceInspectorReport, review: AnalystEvidenceReview
) -> AnalystEvidenceReview:
    claims = {c.claim_id for c in report.claims}
    evidence = {s.provenance.evidence_id for s in report.sources} | {
        r.observation_id for r in report.input_inventory
    }
    if (
        review.inspector_id != report.inspector_id
        or review.claim_id not in claims
        or not set(review.evidence_ids) <= evidence
    ):
        raise ValueError(
            "Review must refer to this submitted result and its eligible evidence"
        )
    if (
        review.relationship
        in {Relationship.DIRECT, Relationship.PARTIAL, Relationship.CONFLICT}
        and not review.evidence_ids
    ):
        raise ValueError("A support/conflict judgment requires selected evidence")
    return review


@dataclass
class EvidenceCapture:
    workflow: str
    query_sha256: str | None = None
    status: str = "not_observed"
    records: list[EvidenceRecord] = field(default_factory=list)


_ACTIVE: ContextVar[EvidenceCapture | None] = ContextVar(
    "evidence_inspector", default=None
)


@contextmanager
def collect_evidence(workflow: str) -> Iterator[EvidenceCapture]:
    capture = EvidenceCapture(workflow)
    token = _ACTIVE.set(capture)
    try:
        yield capture
    finally:
        _ACTIVE.reset(token)


def capture_selection(mode: str, query: str, selection: Any) -> None:
    capture = _ACTIVE.get()
    if capture is None or capture.workflow != mode:
        return
    try:
        capture.query_sha256 = hashlib.sha256(query.encode()).hexdigest()
        if selection.evidence is not None:
            records = [h.record for h in selection.evidence]
        else:
            catalog = {r.evidence_id: r for r in load_curated_records(mode)}
            records = [
                catalog[c["source_id"]]
                for c in selection.cards
                if c.get("source_id") in catalog
                and catalog[c["source_id"]].legacy_card() == c
            ]
        # The current orchestration grants only public curated references. Never
        # derive additional access/policy grants or registry claims from text.
        context = RetrievalQuery(
            text=query[:20_000] or "evidence", workflow=LEGACY_WORKFLOWS[mode]
        )
        capture.records = filter_records(
            records, context, lambda r: r.document_id is None
        )
        expected = (
            len(selection.evidence)
            if selection.evidence is not None
            else len(selection.cards)
        )
        capture.status = "captured" if len(capture.records) == expected else "partial"
    except Exception:  # noqa: BLE001 -- optional inspection cannot alter analysis or echo errors.
        capture.records = []
        capture.status = "unavailable"


SOC_KINDS = {
    "severity": ClaimKind.INFERENCE,
    "likely_incident_type": ClaimKind.INFERENCE,
    "summary": ClaimKind.UNKNOWN,
    "mitre_mapping": ClaimKind.INFERENCE,
    "observed_evidence": ClaimKind.OBSERVATION,
    "analyst_inferences": ClaimKind.INFERENCE,
    "recommended_containment": ClaimKind.RECOMMENDATION,
    "recommended_investigation_steps": ClaimKind.RECOMMENDATION,
    "evidence_gaps": ClaimKind.UNKNOWN,
    "analyst_note": ClaimKind.UNKNOWN,
}
GOV_KINDS = {
    "risk_level": ClaimKind.INFERENCE,
    "decision": ClaimKind.RECOMMENDATION,
    "summary": ClaimKind.UNKNOWN,
    "key_risks": ClaimKind.INFERENCE,
    "required_controls": ClaimKind.RECOMMENDATION,
    "human_review_requirements": ClaimKind.RECOMMENDATION,
    "logging_requirements": ClaimKind.RECOMMENDATION,
    "recommended_next_steps": ClaimKind.RECOMMENDATION,
    "evidence_gaps": ClaimKind.UNKNOWN,
}


def build_inspector(
    capture: EvidenceCapture, request: SocAlertRequest | GovernanceRiskRequest, result
) -> EvidenceInspectorReport:
    original = request.model_dump(mode="json")
    response = result.model_dump(mode="json")
    request_hash = fingerprint(original)
    inspector_id = fingerprint(
        {
            "request": request_hash,
            "response": response,
            "sources": [r.evidence_id for r in capture.records],
        }
    )
    cited = {s["source_id"] for s in response.get("source_references", [])}
    sources = tuple(
        InspectorSource(
            provenance=source_provenance(r),
            cited=r.evidence_id in cited,
            excerpt=r.content[:MAX_EXCERPT],
            excerpt_truncated=len(r.content) > MAX_EXCERPT,
        )
        for r in capture.records
    )
    inventory = []
    field_anchors = []
    structured = (
        microsoft_evidence(original) if isinstance(request, SocAlertRequest) else None
    )
    if structured is not None:
        for table, rows in sorted(structured.bundle["tables"].items()):
            for index, row in enumerate(rows):
                inventory.append(
                    InputInventoryRow(
                        observation_id=fingerprint([request_hash, table, index]),
                        table=table,
                        row_index=index,
                        field_names=tuple(sorted(row)),
                    )
                )
                for name, value in sorted(row.items()):
                    field_anchors.append(
                        SuppliedFieldAnchor(
                            evidence_id=fingerprint(
                                [
                                    request_hash,
                                    table,
                                    index,
                                    name,
                                    "supplied-field-v1",
                                ]
                            ),
                            request_sha256=request_hash,
                            table=table,
                            row_index=index,
                            field_name=name,
                            parent_observation_id=inventory[-1].observation_id,
                            value_presence="empty"
                            if value in (None, "", [], {})
                            else "nonempty",
                        )
                    )
    else:
        inventory.append(
            InputInventoryRow(
                observation_id=fingerprint([request_hash, "input"]),
                table=type(request).__name__,
                row_index=None,
                field_names=tuple(
                    k for k, v in original.items() if v not in (None, "", [])
                ),
            )
        )
    claims = []
    total = 0
    for name, kind in (
        SOC_KINDS if isinstance(request, SocAlertRequest) else GOV_KINDS
    ).items():
        values = response.get(name, [])
        for index, text in enumerate(values if isinstance(values, list) else [values]):
            if not isinstance(text, str) or not text.strip():
                continue
            total += 1
            if len(claims) >= MAX_INSPECTED_CLAIMS:
                continue
            claim_id = fingerprint([inspector_id, name, index, text])
            assessment = EvidenceSupportAssessment(
                claim_id=claim_id,
                candidate_evidence_ids=tuple(r.evidence_id for r in capture.records),
                relationship=Relationship.UNASSESSED,
                provenance=AssessmentOrigin.MODEL,
                verification_status="not_verified",
                limitation="Field-based claim kind is a display aid, not semantic classification. Global citations do not establish claim-specific support.",
            )
            claims.append(
                InspectorClaim(
                    claim_id=claim_id,
                    response_field=name,
                    kind=kind,
                    text=text[:4096],
                    text_truncated=len(text) > 4096,
                    assessment=assessment,
                )
            )
    return EvidenceInspectorReport(
        inspector_id=inspector_id,
        request_sha256=request_hash,
        query_sha256=capture.query_sha256,
        workflow=capture.workflow,
        retrieval_status=capture.status,
        sources=sources,
        input_inventory=tuple(inventory),
        field_anchors=tuple(field_anchors),
        claims=tuple(claims),
        total_claims=total,
        evidence_gaps=tuple(response.get("evidence_gaps", [])),
    )


def inspector_export(
    report: EvidenceInspectorReport,
    reviews: list[AnalystEvidenceReview] | None = None,
    *,
    corrections: tuple[AnalystCorrection, ...] = (),
) -> dict:
    checked = [
        validate_analyst_review(report, r).model_dump(mode="json")
        for r in reviews or []
    ]
    document = {
        "format": "evidence-inspector-v1",
        "inspector_id": report.inspector_id,
        "request_sha256": report.request_sha256,
        "workflow": report.workflow,
        "retrieval_status": report.retrieval_status,
        "sources": [
            {"provenance": s.provenance.model_dump(mode="json"), "cited": s.cited}
            for s in report.sources
        ],
        "input_inventory": [r.model_dump(mode="json") for r in report.input_inventory],
        "claims": [
            {
                "claim_id": c.claim_id,
                "response_field": c.response_field,
                "kind": c.kind.value,
                "relationship": c.assessment.relationship.value,
                "provenance": c.assessment.provenance.value,
                "verification_status": c.assessment.verification_status,
            }
            for c in report.claims
        ],
        "claims_shown": len(report.claims),
        "total_claims": report.total_claims,
        "analyst_reviews": checked,
        "human_review_required": True,
        "limitations": list(report.limitations),
    }
    if corrections:
        history = validate_correction_history(report, corrections)
        latest = {r.claim_id: r for r in history}
        claims = {c.claim_id: c for c in report.claims}
        summary = {
            "format": "analyst-review-summary-v1",
            "notice": "Contains unverified analyst-entered text and bounded original AI excerpts that may be sensitive. Review before sharing; not redacted. Original AI analysis remains unchanged. See correction_history for every revision.",
            "claims": [
                {
                    "claim_id": r.claim_id,
                    "original_response_field": r.original_response_field,
                    "original_claim_excerpt": claims[r.claim_id].text[:400],
                    "original_claim_excerpt_truncated": claims[
                        r.claim_id
                    ].text_truncated
                    or len(claims[r.claim_id].text) > 400,
                    "latest_proposed_text": r.proposed_text,
                    "category": r.category.value,
                    "revision_count": r.revision,
                    "provenance": r.provenance,
                    "verification_status": r.verification_status,
                    "evidence_linked": bool(r.evidence_ids),
                    "correction_id": r.correction_id,
                    "latest_revision_id": r.revision_id,
                    "history_section": "correction_history",
                }
                for r in latest.values()
            ],
        }
        document = {"review_summary": summary, **document}
        linked_ids = {i for r in history for i in r.evidence_ids}
        linked_fields = [
            a.model_dump(mode="json")
            for a in report.field_anchors
            if a.evidence_id in linked_ids
        ]
        if linked_fields:
            document["field_anchors"] = linked_fields
        document["correction_history"] = {
            "format": "analyst-corrections-v1",
            "notice": "Contains user-entered text that may be sensitive. Review before sharing; not redacted or independently verified. Original AI analysis is unchanged. Session history is not durable or an authenticated audit trail.",
            "revisions": [r.model_dump(mode="json") for r in history],
        }
    return document
