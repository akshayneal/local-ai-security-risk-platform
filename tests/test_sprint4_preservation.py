import json
import subprocess

from historical_identity import sprint4_blob, sprint5_blob

from evals.provenance import ROOT


def test_prior_mini_sprint_and_unmodified_source_are_preserved():
    manifest = json.loads(
        (ROOT / "Documentation/expansion_sprint_4_preservation.json").read_bytes()
    )
    assert manifest["starting_commit"] == "47f038602b03b38854dfe82024941f2d4204ca76"
    paths = manifest["unchanged_git_blob_sha1"]
    actual = subprocess.check_output(
        ["git", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        input="\n".join(paths) + "\n",
        text=True,
    ).splitlines()
    actual = dict(zip(paths, actual, strict=True))
    sprint5 = json.loads(
        (ROOT / "Documentation/sprint5_preservation.json").read_bytes()
    )
    for name in set(paths) & set(sprint5["authorized_existing"]):
        actual[name] = sprint5_blob(name)
    assert actual == paths
    for name, expected in manifest["authorized_prior_source_git_blob_sha1"].items():
        assert sprint4_blob(name) == expected
