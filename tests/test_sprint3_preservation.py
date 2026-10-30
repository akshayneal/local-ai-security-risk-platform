import json
import subprocess

from historical_identity import sprint4_blob

from evals.provenance import ROOT


def test_sprint3_frozen_evidence_and_prior_production_identity():
    manifest = json.loads(
        (ROOT / "Documentation/expansion_sprint_3_preservation.json").read_bytes()
    )
    assert manifest["starting_commit"] == "949d4cbdc3320a2bd409702d6e26fc6e98cff1fb"
    assert set(manifest["authorized_prior_source_git_blob_sha1"]) == {
        "app/ollama_client.py",
        "app/soc_analyzer.py",
        "app/output_policy.py",
        "app/prompts.py",
        "app/main.py",
        "dashboard/api_client.py",
        "dashboard/microsoft_input.py",
    }
    for name, expected in manifest["frozen_git_blob_sha1"].items():
        assert sprint4_blob(name) == expected, name
    for name, expected in manifest["authorized_prior_source_git_blob_sha1"].items():
        assert (
            subprocess.check_output(
                ["git", "rev-parse", f"{manifest['starting_commit']}:{name}"],
                cwd=ROOT,
                text=True,
            ).strip()
            == expected
        )
