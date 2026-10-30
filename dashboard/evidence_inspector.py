"""Expandable provenance and local analyst judgments, never automatic verification."""

import json

import streamlit as st
from pydantic import ValidationError

from app.evidence_inspector import (
    AnalystCorrection,
    AnalystEvidenceReview,
    CorrectionCategory,
    EvidenceInspectorReport,
    InspectorClaim,
    SuppliedFieldAnchor,
    append_analyst_correction,
    fingerprint,
    validate_analyst_review,
    validate_correction_history,
)
from app.microsoft_evidence import microsoft_evidence
from app.support_contracts import Relationship

REVIEW_OPTIONS = {
    "Unassessed": Relationship.UNASSESSED,
    "Supports within stated scope — analyst judgment": Relationship.DIRECT,
    "Partially supports — analyst judgment": Relationship.PARTIAL,
    "Insufficient support — analyst judgment": Relationship.RELATED,
    "Conflicting evidence — analyst judgment": Relationship.CONFLICT,
    "Inapplicable to this claim — analyst judgment": Relationship.INAPPLICABLE,
}
MAX_FIELD_CHOICES = 200


def field_label(anchor: SuppliedFieldAnchor) -> str:
    return f"Field: {anchor.table} · Row {anchor.row_index} · {anchor.field_name} ({anchor.value_presence})"


def field_choices(
    report: EvidenceInspectorReport, query: str
) -> tuple[tuple[SuppliedFieldAnchor, ...], int]:
    matching = tuple(
        a for a in report.field_anchors if query.casefold() in field_label(a).casefold()
    )
    return matching[:MAX_FIELD_CHOICES], len(matching)


def correction_history(
    report: EvidenceInspectorReport, *, prefix: str
) -> tuple[AnalystCorrection, ...]:
    state = st.session_state.get(f"{prefix}_evidence_reviews", {})
    if state.get("inspector_id") != report.inspector_id:
        return ()
    return validate_correction_history(
        report,
        tuple(
            AnalystCorrection.model_validate(r) for r in state.get("corrections", [])
        ),
    )


def _correction_editor(
    report: EvidenceInspectorReport,
    claim: InspectorClaim,
    labels: dict[str, str],
    state: dict,
    *,
    prefix: str,
) -> None:
    history = correction_history(report, prefix=prefix)
    selected = [r for r in history if r.claim_id == claim.claim_id]
    latest = selected[-1] if selected else None
    field_options = ()
    if report.field_anchors:
        query = st.text_input(
            "Filter supplied field anchors",
            key=f"{prefix}_field_filter_{report.inspector_id[:12]}_{claim.claim_id[:12]}",
            help="Filter by table, row or field name before editing. Changing filters can discard unsaved form edits. Row indices are zero-based. No field values appear in these labels.",
        )
        field_options, matching = field_choices(report, query)
        st.caption(
            f"Field anchor coverage: showing {len(field_options)} of {matching} matching fields ({len(report.field_anchors)} total). "
            + (
                "Incomplete display; refine the filter to find other fields."
                if matching > MAX_FIELD_CHOICES
                else "All matching fields shown."
            )
        )
    field_ids = {a.evidence_id for a in report.field_anchors}
    visible_ids = {a.evidence_id for a in field_options}
    retained_ids = tuple(
        evidence_id
        for evidence_id in (latest.evidence_ids if latest else ())
        if evidence_id in field_ids - visible_ids
    )
    if retained_ids:
        st.caption(
            f"{len(retained_ids)} previously linked fields outside this display are retained. Refine the filter to inspect or remove them."
        )
    st.write("Original AI analysis — unchanged")
    st.text(claim.text)
    st.caption(
        "Analyst-proposed correction — not independently verified. Session history is not durable storage or an authenticated audit trail. No reanalysis or action occurs."
    )
    form_key = f"{prefix}_correction_{report.inspector_id[:12]}_{claim.claim_id[:12]}_{latest.revision if latest else 0}"
    with st.form(form_key):
        categories = list(CorrectionCategory)
        category = st.selectbox(
            "Correction category",
            categories,
            format_func=lambda c: c.value,
            index=categories.index(latest.category) if latest else 0,
        )
        proposed = st.text_area(
            "Proposed correction wording",
            value=latest.proposed_text if latest else "",
            max_chars=4096,
        )
        rationale = st.text_area(
            "Correction rationale",
            value=latest.rationale if latest else "",
            max_chars=2000,
        )
        ids = st.multiselect(
            "Correction evidence",
            list(labels),
            default=[i for i in latest.evidence_ids if i in labels] if latest else [],
            format_func=labels.get,
        )
        selected_fields = []
        if report.field_anchors:
            field_labels = {a.evidence_id: field_label(a) for a in field_options}
            selected_fields = st.multiselect(
                "Supplied field evidence",
                list(field_labels),
                default=[i for i in latest.evidence_ids if i in visible_ids]
                if latest
                else [],
                format_func=field_labels.get,
            )
        st.caption(
            "Evidence is optional when documenting an unsupported claim. Linking a source does not verify this proposal or grant policy authority. Wording and rationale may be sensitive; review exports before sharing."
        )
        save = st.form_submit_button("Save correction revision")
    if save:
        try:
            history = append_analyst_correction(
                report,
                history,
                claim_id=claim.claim_id,
                category=category,
                proposed_text=proposed,
                rationale=rationale,
                evidence_ids=(*ids, *selected_fields, *retained_ids),
            )
            state["corrections"] = [r.model_dump(mode="json") for r in history]
            st.rerun()
        except (ValidationError, ValueError):
            st.warning(
                "Correction not saved. Use nonblank bounded wording/rationale and evidence from this result."
            )
    if selected:
        latest = selected[-1]
        st.write("Latest analyst-proposed correction — not independently verified")
        st.text(latest.proposed_text)
        st.text(f"Rationale: {latest.rationale}")
        st.caption(
            f"Revision {latest.revision}. "
            + (
                "Linked evidence selected; entailment remains unverified."
                if latest.evidence_ids
                else "No linked support selected."
            )
        )
        with st.expander("Correction revision history", expanded=False):
            for revision in selected:
                st.text(
                    f"Revision {revision.revision} · {revision.category.value}\nCorrection ID: {revision.correction_id}\nRevision ID: {revision.revision_id}\nSupersedes: {revision.supersedes_revision_id or 'None (first revision)'}\nOriginal field: {revision.original_response_field}\nOriginal claim fingerprint: {revision.original_claim_fingerprint}\nProposed: {revision.proposed_text}\nRationale: {revision.rationale}\nEvidence: {', '.join(revision.evidence_ids) or 'No linked support selected'}\nProvenance: analyst_recorded; not_verified"
                )


