"""Exact Sprint 12 scope and immutable Sprint 11 source/artifact protection."""

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from sprint12_history import _snapshot

ROOT = Path(__file__).resolve().parents[1]
BASE = "430f20b93836584acc7719a9ed7c946781cdb3d1"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def load(path):
    return json.loads((ROOT / path).read_bytes())


def assert_scope(names, allowed):
    assert not set(names) - set(allowed), "Unauthorized Sprint 12 path"


def test_current_exact_paths_and_all_other_base_blobs():
    manifest = load("Documentation/sprint12_preservation.json")
    assert manifest["base_commit"] == BASE
    assert set(manifest["authorized_existing"]) == {
        "tests/test_sprint11_preservation.py"
    }
    allowed = set(manifest["authorized_existing"]) | set(manifest["authorized_new"])
    untracked = [
        path
        for path in git("ls-files", "--others", "--exclude-standard").splitlines()
        if not path.startswith("evals/results/s4check/")
    ]
    assert_scope(git("diff", BASE, "--name-only").splitlines() + untracked, allowed)
    blobs = {
        line.split("\t")[1]: line.split()[2]
        for line in git("ls-tree", "-r", BASE).splitlines()
    }
    assert not set(manifest["authorized_new"]) & set(blobs)
    assert {path: blobs[path] for path in manifest["authorized_existing"]} == manifest[
        "authorized_existing"
    ]
    protected = {
        path: digest
        for path, digest in blobs.items()
        if path not in manifest["authorized_existing"]
    }
    actual = subprocess.check_output(
        ["git", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        text=True,
        input="\n".join(protected) + "\n",
    ).splitlines()
    assert dict(zip(protected, actual, strict=True)) == protected


def test_inherited_raw_artifacts_and_installed_agents_remain_exact():
    from test_sprint10_preservation import (
        test_all_inherited_raw_files_and_frozen_aster_bytes,
    )
    from test_sprint11_preservation import test_all_elm_bytes_and_installed_agents

    # Reuse unchanged check bodies: 671 inherited raw files, seven Aster literals,
    # 71 Elm files and installed AGENTS. No archived source is executed here.
    test_all_inherited_raw_files_and_frozen_aster_bytes()
    test_all_elm_bytes_and_installed_agents()
    manifest = load("Documentation/sprint12_preservation.json")
    assert (
        git("hash-object", "--path=AGENTS.md", "AGENTS.md").strip()
        == git("rev-parse", BASE + ":AGENTS.md").strip()
    )
    if (ROOT / "knowledge_base/workspaces/elm-sprint10-lab").exists():
        assert (
            hashlib.sha256((ROOT / "AGENTS.md").read_bytes()).hexdigest()
            == manifest["installed_agents_sha256"]
        )


def test_sprint11_raw_artifacts_and_frozen_literals_remain_exact():
    record = load("Documentation/deterministic_evidence_v1/lab_readout.json")
    hashes = record["artifact_sha256"]
    assert len(hashes) == 72
    directories = [
        ROOT / "knowledge_base/workspaces/larch-sprint11-lab",
        ROOT / "knowledge_base/workspaces/larch-sprint11-campaign",
    ]
    if any(directory.exists() for directory in directories):
        actual = {
            path.relative_to(ROOT).as_posix()
            for directory in directories
            for path in directory.rglob("*")
            if path.is_file()
        }
        assert actual == set(hashes)
        assert sum((ROOT / path).stat().st_size for path in hashes) == 497_600
        for path, digest in hashes.items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    # Hosted clean clones omit ignored artifacts; this is not a local-file claim.
    freeze = load("evals/deterministic_evidence_v1/freeze.json")["sha256"]
    assert len(freeze) == 6
    for path, digest in freeze.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


def test_sprint12_prospective_freeze_identity_and_executable_sources():
    from evals.evidence_reasoning_v1.runner import verify_freeze

    # This checks original-added Git identity as well as both working-tree and
    # committed bytes. Reading frozen hashes does not execute an evaluation.
    freeze = verify_freeze()
    history = git(
        "log",
        "--diff-filter=A",
        "--format=%H",
        "--",
        "evals/evidence_reasoning_v1/freeze.json",
    ).splitlines()
    assert history[-1] == "ca9ddad86b679e35326d2ac0aafa77b9f90607ee"
    assert len(freeze["sha256"]) == 20
    assert freeze["protected_git_blobs"] == {
        "app/schemas.py": "44402b810c6ec967393d8883cde55927d381cb9d"
    }


def test_sprint12_final_raw_artifact_inventory_and_bytes():
    hashes = load("Documentation/evidence_reasoning_v1/readout.json")[
        "artifact_sha256"
    ]
    assert hashes
    directories = [
        ROOT / "knowledge_base/workspaces" / name
        for name in (
            "spruce-sprint12-development",
            "spruce-sprint12-diagnostic",
            "spruce-sprint12-campaign",
        )
    ]
    if any(directory.exists() for directory in directories):
        actual = {
            path.relative_to(ROOT).as_posix()
            for directory in directories
            for path in directory.rglob("*")
            if path.is_file()
        }
        # The final manifest determines the count. Missing or extra artifacts
        # fail, including an incompletely preserved development/holdout track.
        assert actual == set(hashes)
        for path, digest in hashes.items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    # A clean hosted checkout may omit all ignored roots; this establishes no
    # local preservation claim for that checkout.


def test_new_replay_cache_preserves_original_archive_body_without_eviction():
    from sprint8_history import _snapshot as original
    from sprint11_history import _snapshot as previous

    assert _snapshot is not original and _snapshot is not previous
    assert _snapshot.__wrapped__ is original.__wrapped__ is previous.__wrapped__


def canonical(tree):
    imports = sorted(
        ast.dump(node)
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )
    body = [
        ast.dump(node)
        for node in tree.body
        if not isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    return imports, body


def test_historical_migration_is_exactly_one_import_and_one_decorator():
    path = "tests/test_sprint11_preservation.py"
    original = ast.parse(git("show", BASE + ":" + path))
    original.body.append(
        ast.ImportFrom(
            module="sprint12_history",
            names=[ast.alias("historical_test", "sprint12_historical_test")],
            level=0,
        )
    )
    for node in original.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "test_current_exact_paths_and_all_other_base_blobs"
        ):
            node.decorator_list.append(
                ast.Name(id="sprint12_historical_test", ctx=ast.Load())
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
            load("Documentation/sprint12_preservation.json")["authorized_existing"],
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
            "tests/test_sprint11_preservation.py::test_current_exact_paths_and_all_other_base_blobs",
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
