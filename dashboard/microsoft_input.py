"""Microsoft is an input profile of the existing SOC workflow."""

import hashlib
import json

import streamlit as st
from pydantic import ValidationError

from app.evidence_inspector import inspector_export
from app.soc_inputs import (
    TABLES,
    MicrosoftSocAdapter,
    SocInputError,
    parse_csv_bundle,
    parse_json_bundle,
)
from app.ui_schemas import SocAnalysisEnvelope
from dashboard.api_client import GENERIC_ERROR, post_analysis
from dashboard.evidence_inspector import correction_history, display_evidence_inspector
from dashboard.exports import export_document, json_export, markdown_export
from dashboard.knowledge_workspace import knowledge_checkbox
from dashboard.sample_loader import SampleLoadError, load_microsoft_samples


def clear_soc_profile() -> None:
    for key in (
        "soc_result",
        "soc_error",
        "ms_result",
        "ms_error",
        "soc_evidence_reviews",
        "ms_evidence_reviews",
    ):
        st.session_state.pop(key, None)


def microsoft_workspace(base_url: str) -> None:
    # Import at render time to share presentation without a module import cycle.
    from dashboard.workflows import display_source_references, soc_result, trust_panel

    st.caption("SYNTHETIC EXAMPLES · local JSON / CSV · no Microsoft connection")
    st.caption(
        "Valid uploads must also fit a complete local analysis. Oversized analyses are withheld; input rows are never silently selected out."
    )
    try:
        samples = load_microsoft_samples()
    except SampleLoadError as exc:
        st.warning(str(exc))
        samples = {}
    if samples:
        label = st.selectbox("Microsoft synthetic sample", list(samples))
        if st.button("Load Microsoft sample"):
            st.session_state["ms_json"] = json.dumps(samples[label], indent=2)
            clear_soc_profile()
    mode = st.selectbox("Telemetry input", ["Paste JSON", "Upload JSON", "Upload CSV"])
    data: str | bytes = ""
    table, case_id = "", ""
    if mode == "Paste JSON":
        data = st.text_area("Microsoft JSON bundle", key="ms_json", height=240)
    else:
        upload = st.file_uploader(
            "Microsoft telemetry file",
            type=["csv" if mode == "Upload CSV" else "json"],
            key=f"ms_upload_{mode}",
        )
        if upload is not None:
            data = upload.getvalue()
        if mode == "Upload CSV":
            table = st.selectbox("CSV source table", TABLES)
            case_id = st.text_input("CSV case ID", value="SYN-CSV-001")
    fingerprint = hashlib.sha256(
        (mode + table + case_id).encode()
        + (data.encode() if isinstance(data, str) else data)
    ).hexdigest()
    if st.session_state.get("ms_input_fingerprint") != fingerprint:
        st.session_state.pop("ms_result", None)
        st.session_state.pop("ms_error", None)
        st.session_state.pop("ms_evidence_reviews", None)
        st.session_state["ms_input_fingerprint"] = fingerprint
    normalized = None
    if data:
        try:
            bundle = (
                parse_csv_bundle(data, table, case_id)
                if mode == "Upload CSV"
                else parse_json_bundle(data)
            )
            normalized = MicrosoftSocAdapter().normalize(bundle)
        except SocInputError as exc:
            st.error(str(exc))
    if normalized is not None:
        st.subheader("Normalization preview")
        st.text(f"Case: {normalized.request.alert_id}")
        st.dataframe(
            [{"Table": t, "Rows": n} for t, n in normalized.row_counts.items()],
            hide_index=True,
        )
        st.text(
            "Affected entities: "
            + ("; ".join(normalized.entities[:20]) or "Not supplied")
        )
        st.text(
            "Indicators: "
            + ("; ".join(normalized.request.known_indicators[:20]) or "Not supplied")
        )
        st.caption(
            "Preview lists show up to 20 entries. All supplied rows remain in canonical raw evidence."
        )
        for warning in normalized.warnings:
            st.warning(warning)
    include_knowledge = knowledge_checkbox("ms")
    if st.button(
        "Analyze Microsoft telemetry", type="primary", disabled=normalized is None
    ):
        st.session_state.pop("ms_result", None)
        st.session_state.pop("ms_error", None)
        st.session_state.pop("ms_evidence_reviews", None)
        with st.spinner("Analyzing with the local model..."):
            body, error = post_analysis(
                base_url,
                "/ui/analyze/soc-alert",
                {
                    **normalized.request.model_dump(mode="json"),
                    **({"local_knowledge": True} if include_knowledge else {}),
                },
            )
        if error:
            st.session_state["ms_error"] = error
        else:
            try:
                envelope = SocAnalysisEnvelope.model_validate(body)
                st.session_state["ms_result"] = {
                    "envelope": envelope.model_dump(mode="json"),
                    "submitted_input": normalized.request.model_dump(mode="json"),
                    "document": export_document(
                        normalized.request,
                        envelope.analysis,
                        evidence_inspector=envelope.metadata.evidence_inspector,
                    ),
                }
            except (ValidationError, ValueError):
                st.session_state["ms_error"] = GENERIC_ERROR
    if st.session_state.get("ms_error"):
        st.error(st.session_state["ms_error"])
    saved = st.session_state.get("ms_result")
    if saved:
        st.divider()
        st.caption("RESULT FOR SUBMITTED MICROSOFT INPUT · human review required")
        soc_result(saved["envelope"]["analysis"])
        trust_panel(saved["envelope"]["metadata"], soc=True)
        display_source_references(saved["envelope"]["analysis"])
        inspector, reviews = display_evidence_inspector(
            saved["envelope"]["metadata"].get("evidence_inspector"),
            prefix="ms",
            submitted_input=saved.get("submitted_input"),
        )
        if inspector is not None:
            saved["document"]["evidence_inspector"] = inspector_export(
                inspector,
                reviews,
                corrections=correction_history(inspector, prefix="ms"),
            )
        st.subheader("Exports")
        st.download_button(
            "Download JSON analysis",
            json_export(saved["document"]),
            file_name="soc_analysis.json",
            mime="application/json",
        )
        st.download_button(
            "Download Markdown brief",
            markdown_export(saved["document"]),
            file_name="soc_brief.md",
            mime="text/markdown",
        )
