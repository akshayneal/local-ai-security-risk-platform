import json
import subprocess

from evals.provenance import ROOT


def test_sprint3_frozen_evidence_and_prior_production_identity():
    manifest = json.loads(
        (ROOT / "Documentation/expansion_sprint_3_preservation.json").read_bytes()
    )
    assert manifest["starting_commit"] == "949d4cbdc3320a2bd409702d6e26fc6e98cff1fb"
    for name, expected in manifest["frozen_git_blob_sha1"].items():
        assert (
            subprocess.check_output(
                ["git", "hash-object", f"--path={name}", name], cwd=ROOT, text=True
            ).strip()
            == expected
        ), name
    for name, expected in manifest["authorized_prior_source_git_blob_sha1"].items():
        assert (
            subprocess.check_output(
                ["git", "rev-parse", f"{manifest['starting_commit']}:{name}"],
                cwd=ROOT,
                text=True,
            ).strip()
            == expected
        )
