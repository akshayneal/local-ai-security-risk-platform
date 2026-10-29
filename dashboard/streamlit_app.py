"""Streamlit entrypoint. Run from the repository with python -m streamlit."""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Streamlit also executes this file with dashboard/ as the script directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard.api_client import get_data
from dashboard.navigation import PAGE_GROUPS

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Local AI Security Risk Platform", layout="wide")
page = st.navigation(
    {
        group: [
            st.Page(path, title=title, default=title == "Overview")
            for path, title in pages
        ]
        for group, pages in PAGE_GROUPS.items()
    },
    expanded=True,
)
if st.sidebar.button("Check backend status"):
    status, error = get_data(API_BASE_URL, "/ui/status")
    if error:
        st.sidebar.info(error)
    else:
        st.sidebar.caption("Backend: Available")
        st.sidebar.text(f"Version: {status.get('version', 'Unknown')}")
        st.sidebar.text(f"Configured model: {status.get('model', 'Unknown')}")
        st.sidebar.caption("Model availability is checked on submission.")

page.run()
