"""Current-tree scope and byte preservation; historical tests replay fixed history."""

import ast
import hashlib
import json
import subprocess

import pytest

from evals.provenance import ROOT

END = "1c4f937f2b067a4a2b0d8ac8cf5db4f552555d00"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def manifest():
    return json.loads((ROOT / "Documentation/sprint7_preservation.json").read_bytes())


def assert_scope(names, allowed):
    assert not set(names) - set(allowed), "Unauthorized current-tree paths"


def test_current_scope_and_protected_base_blobs():
    plan = manifest()
    assert plan["base_commit"] == plan["historical_end_commit"] == END
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", END, "HEAD"], cwd=ROOT, check=True
    )
    allowed = set(plan["authorized_existing"]) | set(plan["authorized_new"])
    changed = git("diff", END, "--name-only").splitlines()
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    assert_scope(
        changed + [p for p in untracked if not p.startswith("evals/results/s4check/")],
        allowed,
    )
    protected = plan["protected_git_blobs"]
    actual = subprocess.check_output(
        ["git", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        text=True,
        input="\n".join(protected) + "\n",
    ).splitlines()
    assert dict(zip(protected, actual, strict=True)) == protected
    assert all(
        not p.startswith(("scripts/demo/", "app/", "reference_material/"))
        for p in plan["authorized_existing"]
    )


def test_all_inherited_file_sets_and_exact_bytes():
    plan = manifest()
    s5 = json.loads((ROOT / plan["original_snapshot_manifest"]).read_bytes())
    s6 = json.loads((ROOT / plan["workspace_manifest"]).read_bytes())
    inherited = (
        s5["preexisting_untracked_sha256"] | plan["protected_inherited_cache_sha256"]
    )
    for directory, files in [
        ("evals/results/s4check", inherited),
        (
            "knowledge_base/workspaces/northstar-sprint5",
            s6["protected_workspace_sha256"],
        ),
    ]:
        root = ROOT / directory
        if root.exists():
            actual = {
                p.relative_to(ROOT).as_posix() for p in root.rglob("*") if p.is_file()
            }
            assert actual == set(files), "Inherited extra/missing file"
            for name, digest in files.items():
                assert (
                    hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                ), name
    agents = (ROOT / "AGENTS.md").read_bytes()
    if (ROOT / "evals/results/s4check").exists():
        assert hashlib.sha256(agents).hexdigest() == plan["installed_agents_sha256"]
    assert (
        git("hash-object", "AGENTS.md").strip()
        == plan["protected_git_blobs"]["AGENTS.md"]
    )
    assert not git("ls-files", "--", "evals/results/s4check").strip()
    assert "evals/results/s4check/" not in git("diff", "--cached", "--name-only")


def expected_historic_source(sprint):
    """Allow only the immutable endpoint/snapshot substitutions, no assertion edits."""
    source = git("show", f"{END}:tests/test_sprint{sprint}_preservation.py")
    variable = "hashes" if sprint == 5 else "actual"
    begin = source.index(
        f'    {variable} = subprocess.check_output(\n        ["git", "hash-object", "--stdin-paths"],'
    )
    finish = source.index("    assert dict(zip(", begin)
    source = (
        source[:begin]
        + f'''    snapshot = subprocess.check_output(
        ["git", "ls-tree", "-r", "{END}"], cwd=ROOT, text=True
    ).splitlines()
    by_path = {{line.split("\\t")[1]: line.split()[2] for line in snapshot}}
    {variable} = [by_path[name] for name in protected]
'''
        + source[finish:]
    )
    if sprint == 6:
        source = source.replace(
            '["git", "diff", BASE, "--name-only"]',
            f'["git", "diff", BASE, "{END}", "--name-only"]',
        )
        source = source.replace(
            'source = (ROOT / "tests/test_sprint5_preservation.py").read_text()',
            f'''source = subprocess.check_output(
        ["git", "show", "{END}:tests/test_sprint5_preservation.py"],
        cwd=ROOT, text=True,
    )''',
        )
    return source


@pytest.mark.parametrize("sprint", [5, 6])
def test_historic_executable_ast_changed_only_to_pin_endpoints(sprint):
    expected = ast.dump(ast.parse(expected_historic_source(sprint)))
    current = ast.dump(
        ast.parse((ROOT / f"tests/test_sprint{sprint}_preservation.py").read_text())
    )
    assert current == expected
    # Even one changed original assertion must be detected by the AST guard.
    hostile = expected_historic_source(sprint).replace("assert ", "assert True or ", 1)
    assert ast.dump(ast.parse(hostile)) != expected


def test_historical_and_current_guards_reject_unauthorized_changes():
    s6 = json.loads(git("show", END + ":Documentation/sprint6_preservation.json"))
    allowed = set(s6["authorized_existing"]) | set(s6["authorized_new"])
    names = git("diff", s6["base_commit"], END, "--name-only").splitlines()
    prefixes = tuple(s6["authorized_new_prefixes"])
    assert all(p in allowed or p.startswith(prefixes) for p in names)
    unauthorized = "app/ollama_client.py"
    assert not all(
        p in allowed or p.startswith(prefixes) for p in names + [unauthorized]
    )
    assert (
        git("rev-parse", END + ":" + unauthorized).strip()
        == s6["protected_git_blobs"][unauthorized]
    )
    with pytest.raises(AssertionError, match="Unauthorized current-tree"):
        assert_scope([unauthorized], manifest()["authorized_existing"])
    # Byte hashing detects content changes even if path scope were unchanged.
    data = (ROOT / unauthorized).read_bytes()
    assert (
        hashlib.sha256(data).digest() != hashlib.sha256(data + b"\n# changed").digest()
    )
