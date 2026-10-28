"""Read-only product pages; evaluation/about work without running services."""

import streamlit as st

from dashboard.api_client import get_data
from dashboard.evaluation_catalog import (
    CROSS_VERSION_CAVEAT,
    ArtifactUnavailable,
    catalog_rows,
    same_suite_comparison,
)
from dashboard.presentation import audit_rows


def evaluation_page() -> None:
    st.header("Evaluation Lab")
    st.write("Frozen experiments, measured tradeoffs, visible limits.")
    st.warning(CROSS_VERSION_CAVEAT)
    st.caption(
        "Read-only tracked evidence. Opening this page does not run or rescore an evaluation."
    )
    history, comparison_tab, story = st.tabs(
        [
            "Evaluation history",
            "V3.2 same-suite comparison",
            "Security story & limitations",
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
            st.subheader("Integrity and availability tradeoff")
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
                "The exact frozen suite/scorer improved from 32/42 to 37/41 valid passes. Across all attempts the treatment passed 37/42. One response was withheld after failed repair; it is an availability loss, never a pass. Mean attempt latency increased from about 65.31 to 81.29 seconds."
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
    st.header("Activity")
    st.write("Recent local analysis outcomes and source usage.")
    st.caption(
        "Up to 100 most recent entries. Stored internal errors are omitted from this view."
    )
    left, right = st.columns(2)
    workflow = left.selectbox("Workflow", ["All", "soc_alert", "governance"])
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


def about_page() -> None:
    st.header("About the platform")
    st.write("Local AI analyst support for SOC investigation and AI governance review.")
    with st.container(border=True):
        st.subheader(
            "The model proposes. The application checks bounded properties. Humans decide."
        )
        st.write(
            "Results support investigation and review. The application does not execute containment, approve deployments or contact external services for threat verification."
        )
    st.subheader("Architecture")
    st.graphviz_chart("""digraph architecture {
        rankdir=LR; node [shape=box, style="rounded", fontname="Arial"];
        UI [label="Streamlit analyst workspace"];
        API [label="FastAPI + Pydantic requests"];
        Retrieval [label="Local reference retrieval"];
        Prompt [label="Untrusted-content quarantine"];
        Model [label="Local Ollama / qwen3:8b"];
        Sources [label="Citation cleanup + source sanitization"];
        SOC [label="SOC: full bounded integrity contract"];
        Repair [label="At most one policy repair"];
        Withheld [label="Failed repair: no analyst result"];
        Governance [label="Governance: response schema; semantics prompt-guided"];
        Result [label="Audit + analyst result + human review"];
        UI -> API -> Retrieval -> Prompt -> Model -> Sources;
        Sources -> SOC; Sources -> Governance;
        SOC -> Result [label="pass"]; SOC -> Repair [label="initial reject"];
        Repair -> SOC [label="recheck full contract"]; SOC -> Withheld [label="repair reject"];
        Governance -> Result;
    }""")
    st.caption(
        "The policy repair uses the neutralized original prompt and fixed machine reasons; failed raw output is not fed back. Transport/JSON retries remain separate from the single policy repair."
    )
    privacy, review = st.columns(2)
    with privacy:
        st.subheader("Local-first privacy")
        st.write(
            "Model inference runs locally through Ollama with no cloud AI API calls. Curated references and JSONL audit logs remain local. Inputs, summaries and exported briefs can contain sensitive information; review local files before sharing."
        )
    with review:
        st.subheader("Human review")
        st.write(
            "No truth, hallucination or safety percentage is assigned to a result. SOC identity membership does not prove claim support. Governance decisions and MITRE-style mapping are model proposals, not independently verified certifications."
        )
    st.subheader("Demo boundary")
    st.write(
        "A local demonstration, without authentication or a multi-user access boundary. No live threat intelligence, STIX validation, vector RAG, SIEM, ticketing or autonomous actions. Evaluation Lab and this page work without FastAPI or Ollama."
    )
