"""Current sprint scope, immutable historical resources and installed user policy."""

import hashlib
import json
import subprocess

from evals.provenance import ROOT

BASE = "6be3887617dfac1b95c09d672f5fa5acaabb9e08"


def manifest():
    return json.loads((ROOT / "Documentation/sprint5_preservation.json").read_bytes())


def test_sprint5_scope_and_protected_historical_bytes():
    plan = manifest()
    assert plan["base_commit"] == BASE
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE, "HEAD"], cwd=ROOT, check=True
    )
    changed = subprocess.check_output(
        [
            "git",
            "diff",
            BASE,
            "a43814b43df9bd677469f002c785ac0710c4404d",
            "--name-only",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    allowed = set(plan["authorized_existing"]) | set(plan["authorized_new"])
    assert all(
        p in allowed or p.startswith(tuple(plan["authorized_new_prefixes"]))
        for p in changed
    )
    protected = plan["protected_git_blobs"]
    snapshot = subprocess.check_output(
        ["git", "ls-tree", "-r", "1c4f937f2b067a4a2b0d8ac8cf5db4f552555d00"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    by_path = {line.split("\t")[1]: line.split()[2] for line in snapshot}
    hashes = [by_path[name] for name in protected]
    assert dict(zip(protected, hashes, strict=True)) == protected
    # Explicitly immutable semantics: neither frozen scorers/data nor dependencies
    # may be placed in an authorized source exception.
    assert not any(
        p.startswith(("evals/", "reference_material/"))
        for p in plan["authorized_existing"]
    )
    policy = (ROOT / "AGENTS.md").read_bytes()
    assert (
        hashlib.sha256(policy.replace(b"\r\n", b"\n")).hexdigest()
        == plan["installed_agents_lf_sha256"]
    )
    if (ROOT / "evals/results/s4check").exists():
        # Preserve this user's installed bytes, including mixed line endings.
        # A fresh clone has Git-normalized text, not the original transport bytes.
        assert hashlib.sha256(policy).hexdigest() == plan["installed_agents_sha256"]


def test_policy_portability_is_bound_to_the_unchanged_policy_checkpoint():
    plan = manifest()
    original = subprocess.check_output(["git", "show", "9af0344:AGENTS.md"], cwd=ROOT)
    assert hashlib.sha256(original).hexdigest() == plan["installed_agents_lf_sha256"]
    assert original == (ROOT / "AGENTS.md").read_bytes().replace(b"\r\n", b"\n")
    assert (
        hashlib.sha256(
            original.replace(b"\n", b"\r\n").replace(b"\r\n", b"\n")
        ).hexdigest()
        == plan["installed_agents_lf_sha256"]
    )
    assert (
        hashlib.sha256(original + b"\nunauthorized policy change").hexdigest()
        != plan["installed_agents_lf_sha256"]
    )


def test_fixed_historical_ranges_keep_the_original_allowlists():
    source = (ROOT / "tests/test_correction_preservation.py").read_text()
    assert source.count(f'"{BASE}"') == 2
    assert "app/knowledge_workspace.py" not in source
    assert 'AGENTS.md",\n    }' not in source


def test_preexisting_snapshot_preserved_if_present():
    # A clean clone has no copy. A partially removed/modified inherited copy fails.
    plan = manifest()
    if (ROOT / "evals/results/s4check").exists():
        for name, digest in plan["preexisting_untracked_sha256"].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, (
                name
            )
    staged = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True
    )
    tracked = subprocess.check_output(
        ["git", "ls-files", "--", "evals/results/s4check"], cwd=ROOT, text=True
    )
    assert "evals/results/s4check/" not in staged and not tracked
