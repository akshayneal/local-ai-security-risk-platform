import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Local AI Security Risk Platform",
    page_icon="🛡️",
    layout="wide",
)

st.title("Local AI Security Risk & SOC Triage Platform")
st.write(
    "A local AI project using FastAPI, Streamlit, Ollama, Pydantic schemas, and audit logging."
)

mode = st.sidebar.selectbox(
    "Choose analysis mode",
    ["AI Governance Risk Intake", "SOC Alert Triage", "Audit Logs"],
)


def post_to_api(endpoint: str, payload: dict):
    """
    Sends a POST request from the Streamlit dashboard to the FastAPI backend.
    """
    url = f"{API_BASE_URL}{endpoint}"

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json(), None

    except requests.exceptions.RequestException as exc:
        return None, str(exc)


if mode == "AI Governance Risk Intake":
    st.header("AI Governance Risk Intake")

    with st.form("governance_form"):
        system_name = st.text_input("System name", "Internal HR Policy Chatbot")

        system_purpose = st.text_area(
            "System purpose",
            "Answer employee questions using internal HR policy documents.",
        )

        data_types = st.text_area(
            "Data types, one per line",
            "employee handbook\nbenefits information\npolicy documents\nlimited employee personal data",
        )

        users = st.text_area(
            "Users, one per line",
            "HR staff\nemployees",
        )

        external_integrations = st.text_area(
            "External integrations, one per line",
            "internal document repository",
        )

        human_review_process = st.text_area(
            "Human review process",
            "HR reviews high-risk answers before policy changes are communicated.",
        )

        business_impact = st.text_area(
            "Business impact",
            "Medium impact because incorrect answers could mislead employees about benefits or workplace policy.",
        )

        submitted = st.form_submit_button("Analyze Governance Risk")

    if submitted:
        payload = {
            "system_name": system_name,
            "system_purpose": system_purpose,
            "data_types": [
                item.strip() for item in data_types.splitlines() if item.strip()
            ],
            "users": [
                item.strip() for item in users.splitlines() if item.strip()
            ],
            "external_integrations": [
                item.strip()
                for item in external_integrations.splitlines()
                if item.strip()
            ],
            "human_review_process": human_review_process,
            "business_impact": business_impact,
        }

        with st.spinner("Analyzing governance risk with local model..."):
            result, error = post_to_api("/analyze/governance", payload)

        if error:
            st.error(error)
        else:
            st.subheader("Result")

            col1, col2 = st.columns(2)
            col1.metric("Risk Level", result.get("risk_level", "unknown"))
            col2.metric("Decision", result.get("decision", "unknown"))

            st.subheader("Summary")
            st.write(result.get("summary", ""))

            st.subheader("Key Risks")
            for risk in result.get("key_risks", []):
                st.write(f"- {risk}")

            st.subheader("Required Controls")
            for control in result.get("required_controls", []):
                st.write(f"- {control}")

            st.subheader("Human Review Requirements")
            for requirement in result.get("human_review_requirements", []):
                st.write(f"- {requirement}")

            st.subheader("Logging Requirements")
            for requirement in result.get("logging_requirements", []):
                st.write(f"- {requirement}")

            st.subheader("Evidence Gaps")
            for gap in result.get("evidence_gaps", []):
                st.write(f"- {gap}")

            st.subheader("Recommended Next Steps")
            for step in result.get("recommended_next_steps", []):
                st.write(f"- {step}")

            with st.expander("Full JSON response"):
                st.json(result)


elif mode == "SOC Alert Triage":
    st.header("SOC Alert Triage")

    with st.form("soc_form"):
        alert_id = st.text_input("Alert ID", "SOC-001")

        alert_type = st.text_input(
            "Alert type",
            "SSH brute force followed by successful login",
        )

        source_system = st.text_input("Source system", "Linux auth logs")

        affected_asset = st.text_input("Affected asset", "ubuntu-web-01")

        raw_log = st.text_area(
            "Raw log",
            "Multiple failed password attempts for root from 185.22.10.4 followed by accepted password for admin from the same IP.",
        )

        known_indicators = st.text_area(
            "Known indicators, one per line",
            "185.22.10.4\nroot\nadmin",
        )

        observed_behavior = st.text_area(
            "Observed behavior",
            "A foreign IP attempted multiple failed logins and then successfully authenticated to an admin account.",
        )

        submitted = st.form_submit_button("Analyze SOC Alert")

    if submitted:
        payload = {
            "alert_id": alert_id,
            "alert_type": alert_type,
            "source_system": source_system,
            "affected_asset": affected_asset,
            "raw_log": raw_log,
            "known_indicators": [
                item.strip()
                for item in known_indicators.splitlines()
                if item.strip()
            ],
            "observed_behavior": observed_behavior,
        }

        with st.spinner("Triaging SOC alert with local model..."):
            result, error = post_to_api("/analyze/soc-alert", payload)

        if error:
            st.error(error)
        else:
            st.subheader("Result")

            col1, col2 = st.columns(2)
            col1.metric("Severity", result.get("severity", "unknown"))
            col2.metric(
                "Incident Type",
                result.get("likely_incident_type", "unknown"),
            )

            st.subheader("Summary")
            st.write(result.get("summary", ""))

            st.subheader("Analyst Note")
            st.write(result.get("analyst_note", ""))

            st.subheader("MITRE-Style Mapping")
            for item in result.get("mitre_mapping", []):
                st.write(f"- {item}")

            st.subheader("Recommended Containment")
            for action in result.get("recommended_containment", []):
                st.write(f"- {action}")

            st.subheader("Recommended Investigation Steps")
            for step in result.get("recommended_investigation_steps", []):
                st.write(f"- {step}")

            st.subheader("False Positive Considerations")
            for consideration in result.get("false_positive_considerations", []):
                st.write(f"- {consideration}")

            st.subheader("Evidence Gaps")
            for gap in result.get("evidence_gaps", []):
                st.write(f"- {gap}")

            with st.expander("Full JSON response"):
                st.json(result)


elif mode == "Audit Logs":
    st.header("Audit Logs")

    try:
        response = requests.get(f"{API_BASE_URL}/logs", timeout=30)
        response.raise_for_status()

        logs = response.json().get("logs", [])

        if not logs:
            st.info("No audit logs yet. Run an analysis first.")
        else:
            st.dataframe(logs, use_container_width=True)

    except requests.exceptions.RequestException as exc:
        st.error(f"Could not load logs: {exc}")