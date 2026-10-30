"""Expandable provenance and local analyst judgments, never automatic verification."""

import json

import streamlit as st
from pydantic import ValidationError

from app.evidence_inspector import (
    AnalystEvidenceReview,
    EvidenceInspectorReport,
    fingerprint,
    validate_analyst_review,
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
        state = {"inspector_id": report.inspector_id, "reviews": {}}
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
