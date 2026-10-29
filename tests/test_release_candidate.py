"""Release presentation checks; analysis and frozen scorers stay covered separately."""

import re
import subprocess
from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient
from test_dashboard import ENTRY, PAGES, open_page
from test_schemas import GOVERNANCE_INPUT, GOVERNANCE_RESPONSE

from app.main import app
from app.schemas import GovernanceRiskRequest, GovernanceRiskResponse
from app.version import APPLICATION_VERSION
from dashboard.exports import export_document, json_export, markdown_export
from dashboard.navigation import PAGE_GROUPS, WORKFLOW_MAP

ROOT = Path(__file__).resolve().parents[1]


def test_native_navigation_groups_and_default_overview():
    assert list(PAGE_GROUPS) == ["", "Workflows", "Platform"]
    assert [title for _, title in PAGE_GROUPS["Workflows"]] == [
        "SOC Investigation",
        "AI System Risk Review",
    ]
    assert [title for _, title in PAGE_GROUPS["Platform"]] == [
        "Platform Evaluation",
        "Activity",
        "About",
    ]
    assert PAGE_GROUPS[""] == (("pages/overview.py", "Overview"),)
    assert all(
        (ENTRY.parent / path).is_file()
        for pages in PAGE_GROUPS.values()
        for path, _ in pages
    )
    page = open_page("Overview")
    assert [title.value for title in page.title] == ["Overview"]
    assert not page.sidebar.selectbox
    assert not page.exception


def test_overview_two_active_two_planned_and_no_analysis_controls(monkeypatch):
    def no_network(*args, **kwargs):
        pytest.fail("Overview must not call a backend or model")

    monkeypatch.setattr(requests, "post", no_network)
    monkeypatch.setattr(requests, "get", no_network)
    page = open_page("Overview")
    captions = [c.value for c in page.caption]
    assert captions.count("Active") == captions.count("Planned") == 2
    assert {
        "Technical",
        "Policy / governance",
        "SOC Investigation",
        "SOC Policy & Governance Review",
        "AI Security Assessment",
        "AI System Risk Review",
    } <= {h.value for h in page.subheader}
    assert len(page.get("page_link")) == 2
    assert not page.get("form") and not page.get("download_button")
    assert [b.label for b in page.button] == ["Check backend status"]
    assert not page.exception


@pytest.mark.parametrize("row", WORKFLOW_MAP)
def test_planned_workflows_have_no_routes_or_actions(row):
    assert row["technical"]["status"] != row["governance"]["status"]
    for card in (row["technical"], row["governance"]):
        if card["status"] == "Planned":
            assert set(card) == {"title", "status", "description"}
            assert card["title"] not in [
                title for pages in PAGE_GROUPS.values() for _, title in pages
            ]
    routes = {route.path for route in app.routes}
    assert not any("ai-security-assessment" in p or "soc-policy" in p for p in routes)


@pytest.mark.parametrize("name", PAGES)
def test_normal_pages_have_no_obsolete_headings_or_slogans(monkeypatch, name):
    monkeypatch.setattr(
        requests,
        "get",
        lambda *a, **kw: (_ for _ in ()).throw(requests.ConnectionError()),
    )
    page = open_page(name)
    headings = [h.value for h in page.title] + [h.value for h in page.subheader]
    assert not {"Governance Review", "Evaluation Lab", "Trust & Integrity"} & set(
        headings
    )
    text = "\n".join(
        item.value
        for group in (page.caption, page.markdown, page.text)
        for item in group
    )
    assert "The model proposes." not in text
    assert "Coming soon" not in text
    assert not page.exception


def test_about_uses_native_readable_architecture_without_graph_or_image():
    page = open_page("About")
    assert {
        "Product scope",
        "Architecture",
        "Current release",
        "Operational boundaries",
    } <= {h.value for h in page.subheader}
    text = "\n".join(
        item.value for group in (page.markdown, page.text) for item in group
    )
    assert "1. Request" in text and "5. Result" in text
    assert (
        "SOC Investigation response" in text
        and "AI System Risk Review response" in text
    )
    assert not page.get("graphviz_chart") and not page.get("imgs")
    source = (ROOT / "dashboard/product_pages.py").read_text(encoding="utf-8")
    assert "st.container(border=True)" in source
    assert "st.graphviz_chart" not in source and "st.image" not in source
    assert "unsafe_allow_html" not in source
    assert not page.exception


def test_ai_system_risk_name_in_exports():
    document = export_document(
        GovernanceRiskRequest(**GOVERNANCE_INPUT),
        GovernanceRiskResponse(**GOVERNANCE_RESPONSE),
    )
    assert document["workflow"] == "AI System Risk Review"
    assert "AI System Risk Review Brief" in markdown_export(document)
    assert "Governance Review" not in json_export(document) + markdown_export(document)


def test_application_version_is_centralized_and_independent_of_scorers():
    assert APPLICATION_VERSION == "2.3.0rc1"
    with TestClient(app) as client:
        assert (
            app.version
            == client.get("/").json()["version"]
            == client.get("/ui/status").json()["version"]
            == APPLICATION_VERSION
        )


def test_release_documentation_local_links_resolve():
    paths = [
        ROOT / "README.md",
        ROOT / "Documentation/20_analyst_product_experience.md",
        ROOT / "Documentation/22_professional_release_candidate.md",
        ROOT / "Documentation/23_release_candidate_sprint_report.md",
        ROOT / "Documentation/demo_walkthrough.md",
    ]
    for path in paths:
        for target in re.findall(
            r"\]\(([^)]+)\)", path.read_text(encoding="utf-8-sig")
        ):
            if not target.startswith(("https://", "http://", "#")):
                assert (path.parent / target.split("#", 1)[0]).is_file(), (path, target)


def test_exact_snapshot_covers_unchanged_readable_direct_manifest():
    lines = (
        (ROOT / "requirements-windows-py313.lock.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    assert "-r requirements.txt" in lines
    pins = [line for line in lines if line and not line.startswith(("#", "-r "))]
    assert pins and all(
        re.fullmatch(r"[A-Za-z0-9_.-]+==[A-Za-z0-9_.+!-]+", line) for line in pins
    )
    names = [line.split("==")[0].lower().replace("_", "-") for line in pins]
    assert len(names) == len(set(names))
    for line in (ROOT / "requirements.txt").read_text().splitlines():
        if line and not line.startswith("#"):
            name = re.split(r"[<>=\[]", line)[0].lower().replace("_", "-")
            assert name in names


def test_frozen_v32_files_override_windows_newline_conversion():
    paths = [
        "evals/cases/semantic_grounding_v3_2.json",
        "Documentation/evaluation_v3_2/manual_review.md",
        "Documentation/evaluation_v3_2/failure_triage.md",
        "Documentation/evaluation_v3_2/treatment_manual_review.md",
        "Documentation/evaluation_v3_2/treatment_failure_triage.md",
    ]
    attributes = subprocess.check_output(
        ["git", "check-attr", "eol", "--", *paths], cwd=ROOT, text=True
    ).splitlines()
    assert len(attributes) == len(paths)
    assert all(line.endswith(": eol: lf") for line in attributes)
