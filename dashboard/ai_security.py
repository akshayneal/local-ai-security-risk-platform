"""Experimental design editor and read-only source panel; never a tool executor."""

import json
from pathlib import Path

import streamlit as st

from app.ai_security_analyzer import validate_envelope_binding
from app.ai_security_api import unique_json
from app.ai_security_contracts import (
    MAX_WIRE_BYTES,
    AiSecurityEnvelope,
    AiSecurityRequest,
)
from dashboard.api_client import post_analysis
from dashboard.exports import _correction_text

SAMPLES = Path(__file__).resolve().parents[1] / "sample_data/ai_security_demo_v1"
EXAMPLES = {
    "Synthetic RAG ingestion": "rag.json",
    "Benign public drafts": "benign.json",
    "Insufficient architecture": "insufficient.json",
}
NOTICE = "Experimental advisory only. All architecture/evidence claims and model hypotheses are unverified. No exploit, control, approval or deployment verification and no actions executed. Review this export for sensitive text before sharing; it is not redacted."


def parse_design(text: str) -> AiSecurityRequest:
    if len(text.encode()) > MAX_WIRE_BYTES:
        raise ValueError("Design too large")
    return AiSecurityRequest.model_validate(
        json.loads(text, object_pairs_hook=unique_json)
    )


def export_ai_security(
    request: AiSecurityRequest, envelope: AiSecurityEnvelope
) -> dict:
    validate_envelope_binding(request, envelope)
    return {
        "format": "ai-security-advisory-v1",
        "workflow": "AI Security Assessment — Experimental",
        "application_name": request.application_name,
        "submitted_design_summary": {
            "provenance": "caller_supplied_unverified",
            "components": [{"id": c.id, "kind": c.kind} for c in request.components],
            "flows": [f.model_dump(mode="json") for f in request.flows],
            "control_ids": [c.id for c in request.controls],
            "implementation_evidence_ids": [
                e.id for e in request.implementation_evidence
            ],
            "verification_status": "not_verified",
        },
        "analysis": envelope.analysis.model_dump(mode="json"),
        "metadata": envelope.metadata.model_dump(mode="json"),
        "sharing_notice": NOTICE,
    }


def markdown_ai_security(document: dict) -> str:
    # Fixed headings; all submitted/generated strings are escaped as data.
    safe = _correction_text
    response = document["analysis"]
    lines = [
        "# AI Security Assessment — Experimental",
        "",
        safe(NOTICE),
        "",
        safe(document["application_name"]),
        "",
        "## Submitted design — unverified",
    ]
    lines.extend(
        safe(json.dumps(row, ensure_ascii=False))
        for row in document["submitted_design_summary"]["flows"]
    )
    lines += ["", "## Advisory summary", safe(response["summary"])]
    for finding in response["findings"]:
        lines += [
            "",
            "## Candidate finding",
            safe(json.dumps(finding, ensure_ascii=False)),
        ]
    lines += ["", "## Evidence gaps"] + [safe(gap) for gap in response["evidence_gaps"]]
    lines += ["", "## Source provenance — unassessed"] + [
        safe(json.dumps(source, ensure_ascii=False))
        for source in document["metadata"]["sources"]
    ]
    return "\n\n".join(lines)


