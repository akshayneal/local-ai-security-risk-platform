"""In-process AppTest only; no browser, screenshots, server or live model."""

from types import SimpleNamespace

import pytest
import requests
from streamlit.testing.v1 import AppTest
from test_dashboard import ENTRY, button, fake_post, open_page

from dashboard.navigation import PILLARS


@pytest.mark.parametrize("soc", [True, False])
def test_optin_checkbox_defaults_off_and_sends_boolean_only(monkeypatch, soc):
    calls = fake_post(monkeypatch, soc=soc)
    page = open_page("SOC Investigation" if soc else "AI System Risk Review")
    checkbox = next(c for c in page.checkbox if "reviewed local knowledge" in c.label)
    assert checkbox.value is False
    # Form values reach the script together on submit. Do not inject a separate
    # script rerun between editing a form control and clicking its submit button.
    checkbox.check()
    assert checkbox.value is True
    button(page, "Analyze SOC alert" if soc else "Review AI system").click().run()
    assert len(calls) == 1 and calls[0][1]["local_knowledge"] is True
    assert not {"access_scopes", "policy_scopes", "workspace"} & calls[0][1].keys()
    prefix = "soc" if soc else "gov"
    assert (
        "local_knowledge"
        not in page.session_state[f"{prefix}_result"]["submitted_input"]
    )
    assert not page.exception


@pytest.mark.parametrize("status", ["disabled", "unavailable", "experimental"])
def test_knowledge_page_readonly_and_missing_workspace_visible(monkeypatch, status):
    requested = []

    def get(url, **kw):
        requested.append(url)
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {
                "status": status,
                "message": "Safe workspace diagnostic",
                "registered_documents": 8,
                "approved_documents": 7,
                "workflows": {
                    "soc_investigation": [
                        {
                            "title": "Synthetic",
                            "version": "v1",
                            "authority": "unverified_material",
                        }
                    ]
                },
            },
        )

    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr(
        requests, "post", lambda *a, **kw: pytest.fail("read-only page")
    )
    page = AppTest.from_file(ENTRY, default_timeout=15).run()
    page.switch_page("pages/knowledge_workspace.py").run()
    assert requested[-1].endswith("/ui/knowledge/status")
    assert not page.get("file_uploader") and not page.text_input and not page.checkbox
    assert not page.exception


def test_three_pillars_have_only_two_runnable_pages():
    assert len(PILLARS) == 3
    assert sum("page" in p for p in PILLARS) == 2
    planned = next(p for p in PILLARS if p["title"] == "AI Security")
    assert planned["status"] == "Planned" and "page" not in planned
