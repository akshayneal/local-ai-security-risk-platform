"""Verify old source identities at the treatment boundary, not against new behavior.

Only the explicitly authorized production and associated-test paths use history.
Every other frozen suite/scorer/artifact remains checked against current bytes.
CI fetches history so historical checks never silently skip verification.
"""

import json
import subprocess

from evals.provenance import ROOT


def expansion_blob(name: str) -> str:
    """Four explicitly authorized integration paths retain their prior identity."""
    sprint3 = json.loads(
        (ROOT / "Documentation/expansion_sprint_3_preservation.json").read_bytes()
    )
    if name in sprint3["authorized_prior_source_git_blob_sha1"] and name not in {
        "app/soc_analyzer.py",
        "app/governance_analyzer.py",
        "dashboard/workflows.py",
        "dashboard/sample_loader.py",
    }:
        value = subprocess.check_output(
            ["git", "rev-parse", f"{sprint3['starting_commit']}:{name}"],
            cwd=ROOT,
            text=True,
        ).strip()
        assert value == sprint3["authorized_prior_source_git_blob_sha1"][name]
        return value
    manifest = json.loads(
        (ROOT / "Documentation/expansion_sprint_2_preservation.json").read_bytes()
    )
    allowed = {
        "app/soc_analyzer.py",
        "app/governance_analyzer.py",
        "dashboard/workflows.py",
        "dashboard/sample_loader.py",
    }
    assert set(manifest["authorized_prior_source_git_blob_sha1"]) == allowed
    assert manifest["starting_commit"] == "8faa103087475be15ef1fc4ee3166dacb56a6d1c"
    if name in allowed:
        value = subprocess.check_output(
            ["git", "rev-parse", f"{manifest['starting_commit']}:{name}"],
            cwd=ROOT,
            text=True,
        ).strip()
        assert value == manifest["authorized_prior_source_git_blob_sha1"][name]
        return value
    return subprocess.check_output(
        ["git", "hash-object", f"--path={name}", name], cwd=ROOT, text=True
    ).strip()


def historical_blob(name: str) -> str:
    productization = json.loads(
        (ROOT / "Documentation/productization_preservation.json").read_bytes()
    )
    if name in productization["authorized_prior_source_git_blob_sha1"]:
        return productization_blob(name)
    preservation = json.loads(
        (
            ROOT / "Documentation/evaluation_v3_2/semantic_hardening_preservation.json"
        ).read_bytes()
    )
    if name in preservation["authorized_prior_source_git_blob_sha1"]:
        value = subprocess.check_output(
            ["git", "rev-parse", f"{preservation['starting_commit']}:{name}"],
            cwd=ROOT,
            text=True,
        ).strip()
        assert value == preservation["authorized_prior_source_git_blob_sha1"][name]
        return value
    return expansion_blob(name)


def productization_blob(name: str) -> str:
    """Only authorized UI/plumbing paths use history; frozen evidence stays live-checked."""
    manifest = json.loads(
        (ROOT / "Documentation/productization_preservation.json").read_bytes()
    )
    if name in manifest["authorized_prior_source_git_blob_sha1"]:
        value = subprocess.check_output(
            ["git", "rev-parse", f"{manifest['starting_commit']}:{name}"],
            cwd=ROOT,
            text=True,
        ).strip()
        assert value == manifest["authorized_prior_source_git_blob_sha1"][name]
        return value
    return expansion_blob(name)