def render_result(request: AiSecurityRequest, envelope: AiSecurityEnvelope) -> None:
    st.caption(
        "RESULT FOR SUBMITTED DESIGN · unassessed hypotheses · human review required"
    )
    st.text(envelope.analysis.coverage_status)
    st.text(envelope.analysis.summary)
    st.subheader("Submitted architecture claims — unverified")
    st.dataframe(
        [c.model_dump(mode="json") for c in request.components], hide_index=True
    )
    st.dataframe([f.model_dump(mode="json") for f in request.flows], hide_index=True)
    st.caption(
        "Flow classification and boundary crossings are caller statements. No graph edge was inferred from a diagram."
    )
    with st.expander(
        "Claimed controls and separately supplied implementation evidence"
    ):
        st.text(envelope.metadata.control_status)
        for item in (*request.controls, *request.implementation_evidence):
            st.text(item.model_dump_json())
    st.subheader("Candidate technical findings")
    if not envelope.analysis.findings:
        st.info(
            "No candidate findings returned. This is not evidence that the design is safe or deployed controls work."
        )
    for finding in envelope.analysis.findings:
        with st.container(border=True):
            st.text(
                f"{finding.finding_id} · {finding.category} · candidate / not_verified"
            )
            st.text(finding.hypothesis)
            st.text("Affected components: " + ", ".join(finding.component_ids))
            st.text("Affected flows: " + ", ".join(finding.flow_ids))
            for label, values in (
                ("Prerequisites", finding.prerequisites),
                ("Possible impact", (finding.possible_impact,)),
                ("Proposed mitigations", finding.proposed_mitigations),
                ("Validation recommendations", finding.validation_recommendations),
                ("Missing evidence", finding.missing_evidence),
                ("Guidance identities", finding.source_references),
            ):
                st.text(label + ": " + "\n".join(values))
    st.subheader("Evidence gaps and human review")
    for value in (
        *envelope.analysis.evidence_gaps,
        *envelope.analysis.human_review_requirements,
        *envelope.metadata.limitations,
    ):
        st.text(value)
    with st.expander("Read-only evidence provenance — unassessed"):
        st.caption(
            "Versioned local author guidance. Category and citation membership are structural metadata checks, not entailment or framework certification. Analyst correction history is not supported for this experimental workflow."
        )
        for source in envelope.metadata.sources:
            st.text(source.model_dump_json(indent=2))
    document = export_ai_security(request, envelope)
    st.caption(NOTICE)
    st.download_button(
        "Download AI Security JSON",
        json.dumps(document, indent=2, ensure_ascii=False),
        file_name="ai_security_advisory.json",
        mime="application/json",
    )
    st.download_button(
        "Download AI Security Markdown",
        markdown_ai_security(document),
        file_name="ai_security_advisory.md",
        mime="text/markdown",
    )


def ai_security_page(base_url: str) -> None:
    st.title("AI Security Assessment")
    st.caption(
        "EXPERIMENTAL · technical design review · no penetration testing or actions"
    )
    st.info(
        "The Windows development launcher uses the three-workflow gateway (app.ai_security_api:app). For a manual backend, use that same gateway. Local organizational knowledge is unsupported here; this workflow grants no document or tool permissions."
    )
    st.code(
        ".\\.venv\\Scripts\\python.exe -m uvicorn app.ai_security_api:app --host 127.0.0.1 --port 8000",
        language="powershell",
    )
    label = st.selectbox("Synthetic technical design", list(EXAMPLES))
    try:
        sample = (SAMPLES / EXAMPLES[label]).read_text(encoding="utf-8")
        parse_design(sample)
    except (OSError, ValueError):
        st.error("Synthetic example unavailable or invalid.")
        return
    if st.button("Load synthetic design"):
        st.session_state["aisec_design"] = sample
        st.session_state.pop("aisec_result", None)
        st.session_state.pop("aisec_error", None)
    st.session_state.setdefault("aisec_design", sample)
    with st.form("aisec_form"):
        text = st.text_area(
            "Declarative threat-model JSON",
            key="aisec_design",
            height=360,
            max_chars=MAX_WIRE_BYTES,
        )
        submitted = st.form_submit_button("Assess AI security", type="primary")
    if submitted:
        st.session_state.pop("aisec_result", None)
        st.session_state.pop("aisec_error", None)
        try:
            request = parse_design(text)
            body, error = post_analysis(
                base_url, "/ui/analyze/ai-security", request.model_dump(mode="json")
            )
            if error:
                st.session_state["aisec_error"] = error
            else:
                envelope = AiSecurityEnvelope.model_validate(body)
                validate_envelope_binding(request, envelope)
                st.session_state["aisec_result"] = (
                    request.model_dump(mode="json"),
                    envelope.model_dump(mode="json"),
                )
        except (ValueError, RuntimeError, RecursionError):
            st.session_state["aisec_error"] = (
                "Invalid design or unbound advisory result. Check identifiers, bounded fields and the experimental gateway."
            )
    if st.session_state.get("aisec_error"):
        st.error(st.session_state["aisec_error"])
    if saved := st.session_state.get("aisec_result"):
        render_result(
            AiSecurityRequest.model_validate(saved[0]),
            AiSecurityEnvelope.model_validate(saved[1]),
        )
