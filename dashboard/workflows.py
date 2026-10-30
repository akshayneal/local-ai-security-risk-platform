"""SOC and governance workspaces with persisted, explicitly submitted results."""

import streamlit as st
from pydantic import ValidationError

from app.evidence_inspector import inspector_export
from app.schemas import GovernanceRiskRequest, SocAlertRequest
from app.ui_schemas import GovernanceAnalysisEnvelope, SocAnalysisEnvelope
from dashboard.api_client import GENERIC_ERROR, post_analysis
from dashboard.evidence_inspector import correction_history, display_evidence_inspector
from dashboard.exports import export_document, json_export, markdown_export
from dashboard.knowledge_workspace import knowledge_checkbox
from dashboard.presentation import SOURCE_CAVEAT, TRUST_CAVEAT, integrity_rows
from dashboard.sample_loader import (
    SampleLoadError,
    form_values,
    load_governance_samples,
    load_soc_samples,
    sample_labels,
    select_sample,
)

SOC_FIELDS = (
    ("alert_id", "Alert ID"),
    ("alert_type", "Alert type"),
    ("source_system", "Source system"),
    ("affected_asset", "Affected asset"),
    ("raw_log", "Raw log"),
    ("known_indicators", "Known indicators, one per line"),
    ("observed_behavior", "Observed behavior"),
)
GOV_FIELDS = (
    ("system_name", "System name"),
    ("system_purpose", "System purpose"),
    ("data_types", "Data types, one per line"),
    ("users", "Users, one per line"),
    ("external_integrations", "External integrations, one per line"),
    ("human_review_process", "Human review process"),
    ("business_impact", "Business impact"),
)
LIST_FIELDS = {"known_indicators", "data_types", "users", "external_integrations"}


def section(title: str, items: list[str]) -> None:
    st.subheader(title)
    if not items:
        st.caption("None provided.")
    for item in items:
        st.text(f"• {item}")


def display_source_references(result: dict) -> None:
    st.subheader("Sources")
    st.caption(SOURCE_CAVEAT)
    sources = result.get("source_references", [])
    if not sources:
        st.info("No source references returned for this response.")
    for source in sources:
        with st.expander(source.get("title", "Untitled source")):
            st.text(f"Source family: {source.get('framework', 'Unknown')}")
            st.text(f"Source ID: {source.get('source_id', 'Unknown')}")
            st.text(source.get("relevance", "No relevance explanation provided."))


def trust_panel(metadata: dict, *, soc: bool) -> None:
    with st.container(border=True):
        st.subheader("Response checks" if soc else "Validation")
        st.dataframe(
            integrity_rows(metadata, soc=soc), hide_index=True, width="stretch"
        )
        st.caption(f"Local model: {metadata.get('model', 'Unavailable')}")
        with st.expander("About these checks"):
            st.write(TRUST_CAVEAT)
            if not soc:
                st.write(
                    "AI-system risk analysis is prompt-guided. The SOC identifier and endpoint contract does not apply."
                )


def soc_result(result: dict) -> None:
    severity, incident = st.columns([1, 3])
    severity.metric("Severity", result.get("severity", "Unknown").upper())
    incident.caption("LIKELY INCIDENT TYPE · provisional assessment")
    incident.text(result.get("likely_incident_type", "Unknown"))
    st.subheader("Summary")
    st.text(result.get("summary", ""))
    observed, inferences = st.columns(2)
    with observed:
        section("Observed Evidence", result.get("observed_evidence", []))
    with inferences:
        section("Analyst Inferences", result.get("analyst_inferences", []))
    investigate, actions, context = st.tabs(["Investigation", "Response", "Context"])
    with investigate:
        section("Evidence Gaps", result.get("evidence_gaps", []))
        section(
            "Recommended Investigation Steps",
            result.get("recommended_investigation_steps", []),
        )
    with actions:
        st.caption(
            "Recommendations only. Confirm scope and authorization before taking any action."
        )
        section("Recommended Containment", result.get("recommended_containment", []))
        section(
            "False Positive Considerations",
            result.get("false_positive_considerations", []),
        )
    with context:
        section("MITRE-Style Mapping", result.get("mitre_mapping", []))
        st.caption("Model-proposed mapping; not validated against MITRE ATT&CK STIX.")
        st.subheader("Analyst Note")
        st.text(result.get("analyst_note", ""))


def governance_result(result: dict) -> None:
    risk, decision = st.columns(2)
    risk.metric("Risk level", result["risk_level"].upper())
    decision.metric("Review decision", result["decision"].replace("_", " ").title())
    st.caption("The decision is proposed and requires human review.")
    st.subheader("Summary")
    st.text(result["summary"])
    concerns, controls, oversight = st.tabs(
        ["Risks & evidence", "Controls", "Human oversight"]
    )
    with concerns:
        section("Key Risks", result.get("key_risks", []))
        section("Evidence Gaps", result.get("evidence_gaps", []))
    with controls:
        section(
            "Model-Proposed Controls — Verify Applicability",
            result.get("required_controls", []),
        )
        section(
            "Logging Proposals / Stated Requirements — Verify",
            result.get("logging_requirements", []),
        )
    with oversight:
        section(
            "Human Review Requirements", result.get("human_review_requirements", [])
        )
        section("Recommended Next Steps", result.get("recommended_next_steps", []))


def _load_sample(prefix: str, samples: list, label: str) -> None:
    for field, value in form_values(select_sample(samples, label)).items():
        st.session_state[f"{prefix}_{field}"] = value
    st.session_state.pop(f"{prefix}_result", None)
    st.session_state.pop(f"{prefix}_error", None)
    st.session_state.pop(f"{prefix}_evidence_reviews", None)


