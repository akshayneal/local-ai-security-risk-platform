"""Verify old source identities at the treatment boundary, not against new behavior.

Only the explicitly authorized production and associated-test paths use history.
Every other frozen suite/scorer/artifact remains checked against current bytes.
CI fetches history so historical checks never silently skip verification.
"""

import json
import subprocess

from evals.provenance import ROOT


def sprint5_blob(name: str) -> str:
    """Only named Sprint 5 source edits use their verified pre-sprint blob.

    Frozen historical data/scorers remain checked against current files. The new
    scope guard separately bounds this sprint and preserves the installed policy.
    """
    manifest = json.loads(
        (ROOT / "Documentation/sprint5_preservation.json").read_bytes()
    )
    if name in manifest["authorized_existing"]:
        actual = subprocess.check_output(
            ["git", "rev-parse", f"{manifest['base_commit']}:{name}"],
            cwd=ROOT,
            text=True,
        ).strip()
        assert actual == manifest["authorized_existing"][name]
        return actual
    return subprocess.check_output(
        ["git", "hash-object", f"--path={name}", name], cwd=ROOT, text=True
    ).strip()


def sprint4_blob(name: str) -> str:
    """Only six explicitly authorized additive workbench paths use prior identity."""
    manifest = json.loads(
        (ROOT / "Documentation/expansion_sprint_4_preservation.json").read_bytes()
    )
    allowed = manifest["authorized_prior_source_git_blob_sha1"]
    assert set(allowed) == {
        "app/main.py",
        "app/ui_schemas.py",
        "app/retrieval/orchestration.py",
        "dashboard/workflows.py",
        "dashboard/microsoft_input.py",
        "dashboard/exports.py",
    }
    if name in allowed:
        actual = subprocess.check_output(
            ["git", "rev-parse", f"{manifest['starting_commit']}:{name}"],
            cwd=ROOT,
            text=True,
        ).strip()
        assert actual == allowed[name]
        return actual
    return sprint5_blob(name)


def expansion_blob(name: str) -> str:
    """Four explicitly authorized integration paths retain their prior identity."""
    if name in {
        "app/ui_schemas.py",
        "dashboard/exports.py",
        "app/retrieval/orchestration.py",
    }:
        return sprint4_blob(name)
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
    return sprint5_blob(name)


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
