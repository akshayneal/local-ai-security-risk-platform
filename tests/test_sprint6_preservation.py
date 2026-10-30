"""Only the explicitly authorized Sprint 6 delta may change; old evidence stays live."""

import hashlib
import json
import subprocess

from evals.provenance import ROOT

BASE = "a43814b43df9bd677469f002c785ac0710c4404d"


def plan():
    return json.loads((ROOT / "Documentation/sprint6_preservation.json").read_bytes())


def test_sprint6_scope_and_all_other_base_blobs_preserved():
    manifest = plan()
    assert manifest["base_commit"] == BASE
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE, "HEAD"], cwd=ROOT, check=True
    )
    changed = subprocess.check_output(
        ["git", "diff", BASE, "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    allowed = set(manifest["authorized_existing"]) | set(manifest["authorized_new"])
    assert all(
        p in allowed or p.startswith(tuple(manifest["authorized_new_prefixes"]))
        for p in changed
    )
    protected = manifest["protected_git_blobs"]
    actual = subprocess.check_output(
        ["git", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        text=True,
        input="\n".join(protected) + "\n",
    ).splitlines()
    assert dict(zip(protected, actual, strict=True)) == protected
    assert not any(
        p.startswith(("evals/", "reference_material/", "scripts/"))
        for p in manifest["authorized_existing"]
    )


def test_sprint5_scope_range_only_is_pinned_without_changing_its_other_guards():
    source = (ROOT / "tests/test_sprint5_preservation.py").read_text()
    original = subprocess.check_output(
        ["git", "show", BASE + ":tests/test_sprint5_preservation.py"],
        cwd=ROOT,
        text=True,
    )
    # Compare every executable AST node, ignoring only formatting and locations.
    import ast

    expected = ast.parse(original)
    for node in ast.walk(expected):
        if (
            isinstance(node, ast.List)
            and len(node.elts) >= 4
            and isinstance(node.elts[2], ast.Name)
            and node.elts[2].id == "BASE"
        ):
            if ast.dump(node.elts[0]) == ast.dump(ast.Constant("git")) and ast.dump(
                node.elts[1]
            ) == ast.dump(ast.Constant("diff")):
                node.elts.insert(3, ast.Constant(BASE))
                break
    else:
        raise AssertionError("Historic diff call not found")
    assert ast.dump(ast.parse(source)) == ast.dump(expected)


def test_installed_policy_and_preexisting_workspace_remain_byte_identical():
    manifest = plan()
    if (ROOT / "evals/results/s4check").exists():
        assert (
            hashlib.sha256((ROOT / "AGENTS.md").read_bytes()).hexdigest()
            == manifest["installed_agents_sha256"]
        )
    workspace = ROOT / "knowledge_base/workspaces/northstar-sprint5"
    if workspace.exists():
        actual = {p.as_posix() for p in workspace.iterdir() if p.is_file()} | {
            p.as_posix() for p in (workspace / "documents").iterdir()
        }
        expected = {
            str(ROOT / p).replace("\\", "/")
            for p in manifest["protected_workspace_sha256"]
        }
        assert actual == expected
        for name, expected_hash in manifest["protected_workspace_sha256"].items():
            assert (
                hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected_hash
            ), name
