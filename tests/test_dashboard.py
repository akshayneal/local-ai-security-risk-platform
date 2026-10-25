from types import SimpleNamespace

import pytest
import requests
from streamlit.testing.v1 import AppTest
from test_schemas import SOC_RESPONSE


@pytest.mark.parametrize("with_findings", [False, True])
def test_soc_dashboard_displays_findings_and_accepts_older_results(
    monkeypatch, with_findings
):
    result = SOC_RESPONSE.copy()
    if with_findings:
        result.update(
            observed_evidence=["Failed login recorded."],
            analyst_inferences=["Possible credential misuse."],
        )
    calls = []

    def post(url, *, json, timeout):
        calls.append((url, json, timeout))
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: result)

    monkeypatch.setattr(requests, "post", post)
    dashboard = AppTest.from_file(
        "dashboard/streamlit_app.py", default_timeout=15
    ).run()
    dashboard.sidebar.selectbox[0].select("SOC Alert Triage").run()
    dashboard.button[0].click().run()
    assert not dashboard.exception
    headings = [item.value for item in dashboard.subheader]
    assert (
        headings.index("Observed Evidence")
        < headings.index("Analyst Inferences")
        < headings.index("Analyst Note")
    )
    assert len(calls) == 1
    assert calls[0][0].endswith("/analyze/soc-alert")
    if with_findings:
        text = "\n".join(item.value for item in dashboard.markdown)
        assert "Failed login recorded." in text
        assert "Possible credential misuse." in text
