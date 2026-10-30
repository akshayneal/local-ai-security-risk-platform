import json
import subprocess

from historical_identity import sprint4_blob, sprint5_blob

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
    actual = dict(zip(protected, actual, strict=True))
    sprint4 = json.loads(
        (ROOT / "Documentation/expansion_sprint_4_preservation.json").read_bytes()
    )
    for name in sprint4["authorized_prior_source_git_blob_sha1"]:
        if name in actual:
            actual[name] = sprint4_blob(name)
    sprint5 = json.loads(
        (ROOT / "Documentation/sprint5_preservation.json").read_bytes()
    )
    for name in set(protected) & set(sprint5["authorized_existing"]):
        if name not in sprint4["authorized_prior_source_git_blob_sha1"]:
            actual[name] = sprint5_blob(name)
    assert actual == protected
    for name, expected in manifest["authorized_prior_source_git_blob_sha1"].items():
        assert (
            subprocess.check_output(
                ["git", "rev-parse", f"{manifest['starting_commit']}:{name}"],
                cwd=ROOT,
                text=True,
            ).strip()
            == expected
        )
