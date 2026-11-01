"""Exact current scope, inherited byte protection and unchanged historical guard."""

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from sprint11_history import _snapshot

ROOT = Path(__file__).resolve().parents[1]
BASE = "564499f0537688b6422f48c51fc5995467f000c6"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def load(path):
    return json.loads((ROOT / path).read_bytes())


def assert_scope(names, allowed):
    assert not set(names) - set(allowed), "Unauthorized Sprint 11 path"


def test_current_exact_paths_and_all_other_base_blobs():
    manifest = load("Documentation/sprint11_preservation.json")
    assert manifest["base_commit"] == BASE
    allowed = set(manifest["authorized_existing"]) | set(manifest["authorized_new"])
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
    assert {p: blobs[p] for p in manifest["authorized_existing"]} == manifest[
        "authorized_existing"
    ]
    protected = {
        p: h for p, h in blobs.items() if p not in manifest["authorized_existing"]
    }
    actual = subprocess.check_output(
        ["git", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        text=True,
        input="\n".join(protected) + "\n",
    ).splitlines()
    assert dict(zip(protected, actual, strict=True)) == protected


def test_all_elm_bytes_and_installed_agents():
    manifest = load("Documentation/sprint11_preservation.json")
    hashes = manifest["elm_sha256"]
    assert len(hashes) == 71
    if (ROOT / "knowledge_base/workspaces/elm-sprint10-lab").exists():
        actual = {
            p.relative_to(ROOT).as_posix()
            for d in ["elm-sprint10-lab", "elm-sprint10-campaign"]
            for p in (ROOT / "knowledge_base/workspaces" / d).rglob("*")
            if p.is_file()
        }
        assert actual == set(hashes)
        for path, digest in hashes.items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
        assert (
            hashlib.sha256((ROOT / "AGENTS.md").read_bytes()).hexdigest()
            == manifest["installed_agents_sha256"]
        )


def test_new_replay_cache_preserves_original_archive_body_without_eviction():
    from sprint8_history import _snapshot as original

    assert _snapshot is not original
    assert _snapshot.__wrapped__ is original.__wrapped__


def canonical(tree):
    imports = sorted(
        ast.dump(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
    )
    body = [
        ast.dump(n)
        for n in tree.body
        if not isinstance(n, (ast.Import, ast.ImportFrom))
    ]
    return imports, body


def test_historical_migration_is_exactly_one_import_and_one_decorator():
    path = "tests/test_sprint10_preservation.py"
    original = ast.parse(git("show", BASE + ":" + path))
    original.body.append(
        ast.ImportFrom(
            module="sprint11_history",
            names=[ast.alias("historical_test", "sprint11_historical_test")],
            level=0,
        )
    )
    for node in original.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "test_current_exact_paths_and_all_other_base_blobs"
        ):
            node.decorator_list.append(
                ast.Name(id="sprint11_historical_test", ctx=ast.Load())
            )
    assert canonical(ast.parse((ROOT / path).read_text(encoding="utf-8"))) == canonical(
        original
    )
    source = git("show", BASE + ":" + path)
    assert canonical(
        ast.parse(source.replace("assert ", "assert True or ", 1))
    ) != canonical(ast.parse(source))


def test_unlisted_path_and_original_historical_mutation_are_rejected(tmp_path):
    with pytest.raises(AssertionError, match="Unauthorized"):
        assert_scope(
            ["app/main.py"],
            load("Documentation/sprint11_preservation.json")["authorized_existing"],
        )
    directory, env = _snapshot(tmp_path, BASE)
    path = directory / "app/main.py"
    path.write_bytes(path.read_bytes() + b"\n# deliberate source mutation\n")
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "tests/test_sprint10_preservation.py::test_current_exact_paths_and_all_other_base_blobs",
        ],
        cwd=directory,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert (
        result.returncode == 1
        and "1 failed" in result.stdout
        and "AssertionError" in result.stdout
    )
