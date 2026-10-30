"""Read-only product pages; evaluation/about work without running services."""

import streamlit as st

from dashboard.api_client import get_data
from dashboard.evaluation_catalog import (
    CROSS_VERSION_CAVEAT,
    ArtifactUnavailable,
    catalog_rows,
    same_suite_comparison,
)
from dashboard.navigation import PILLARS
from dashboard.presentation import audit_rows


def evaluation_page() -> None:
    st.title("Platform Evaluation")
    st.write(
        "This page summarizes the frozen evaluations used to test and harden this platform."
    )
    st.caption(
        "Platform assurance: development and evaluation history for this application"
    )
    st.info(CROSS_VERSION_CAVEAT)
    st.caption(
        "Read-only tracked evidence. Opening this page does not run or rescore an evaluation."
    )
    history, comparison_tab, story = st.tabs(
        [
            "Evaluation history",
            "V3.2 same-suite comparison",
            "Test coverage & limitations",
        ]
    )
    with history:
        rows, errors = catalog_rows()
        for error in errors:
            st.warning(error)
        st.dataframe(rows, hide_index=True, width="stretch")
        st.caption(
            "Official passes use valid returned analyses as denominator; errors are shown separately. Stability labels exclude application errors: V2 treatment has a stable-pass-labelled case with two passes/error, as does V3.2 treatment."
        )
    with comparison_tab:
        try:
            comparison = same_suite_comparison()
        except ArtifactUnavailable as exc:
            st.warning(str(exc))
        else:
            st.subheader("V3.2 treatment comparison")
            baseline, treatment = comparison["metrics"]
            st.dataframe(
                [
                    {
                        "Metric": field,
                        "Baseline": str(baseline[field]),
                        "Treatment": str(treatment[field]),
                    }
                    for field in baseline
                    if field != "Run"
                ],
                hide_index=True,
                width="stretch",
            )
            st.write(
                "Treatment passed 37/41 valid analyses and 37/42 attempts, compared with 32/42 at baseline. One analysis was withheld after failed repair. Mean attempt latency increased from 65.31 to 81.29 seconds."
            )
            st.caption(
                "One bundled, unseeded comparison cannot isolate individual controls or hardware effects. Four treatment failures are suspected lexical scorer mismatches; official scores remain unchanged."
            )
            case = st.selectbox(
                "Inspect frozen case outcomes",
                [r["Case ID"] for r in comparison["cases"]],
            )
            st.dataframe(
                [r for r in comparison["cases"] if r["Case ID"] == case],
                hide_index=True,
                width="stretch",
            )
            st.info(
                "A stable-pass label means all valid trials passed. V32-SOC-006 treatment is error / pass / pass, not three successful responses."
            )
            with st.expander("All case transitions"):
                st.dataframe(comparison["cases"], hide_index=True, width="stretch")
    with story:
        st.subheader("What was tested")
        st.write(
            "Direct and indirect prompt injection; retrieval poisoning; source integrity; evidence fidelity; claim authority; event grounding; cross-field consistency; agency limits."
        )
        st.subheader("What changed")
        st.write(
            "Prompt guidance → repeated evaluation → deterministic I/O boundary → semantic grounding measurement → calibrated evaluator → final semantic production treatment."
        )
        st.subheader("What remains limited")
        st.write(
            "Small synthetic suites, three unseeded trials and a local qwen model do not establish a statistical safety guarantee. Latency and fail-closed availability costs remain. Deterministic identity grammar is finite; support-scope ambiguity, formatting and out-of-key identifiers still require human review. Governance semantics are prompt-guided. Manual review found false positives and missed defects, including official passes."
        )


def activity_page(base_url: str) -> None:
    st.title("Activity")
    st.write(
        "Platform activity: recent analysis submissions, outcomes and source usage."
    )
    st.caption(
        "Latest 100 audit entries. This view is not an incident-management queue."
    )
    left, right = st.columns(2)
    workflow = left.selectbox(
        "Workflow",
        ["All", "soc_alert", "governance"],
        format_func=lambda value: {
            "soc_alert": "SOC Investigation",
            "governance": "AI System Risk Review",
        }.get(value, value),
    )
    outcome = right.selectbox("Outcome", ["All", "Success", "Failure"])
    data, error = get_data(base_url, "/logs?limit=100")
    if error:
        st.info(error)
        return
    rows = audit_rows(data.get("logs", []), workflow, outcome)
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")
    else:
        st.info(
            "No activity matches these filters. Submit an analysis to create an audit entry."
        )


