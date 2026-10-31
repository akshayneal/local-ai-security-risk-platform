"""Current exact-path scope, inherited bytes and historical assertion preservation."""

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from sprint8_history import _snapshot

ROOT = Path(__file__).resolve().parents[1]
BASE = "f85e67fbd224fa020d0d904b62b6f8d7fd0b5e24"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def manifest():
    return json.loads((ROOT / "Documentation/sprint9_preservation.json").read_bytes())


def assert_scope(names, allowed):
    assert not set(names) - set(allowed), "Unauthorized Sprint 9 path"


def test_current_scope_and_every_other_baseline_blob():
    plan = manifest()
    assert plan["base_commit"] == BASE
    allowed = set(plan["authorized_existing"]) | set(plan["authorized_new"])
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE, "HEAD"], cwd=ROOT, check=True
    )
    untracked = [
        p
        for p in git("ls-files", "--others", "--exclude-standard").splitlines()
        if not p.startswith("evals/results/s4check/")
    ]
    assert_scope(git("diff", BASE, "--name-only").splitlines() + untracked, allowed)
    blobs = {
        line.split("\t")[1]: line.split()[2]
        for line in git("ls-tree", "-r", BASE).splitlines()
    }
    assert {p: blobs[p] for p in plan["authorized_existing"]} == plan[
        "authorized_existing"
    ]
    protected = {p: h for p, h in blobs.items() if p not in plan["authorized_existing"]}
    actual = subprocess.check_output(
        ["git", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        text=True,
        input="\n".join(protected) + "\n",
    ).splitlines()
    assert dict(zip(protected, actual, strict=True)) == protected


def test_exact_inherited_files_and_both_historical_live_runs():
    load = lambda p: json.loads((ROOT / p).read_bytes())
    s5, s6, s7 = [
        load("Documentation/sprint" + str(n) + "_preservation.json") for n in (5, 6, 7)
    ]
    sets = [
        (
            "evals/results/s4check",
            s5["preexisting_untracked_sha256"] | s7["protected_inherited_cache_sha256"],
            False,
            590,
        ),
        (
            "knowledge_base/workspaces/northstar-sprint5",
            s6["protected_workspace_sha256"],
            False,
            13,
        ),
    ]
    for p, count in (
        ("Documentation/cross_pillar_v1/live_readout.json", 36),
        ("Documentation/reliability_v1/readout.json", 14),
    ):
        record = load(p)
        sets.append(
            (record["ignored_run_root"], record["artifact_sha256"], True, count)
        )
    for name, hashes, relative, count in sets:
        assert len(hashes) == count
        directory = ROOT / name
        if not directory.exists():
            continue  # Fresh CI clone absence is not evidence of local integrity.
        actual = {
            p.relative_to(directory if relative else ROOT).as_posix()
            for p in directory.rglob("*")
            if p.is_file()
        }
        assert actual == set(hashes)
        for p, digest in hashes.items():
            assert (
                hashlib.sha256(
                    (directory / p if relative else ROOT / p).read_bytes()
                ).hexdigest()
                == digest
            ), p
    if (ROOT / "evals/results/s4check").exists():
        assert (
            hashlib.sha256((ROOT / "AGENTS.md").read_bytes()).hexdigest()
            == manifest()["installed_agents_sha256"]
        )
    assert not git("ls-files", "--", "evals/results/s4check").strip()


def normalized_test_file(source):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            node.decorator_list = [
                d
                for d in node.decorator_list
                if not (isinstance(d, ast.Name) and d.id == "sprint9_historical_test")
            ]
    tree.body = [
        n
        for n in tree.body
        if not (isinstance(n, ast.ImportFrom) and n.module == "sprint9_history")
    ]
    imports = sorted(
        ast.dump(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
    )
    body = [
        ast.dump(n)
        for n in tree.body
        if not isinstance(n, (ast.Import, ast.ImportFrom))
    ]
    return imports, body


def test_migrated_historical_tests_keep_all_original_assertions():
    for path in manifest()["authorized_existing"]:
        if not path.startswith("tests/"):
            continue
        original = git("show", BASE + ":" + path)
        current = (ROOT / path).read_text(encoding="utf-8")
        assert normalized_test_file(current) == normalized_test_file(original), path
        assert normalized_test_file(
            original.replace("assert ", "assert True or ", 1)
        ) != normalized_test_file(original)


@pytest.mark.parametrize(
    "target",
    [
        "tests/test_sprint8_preservation.py::test_current_paths_and_every_other_base_blob",
        "tests/test_grounding_preservation.py::test_prior_evidence_and_unmodified_source_bytes_preserved",
    ],
)
def test_scope_rejects_unlisted_file_and_archived_source_mutation(tmp_path, target):
    with pytest.raises(AssertionError, match="Unauthorized"):
        assert_scope(["app/main.py"], manifest()["authorized_existing"])
    directory, env = _snapshot(tmp_path, BASE)
    path = directory / "app/ollama_client.py"
    path.write_bytes(path.read_bytes() + b"\n# deliberate mutation\n")
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            target,
        ],
        cwd=directory,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 1
    assert "1 failed" in result.stdout and "AssertionError" in result.stdout
