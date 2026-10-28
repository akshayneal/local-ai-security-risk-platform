"""Streamlit entrypoint. Run from the repository with python -m streamlit."""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Streamlit also executes this file with dashboard/ as the script directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard.api_client import get_data
from dashboard.product_pages import about_page, activity_page, evaluation_page
from dashboard.workflows import workflow_page

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Local AI | Analyst Workspace", layout="wide")
st.title("Local AI Security Workspace")
st.caption("ANALYST SUPPORT · SOC INVESTIGATION & AI GOVERNANCE")

page = st.sidebar.selectbox(
    "Workspace",
    ["SOC Investigation", "Governance Review", "Evaluation Lab", "Activity", "About"],
)
st.sidebar.caption("The model proposes. Humans decide.")
if st.sidebar.button("Check backend status"):
    status, error = get_data(API_BASE_URL, "/ui/status")
    if error:
        st.sidebar.info(error)
    else:
        st.sidebar.success("FastAPI available")
        st.sidebar.text(f"Version: {status.get('version', 'Unknown')}")
        st.sidebar.text(f"Configured model: {status.get('model', 'Unknown')}")
        st.sidebar.caption(
            "Backend readiness only; model availability is checked when analysis is submitted."
        )

if page in {"SOC Investigation", "Governance Review"}:
    workflow_page(API_BASE_URL, soc=page == "SOC Investigation")
elif page == "Evaluation Lab":
    evaluation_page()
elif page == "Activity":
    activity_page(API_BASE_URL)
else:
    about_page()
