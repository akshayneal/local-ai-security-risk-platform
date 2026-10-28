"""Verify old source identities at the treatment boundary, not against new behavior.

Only the explicitly authorized production and associated-test paths use history.
Every other frozen suite/scorer/artifact remains checked against current bytes.
CI fetches history so historical checks never silently skip verification.
"""

import json
import subprocess

from evals.provenance import ROOT


def historical_blob(name: str) -> str:
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
    return subprocess.check_output(
        ["git", "hash-object", f"--path={name}", name], cwd=ROOT, text=True
    ).strip()
