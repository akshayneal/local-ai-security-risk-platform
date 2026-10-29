import json
import subprocess

from evals.provenance import ROOT


def test_prior_evidence_and_unmodified_source_bytes_preserved():
    manifest = json.loads(
        (ROOT / "Documentation/grounding_stabilization_preservation.json").read_bytes()
    )
    assert manifest["starting_commit"] == "73fd92cb8445ac39beab50ee13b8b47c5aa09e47"
    assert set(manifest["authorized_prior_source_git_blob_sha1"]) == {
        "app/soc_analyzer.py",
        "app/governance_analyzer.py",
        "app/prompts.py",
    }
    protected = manifest["unchanged_git_blob_sha1"]
    actual = subprocess.check_output(
        ["git", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        input="\n".join(protected) + "\n",
        text=True,
    ).splitlines()
    assert dict(zip(protected, actual, strict=True)) == protected
    for name, expected in manifest["authorized_prior_source_git_blob_sha1"].items():
        assert (
            subprocess.check_output(
                ["git", "rev-parse", f"{manifest['starting_commit']}:{name}"],
                cwd=ROOT,
                text=True,
            ).strip()
            == expected
        )