def display_evidence_inspector(
    data: dict | None, *, prefix: str, submitted_input: dict | None = None
):
    if data is None:
        st.caption("Evidence Inspector is unavailable for this older result.")
        return None, []
    try:
        report = EvidenceInspectorReport.model_validate(data)
    except ValidationError:
        st.warning(
            "Evidence Inspector metadata is unavailable. Review the submitted input and sources."
        )
        return None, []
    state_key = f"{prefix}_evidence_reviews"
    state = st.session_state.get(state_key)
    if not state or state["inspector_id"] != report.inspector_id:
        state = {"inspector_id": report.inspector_id, "reviews": {}, "corrections": []}
        st.session_state[state_key] = state
    with st.expander("Evidence Inspector", expanded=False):
        st.write(
            "Retrieved guidance is not binding policy. A binding requirement is not evidence that it has been satisfied."
        )
        st.caption(
            "Provenance and review aid. Model assertions are unassessed; no semantic reliability score or automatic verification."
        )
        st.text(
            f"Retrieved: {len(report.sources)} · Cited: {sum(s.cited for s in report.sources)} · Retrieval capture: {report.retrieval_status}"
        )
        sources_tab, input_tab, claims_tab, review_tab = st.tabs(
            [
                "Retrieved & cited",
                "Supplied evidence",
                "Claims & unknowns",
                "Analyst review",
            ]
        )
        with sources_tab:
            if not report.sources:
                st.info(
                    "No safely captured candidate references are available. Citation presence alone does not establish support."
                )
            for source in report.sources:
                p = source.provenance
                with st.expander(
                    f"{'Cited' if source.cited else 'Retrieved, uncited'} · {p.title}"
                ):
                    st.text(
                        f"Evidence ID: {p.evidence_id}\nFamily: {p.source_family}\nAuthority: {p.authority.value}\nPolicy scope: {p.policy_scope or 'No binding policy scope established'}\nApplicability: {', '.join(p.applicability) or 'Unknown for this case'}\nVersion: {p.document_version_id or 'Curated card'} · {p.version_status}\nEligibility: {p.eligibility}\nRegistry check: {p.registry_check}"
                    )
                    st.text(source.excerpt)
                    if source.excerpt_truncated:
                        st.caption("Source excerpt limited to 600 characters.")
                    st.caption(
                        "Eligibility and citation status are factual metadata checks; source-to-claim entailment is unassessed."
                    )
        with input_tab:
            st.caption(
                "Supplied observation inventory: table/row and available fields only. Private telemetry values are not reproduced here; review the original submitted evidence."
            )
            st.dataframe(
                [
                    {
                        "Table / input": r.table,
                        "Row": r.row_index,
                        "Supplied fields": ", ".join(r.field_names),
                    }
                    for r in report.input_inventory
                ],
                hide_index=True,
                width="stretch",
            )
            st.caption(f"Submitted request fingerprint: {report.request_sha256}")
            if (
                submitted_input is not None
                and fingerprint(submitted_input) == report.request_sha256
                and st.checkbox(
                    "Inspect a selected submitted value",
                    key=f"{prefix}_value_{report.inspector_id[:12]}",
                    help="Explicit local review only. Values may be sensitive and are excluded from evidence exports.",
                )
            ):
                structured = (
                    microsoft_evidence(submitted_input)
                    if report.workflow == "soc_alert"
                    else None
                )
                cells = {}
                if structured is not None:
                    for table, rows in sorted(structured.bundle["tables"].items()):
                        for index, row in enumerate(rows):
                            for name, value in sorted(row.items()):
                                cells[f"{table}[{index}].{name}"] = value
                else:
                    cells = submitted_input
                selected = st.selectbox(
                    "Submitted field to inspect",
                    list(cells),
                    key=f"{prefix}_input_field_{report.inspector_id[:12]}",
                    disabled=not cells,
                )
                if selected is not None:
                    value = cells[selected]
                    text = (
                        value
                        if isinstance(value, str)
                        else json.dumps(value, ensure_ascii=False)
                    )
                    st.text(text[:2000])
                    st.caption(
                        f"Supplied value, not independent verification. Showing {min(len(text), 2000)} of {len(text)} characters; inspect the original source for the complete value."
                    )
                else:
                    st.caption("No supplied fields are available for value inspection.")
        with claims_tab:
            st.caption(
                f"Showing {len(report.claims)} of {report.total_claims} model assertions. Any omitted assertions remain unassessed. Claim kind follows response fields, not a semantic classifier."
            )
            st.dataframe(
                [
                    {
                        "Response field": c.response_field,
                        "Kind / display aid": c.kind.value,
                        "Support": "Analyst verification required",
                        "Origin": c.assessment.provenance.value,
                        "Assertion": c.text,
                    }
                    for c in report.claims
                ],
                hide_index=True,
                width="stretch",
            )
            for gap in report.evidence_gaps:
                st.text(f"Model-proposed gap, verify against input: {gap}")
        with review_tab:
            st.caption(
                "Record your assessment of a selected claim. This is a local user judgment, not independently authenticated or machine-verified support. It does not change the analysis or grant source access."
            )
            if report.claims:
                claims = {c.claim_id: c for c in report.claims}
                labels = {
                    s.provenance.evidence_id: f"Reference: {s.provenance.title}"
                    for s in report.sources
                }
                labels.update(
                    {
                        r.observation_id: f"Supplied inventory: {r.table} row {r.row_index}"
                        for r in report.input_inventory
                    }
                )
                claim_id = st.selectbox(
                    "Claim to review",
                    list(claims),
                    format_func=lambda key: (
                        f"{claims[key].response_field}: {claims[key].text[:100]}"
                    ),
                    key=f"{prefix}_claim_{report.inspector_id[:12]}",
                )
                st.text(claims[claim_id].text)
                if claims[claim_id].text_truncated:
                    st.caption(
                        "Assertion excerpt truncated; review the full analysis before recording a judgment."
                    )
                with st.form(f"{prefix}_review_{report.inspector_id[:12]}"):
                    relation = st.selectbox(
                        "Analyst support judgment", list(REVIEW_OPTIONS)
                    )
                    ids = st.multiselect(
                        "Evidence considered", list(labels), format_func=labels.get
                    )
                    note = st.text_area("Analyst review note", max_chars=1000)
                    submitted = st.form_submit_button("Record analyst judgment")
                if submitted:
                    try:
                        review = validate_analyst_review(
                            report,
                            AnalystEvidenceReview(
                                inspector_id=report.inspector_id,
                                claim_id=claim_id,
                                relationship=REVIEW_OPTIONS[relation],
                                evidence_ids=tuple(ids),
                                note=note,
                            ),
                        )
                        state["reviews"][claim_id] = review.model_dump(mode="json")
                        st.info(
                            "Analyst judgment recorded for this submitted result. It remains unverified."
                        )
                    except (ValidationError, ValueError):
                        st.warning(
                            "Select evidence for a support/conflict judgment and keep the note within limits."
                        )
                _correction_editor(
                    report, claims[claim_id], labels, state, prefix=prefix
                )
            st.text(f"Recorded analyst judgments: {len(state['reviews'])}")
        for limitation in report.limitations:
            st.caption(limitation)
    reviews = []
    for value in state["reviews"].values():
        try:
            reviews.append(
                validate_analyst_review(
                    report, AnalystEvidenceReview.model_validate(value)
                )
            )
        except (ValidationError, ValueError):
            continue
    return report, reviews
