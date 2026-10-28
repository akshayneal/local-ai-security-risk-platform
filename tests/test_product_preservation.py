"""Protect frozen evidence and all unchanged analysis behavior for productization."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_artifacts_scorers_and_analysis_implementation_unchanged():
    manifest = json.loads(
        (ROOT / "Documentation/productization_preservation.json").read_bytes()
    )
    assert set(manifest["authorized_prior_source_git_blob_sha1"]) == {
        "app/main.py",
        "dashboard/streamlit_app.py",
        "tests/test_dashboard.py",
    }
    assert manifest["starting_commit"] == "c5e187e4e9bb02f5e1ce666b84716fa72e66c820"
    for name, expected in manifest["unchanged_git_blob_sha1"].items():
        actual = subprocess.check_output(
            ["git", "hash-object", f"--path={name}", name], cwd=ROOT, text=True
        ).strip()
        assert actual == expected, name
    for name, expected in manifest["authorized_prior_source_git_blob_sha1"].items():
        actual = subprocess.check_output(
            ["git", "rev-parse", f"{manifest['starting_commit']}:{name}"],
            cwd=ROOT,
            text=True,
        ).strip()
        assert actual == expected, name
