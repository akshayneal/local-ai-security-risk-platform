"""Exact current scope, inherited byte protection and unchanged historical guard."""

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from sprint8_history import _snapshot

ROOT = Path(__file__).resolve().parents[1]
BASE = "b6d84530b6eb9dccbb328a8dcffb0f9b532ef7ab"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def load(path):
    return json.loads((ROOT / path).read_bytes())


def assert_scope(names, allowed):
    assert not set(names) - set(allowed), "Unauthorized Sprint 10 path"


def test_current_exact_paths_and_all_other_base_blobs():
    manifest = load("Documentation/sprint10_preservation.json")
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
    assert not [
        p for p in git("diff", BASE, "--name-only").splitlines() if p.startswith("app/")
    ]


def test_all_inherited_raw_files_and_frozen_aster_bytes():
    s5, s6, s7 = [load(f"Documentation/sprint{n}_preservation.json") for n in (5, 6, 7)]
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
    for name, default, count in (
        ("Documentation/cross_pillar_v1/live_readout.json", None, 36),
        ("Documentation/reliability_v1/readout.json", None, 14),
        (
            "Documentation/controlled_inference_v1/lab_readout.json",
            "knowledge_base/workspaces/cedar-sprint9-lab",
            18,
        ),
    ):
        record = load(name)
        sets.append(
            (
                record.get("ignored_run_root", default),
                record["artifact_sha256"],
                True,
                count,
            )
        )
    for name, hashes, relative, count in sets:
        assert len(hashes) == count
        directory = ROOT / name
        if not directory.exists():
            continue  # Fresh hosted clone absence is not a local preservation claim.
        assert {
            p.relative_to(directory if relative else ROOT).as_posix()
            for p in directory.rglob("*")
            if p.is_file()
        } == set(hashes)
        for path, digest in hashes.items():
            assert (
                hashlib.sha256(
                    (directory / path if relative else ROOT / path).read_bytes()
                ).hexdigest()
                == digest
            ), path
    manifest = load("Documentation/sprint10_preservation.json")
    for path, digest in manifest["aster_literal_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
        assert (
            hashlib.sha256(
                subprocess.check_output(["git", "show", "HEAD:" + path], cwd=ROOT)
            ).hexdigest()
            == digest
        )
    if (ROOT / "evals/results/s4check").exists():
        assert (
            hashlib.sha256((ROOT / "AGENTS.md").read_bytes()).hexdigest()
            == manifest["installed_agents_sha256"]
        )
    assert not git("ls-files", "--", "evals/results/s4check").strip()


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
    path = "tests/test_sprint9_preservation.py"
    original = ast.parse(git("show", BASE + ":" + path))
    original.body.append(
        ast.ImportFrom(
            module="sprint10_history",
            names=[ast.alias("historical_test", "sprint10_historical_test")],
            level=0,
        )
    )
    for node in original.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "test_current_scope_and_every_other_baseline_blob"
        ):
            node.decorator_list.append(
                ast.Name(id="sprint10_historical_test", ctx=ast.Load())
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
            load("Documentation/sprint10_preservation.json")["authorized_existing"],
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
            "tests/test_sprint9_preservation.py::test_current_scope_and_every_other_baseline_blob",
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