def overview_page() -> None:
    st.title("Overview")
    st.write(
        "Local analyst-support platform for security-event investigation and AI-system risk review."
    )
    for column, pillar in zip(st.columns(3), PILLARS, strict=True):
        with column, st.container(border=True):
            st.subheader(pillar["title"])
            st.caption(pillar["status"])
            st.markdown(f"**{pillar['workflow']}**")
            st.write(pillar["description"])
            if "page" in pillar:
                st.page_link(pillar["page"], label="Open workflow")
    st.caption(
        "Two active analyzers. AI Security Assessment and standalone SOC Policy & Governance Review remain Planned. Development features are unmerged, not a new release."
    )
    st.subheader("Shared local evidence and assurance")
    st.write(
        "Structured telemetry, curated guidance and explicitly opted-in reviewed local documents feed bounded inference. Provenance, deterministic checks, Evidence Inspector and analyst corrections support human review; citations do not prove truth or authorize action."
    )
    st.caption(
        "Sprint 5 experimental: registered document bridge and Knowledge Workspace. Local knowledge defaults off; no authentication or enterprise IAM."
    )
    st.subheader("Platform views")
    st.write(
        "Platform Evaluation summarizes this application's frozen test history. Activity shows local audit entries. About explains architecture and operational boundaries."
    )


def about_page() -> None:
    st.title("About")
    st.subheader("Product scope")
    st.write(
        "Three pillars share local evidence and assurance: SOC; AI Security (assessment Planned); AI Safety, Assurance & Policy (AI System Risk Review active). Platform Evaluation reports this application's own frozen evaluations."
    )
    st.subheader("Architecture")
    stages = (
        ("1. Request", "Streamlit input, FastAPI and Pydantic request validation"),
        (
            "2. Context",
            "Curated guidance; optional reviewed current local documents, scoped eligibility and untrusted-content handling",
        ),
        ("3. Inference", "Configured local Ollama model; qwen3:8b by default"),
    )
    for column, (title, description) in zip(st.columns(3), stages, strict=True):
        with column, st.container(border=True):
            st.markdown(f"**{title}**")
            st.write(description)
    soc, risk = st.columns(2)
    with soc, st.container(border=True):
        st.markdown("**4. SOC Investigation response**")
        st.write(
            "Source sanitization and schema validation. Bounded identifier, endpoint and observation checks. One policy repair; analysis withheld if the repaired response fails."
        )
    with risk, st.container(border=True):
        st.markdown("**4. AI System Risk Review response**")
        st.write(
            "Source sanitization and schema validation. Prompt-guided risk analysis; no SOC identifier/endpoint contract."
        )
    with st.container(border=True):
        st.markdown("**5. Result**")
        st.write(
            "Local audit entry, analyst-facing result and optional brief export. Human review required."
        )
    st.subheader("Current release")
    st.write(
        "Released main/v2.3.0 has two active analyzers. Inspector, corrections and Microsoft inputs are unmerged functional development. Sprint 5 local knowledge is experimental and opt-in. AI Security Assessment and standalone SOC Policy & Governance Review remain Planned."
    )
    st.write(
        "Policy applicability and model correctness are separate. An applicable requirement is not evidence of implementation, granted approval, complete evidence coverage or a correct generated answer."
    )
    st.subheader("Operational boundaries")
    left, right = st.columns(2)
    left.markdown(
        "- Local Ollama inference; no cloud AI API\n- No automatic containment or other actions\n- No live threat-intelligence verification"
    )
    right.markdown(
        "- No authentication or multi-user boundary\n- Human review required\n- Local audit summaries and exports may contain sensitive input"
    )
    with st.expander("Validation limits"):
        st.write(
            "SOC checks recognize a finite set of IPv4, SHA-256, CVE-style and endpoint forms. They do not prove every conclusion, preserve every identifier or establish completeness. Governance semantics and MITRE-style mapping require review. Local inference can be slow; repair and withheld output affect availability. A UI timeout does not cancel backend work."
        )
