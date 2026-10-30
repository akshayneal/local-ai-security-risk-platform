"""Read-only workspace inspection and a permission-neutral analysis opt-in."""

import streamlit as st

from dashboard.api_client import get_data


def knowledge_checkbox(prefix: str) -> bool:
    return st.checkbox(
        "Include reviewed local knowledge (experimental)",
        value=False,
        key=f"{prefix}_local_knowledge",
        help="Requires a valid operator-configured workspace on the backend. This checkbox grants no access or policy scope. Default off; invalid workspaces withhold analysis.",
    )


def knowledge_page(base_url: str) -> None:
    st.title("Knowledge Workspace")
    st.caption("EXPERIMENTAL · read-only · single-user local demonstration")
    st.write(
        "Documents enter only through intentional local CLI registration and exact-version metadata review. This page cannot upload, read arbitrary paths, approve documents or grant access."
    )
    status, error = get_data(base_url, "/ui/knowledge/status")
    if error:
        st.info(error)
        return
    st.text(f"Workspace: {status.get('status', 'unavailable')}")
    st.info(status.get("message", "Workspace unavailable."))
    if status.get("status") == "experimental":
        st.text(
            f"Registered documents: {status['registered_documents']} · Approved documents: {status['approved_documents']}"
        )
        for workflow, details in status.get("workflows", {}).items():
            st.subheader(workflow)
            st.caption(
                "Eligible current chunks, before ranking. Per-analysis selected and cited status appears in the Evidence Inspector."
            )
            st.dataframe(details, hide_index=True, width="stretch")
    st.caption(
        "No complete raw documents or hidden grants are returned. Source titles/identities may still be sensitive. Eligibility is not authentication, semantic support, implementation evidence or permission to act."
    )
    st.code(
        ".\\.venv\\Scripts\\python.exe -m scripts.knowledge_workspace init northstar --demo\n.\\.venv\\Scripts\\python.exe -m scripts.knowledge_workspace register northstar\n.\\.venv\\Scripts\\python.exe -m scripts.knowledge_workspace status northstar",
        language="powershell",
    )
