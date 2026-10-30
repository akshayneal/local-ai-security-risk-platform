"""The correction feature authorizes only five existing integration modules."""

import subprocess

from evals.provenance import ROOT


def test_corrections_preserve_frozen_evaluations_and_analysis_implementation():
    changed = subprocess.check_output(
        [
            "git",
            "diff",
            "4f7009ec198710f0495e8c5f2e5dce9a19593496",
            "6be3887617dfac1b95c09d672f5fa5acaabb9e08",
            "--name-only",
            "--",
            "app",
            "dashboard",
            "evals",
            "reference_material",
            "Documentation",
            "AGENTS.md",
            "README.md",
            "requirements.txt",
            "requirements-windows-py313.lock.txt",
            ".github",
            ".gitattributes",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    assert set(changed) <= {
        "app/evidence_inspector.py",
        "dashboard/evidence_inspector.py",
        "dashboard/exports.py",
        "dashboard/workflows.py",
        "dashboard/microsoft_input.py",
        "Documentation/43_analyst_corrections.md",
        "Documentation/44_evidence_precision_and_reviewed_reports.md",
        "Documentation/45_development_launcher.md",
    }


def test_precision_sprint_changes_only_inspector_reporting_and_new_documentation():
    changed = subprocess.check_output(
        [
            "git",
            "diff",
            "3b51f9ed2f0ba765fe82b99a50771a5109748feb",
            "6be3887617dfac1b95c09d672f5fa5acaabb9e08",
            "--name-only",
            "--",
            "app",
            "dashboard",
            "evals",
            "reference_material",
            "Documentation",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    assert set(changed) <= {
        "app/evidence_inspector.py",
        "dashboard/evidence_inspector.py",
        "dashboard/exports.py",
        "Documentation/44_evidence_precision_and_reviewed_reports.md",
        "Documentation/45_development_launcher.md",
    }