def workflow_page(base_url: str, *, soc: bool) -> None:
    prefix = "soc" if soc else "gov"
    st.title("SOC Investigation" if soc else "AI System Risk Review")
    st.write(
        "Analyze security telemetry and prepare investigation and conditional response guidance."
        if soc
        else "Assess an AI system or proposed AI use case for governance, security, privacy and operational risk."
    )
    st.caption("Human review required · local inference · recommendations only")
    st.caption("SOC pillar" if soc else "AI Safety, Assurance & Policy pillar")
    if soc:
        from dashboard.microsoft_input import clear_soc_profile, microsoft_workspace

        profile = st.selectbox(
            "Input profile",
            ["Generic / normalized SOC input", "Microsoft Security telemetry"],
            key="soc_input_profile",
            on_change=clear_soc_profile,
        )
        if profile == "Microsoft Security telemetry":
            microsoft_workspace(base_url)
            return
    try:
        samples = load_soc_samples() if soc else load_governance_samples()
    except SampleLoadError as exc:
        st.warning(str(exc))
        samples = []
    fields = SOC_FIELDS if soc else GOV_FIELDS
    if samples:
        with st.container(border=True):
            st.caption(
                "SYNTHETIC / DEMO DATA · fictional inputs, no real incident or organization"
            )
            selection, load = st.columns([4, 1])
            label = selection.selectbox(
                "Synthetic sample", sample_labels(samples), key=f"{prefix}_sample"
            )
            load.button(
                "Load sample",
                on_click=_load_sample,
                args=(prefix, samples, label),
                width="stretch",
            )
        defaults = form_values(samples[0])
    else:
        defaults = {field: "" for field, _ in fields}
    for field, _ in fields:
        st.session_state.setdefault(f"{prefix}_{field}", defaults[field])
    with (
        st.expander("Case input" if soc else "System input", expanded=True),
        st.form(f"{prefix}_form"),
    ):
        values = {}
        left, right = st.columns(2)
        for index, (field, title) in enumerate(fields):
            column = left if index % 2 == 0 else right
            widget = (
                column.text_input
                if field
                in {
                    "alert_id",
                    "alert_type",
                    "source_system",
                    "affected_asset",
                    "system_name",
                }
                else column.text_area
            )
            values[field] = widget(title, key=f"{prefix}_{field}")
        include_knowledge = knowledge_checkbox(prefix)
        submitted = st.form_submit_button(
            "Analyze SOC alert" if soc else "Review AI system", type="primary"
        )
    if submitted:
        st.session_state.pop(f"{prefix}_result", None)
        st.session_state.pop(f"{prefix}_error", None)
        st.session_state.pop(f"{prefix}_evidence_reviews", None)
        payload = {
            field: [item.strip() for item in value.splitlines() if item.strip()]
            if field in LIST_FIELDS
            else value
            for field, value in values.items()
        }
        request_model = SocAlertRequest if soc else GovernanceRiskRequest
        envelope_model = SocAnalysisEnvelope if soc else GovernanceAnalysisEnvelope
        try:
            request = request_model.model_validate(payload)
        except ValidationError:
            st.session_state[f"{prefix}_error"] = (
                "Some input fields are invalid or too long. Review the form and submit again."
            )
        else:
            with st.spinner("Analyzing with the local model..."):
                body, error = post_analysis(
                    base_url,
                    "/ui/analyze/soc-alert" if soc else "/ui/analyze/governance",
                    {
                        **request.model_dump(mode="json"),
                        **({"local_knowledge": True} if include_knowledge else {}),
                    },
                )
            if error:
                st.session_state[f"{prefix}_error"] = error
            else:
                try:
                    envelope = envelope_model.model_validate(body)
                    document = export_document(
                        request,
                        envelope.analysis,
                        evidence_inspector=envelope.metadata.evidence_inspector,
                    )
                    st.session_state[f"{prefix}_result"] = {
                        "envelope": envelope.model_dump(mode="json"),
                        "document": document,
                        "submitted_input": request.model_dump(mode="json"),
                    }
                except (ValidationError, ValueError):
                    st.session_state[f"{prefix}_error"] = GENERIC_ERROR
    if st.session_state.get(f"{prefix}_error"):
        st.error(st.session_state[f"{prefix}_error"])
    saved = st.session_state.get(f"{prefix}_result")
    if saved:
        result = saved["envelope"]["analysis"]
        document = saved["document"]
        st.divider()
        st.caption(
            "RESULT FOR SUBMITTED INPUT · editing the form does not update this result"
        )
        st.text(" · ".join(document["case"].values()))
        analysis_column, integrity_column = st.columns([3, 2], gap="large")
        with analysis_column:
            (soc_result if soc else governance_result)(result)
        with integrity_column:
            trust_panel(saved["envelope"]["metadata"], soc=soc)
        display_source_references(result)
        inspector, reviews = display_evidence_inspector(
            saved["envelope"]["metadata"].get("evidence_inspector"),
            prefix=prefix,
            submitted_input=saved.get("submitted_input"),
        )
        if inspector is not None:
            document["evidence_inspector"] = inspector_export(
                inspector,
                reviews,
                corrections=correction_history(inspector, prefix=prefix),
            )
        st.subheader("Exports")
        st.caption("Submitted case identity and analysis; review before sharing.")
        json_column, md_column = st.columns(2)
        json_column.download_button(
            "Download JSON analysis",
            json_export(document),
            file_name=f"{prefix}_analysis.json",
            mime="application/json",
        )
        md_column.download_button(
            "Download Markdown brief",
            markdown_export(document),
            file_name=f"{prefix}_brief.md",
            mime="text/markdown",
        )
