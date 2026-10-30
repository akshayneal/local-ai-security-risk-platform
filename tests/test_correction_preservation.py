"""The correction feature authorizes only five existing integration modules."""

import subprocess

from evals.provenance import ROOT


def test_corrections_preserve_frozen_evaluations_and_analysis_implementation():
    changed = subprocess.check_output(
        [
            "git", "diff", "4f7009ec198710f0495e8c5f2e5dce9a19593496",
            "--name-only", "--", "app", "dashboard", "evals", "reference_material",
            "Documentation", "AGENTS.md", "README.md", "requirements.txt",
            "requirements-windows-py313.lock.txt", ".github", ".gitattributes",
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
    }
