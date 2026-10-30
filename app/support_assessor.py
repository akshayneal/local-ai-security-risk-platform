"""Conservative exact structured-record matching; no natural-language truth checker."""

import hashlib
import json

from pydantic import ValidationError

from app.retrieval.contracts import Authority, RetrievalQuery, RetrievedEvidence
from app.retrieval.filtering import VersionGate, filter_records, unique_records
from app.support_contracts import (
    AssessmentOrigin,
    ClaimComponent,
    ClaimKind,
    ComponentSupport,
    EvidenceClaim,
    EvidenceSupportAssessment,
    Relationship,
    SourceSupportProvenance,
)


def source_provenance(
    record, *, registry_checked: bool = False
) -> SourceSupportProvenance:
    if record.document_id is not None and not registry_checked:
        raise ValueError("Document provenance requires a checked registry gate")
    return SourceSupportProvenance(
        evidence_id=record.evidence_id,
        source_id=record.source_id,
        title=record.title,
        source_family=record.source_family,
        source_type=record.source_type,
        authority=record.authority,
        policy_scope=record.policy_scope,
        applicability=tuple(sorted(record.applicability)),
        document_version_id=record.document_version_id,
        version_status=record.status,
        content_sha256=hashlib.sha256(record.content.encode()).hexdigest(),
        registry_check="passed" if record.document_id is not None else "not_applicable",
    )


def _assertions(content: str) -> list[ClaimComponent]:
    # Never interpret embedded authority, access grants, role text or instructions.
    # Unstructured prose and malformed/oversized formats remain unassessed.
    if len(content.encode()) > 80_000:
        return []

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Ambiguous structured assertion")
            result[key] = value
        return result

    try:
        payload = json.loads(content, object_pairs_hook=unique_object)
        values = payload.get("assertions") if isinstance(payload, dict) else None
        if not isinstance(values, list) or len(values) > 64:
            return []
        return [ClaimComponent.model_validate(value) for value in values]
    except (ValueError, ValidationError, RecursionError):
        return []


def _allowed_kind(component: ClaimComponent, record, query, claim_scope) -> bool:
    if record.status != "current":
        return False
    if component.kind == ClaimKind.REQUIREMENT:
        scope = claim_scope or (
            next(iter(query.policy_scopes)) if len(query.policy_scopes) == 1 else None
        )
        return (
            record.authority == Authority.POLICY
            and scope is not None
            and record.policy_scope == scope
        )
    if component.kind == ClaimKind.OBSERVATION:
        return record.source_type in {"case_observation", "inventory"}
    if component.kind == ClaimKind.IMPLEMENTATION:
        return record.source_type in {"implementation_record", "case_observation"}
    return component.kind == ClaimKind.RECOMMENDATION and record.authority in {
        Authority.LOCAL,
        Authority.EXTERNAL,
        Authority.POLICY,
    }


def assess_support(
    claim: EvidenceClaim,
    query: RetrievalQuery,
    candidates: list[RetrievedEvidence],
    *,
    version_gate: VersionGate | None = None,
) -> EvidenceSupportAssessment:
    # Eligibility is rechecked before even exposing candidate IDs/content to output.
    # A document/version record needs a live/trusted registry gate, not only a
    # self-contained current-status label. Missing gate does not reactivate it.
    gate = version_gate or (lambda record: record.document_id is None)
    records = filter_records(unique_records(h.record for h in candidates), query, gate)
    ids = tuple(r.evidence_id for r in records)
    parsed = {r.evidence_id: _assertions(r.content) for r in records}
    components = []
    for index, component in enumerate(claim.components):
        matches, different = [], []
        for record in records:
            if not _allowed_kind(component, record, query, claim.scope):
                continue
            for assertion in parsed[record.evidence_id]:
                if (assertion.subject, assertion.predicate, assertion.kind) != (
                    component.subject,
                    component.predicate,
                    component.kind,
                ):
                    continue
                # bool/int and numeric/string coercion must not create support.
                if (
                    type(assertion.value) is type(component.value)
                    and assertion.value == component.value
                ):
                    matches.append(record.evidence_id)
                else:
                    different.append(record.evidence_id)
        matches, different = (
            list(dict.fromkeys(matches)),
            list(dict.fromkeys(different)),
        )
        if different and matches:
            relationship, reason = (
                Relationship.CONFLICT,
                "Eligible comparable structured assertions disagree; no reconciliation performed.",
            )
        elif matches:
            relationship, reason = (
                Relationship.DIRECT,
                "Exact typed assertion matched within trusted source type and scope; record-level support only.",
            )
        elif different:
            relationship, reason = (
                Relationship.CONFLICT,
                "Eligible comparable structured assertions contradict the requested value.",
            )
        else:
            relationship = Relationship.RELATED if records else Relationship.NONE
            reason = "No machine-verifiable structured support established; natural-language entailment remains unassessed."
        components.append(
            ComponentSupport(
                component_index=index,
                relationship=relationship,
                supporting_evidence_ids=tuple(matches),
                conflicting_evidence_ids=tuple(different),
                reason=reason,
            )
        )
    relationships = [c.relationship for c in components]
    if Relationship.CONFLICT in relationships:
        relationship = Relationship.CONFLICT
    elif all(r == Relationship.DIRECT for r in relationships):
        relationship = Relationship.DIRECT
    elif Relationship.DIRECT in relationships:
        relationship = Relationship.PARTIAL
    else:
        relationship = Relationship.RELATED if records else Relationship.NONE
    matched = any(
        c.supporting_evidence_ids or c.conflicting_evidence_ids for c in components
    )
    return EvidenceSupportAssessment(
        claim_id=claim.claim_id,
        candidate_evidence_ids=ids,
        relationship=relationship,
        supporting_evidence_ids=tuple(
            dict.fromkeys(key for c in components for key in c.supporting_evidence_ids)
        ),
        source_provenance=tuple(
            source_provenance(r, registry_checked=version_gate is not None)
            for r in records
        ),
        components=tuple(components),
        provenance=AssessmentOrigin.RECORD_MATCH
        if matched
        else AssessmentOrigin.UNASSESSED,
        verification_status="record_match_only" if matched else "not_verified",
    )
