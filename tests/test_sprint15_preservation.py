"""Preserve frozen v1/v2 studies and narrowly bound product integration edits."""

import ast
import subprocess
import sys

import pytest
from sprint15_history import _snapshot

from evals.native_evidence_workflow_v1 import preservation as guard


def test_current_exact_paths_and_all_original_blobs():
    assert guard.verify_scope()["protected_blobs"] == 795


def test_all_raw_bytes_and_historical_unknown_remain_exact():
    result = guard.verify_raw()
    if not result["absent_groups_not_claimed_preserved"]:
        assert result["local_raw_files_checked"] == 990
    baseline = guard.load_baseline()
    assert sum(baseline["raw_group_counts"].values()) == 990
    assert baseline["inherited_visible_untracked"] == 405
    assert baseline["inherited_ignored_s4check"] == 185
    assert baseline["historical_unknown"]["outcomes"]["unknown_no_retry"] == 1
    assert len(baseline["git_blobs"]) == 797


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


def test_immediate_guard_migration_adds_only_one_import_and_decorator():
    original = ast.parse(guard.git("show", guard.BASE + ":" + guard.MIGRATED))
    original.body.append(
        ast.ImportFrom(
            module="sprint15_history",
            names=[ast.alias("historical_test", "sprint15_historical_test")],
            level=0,
        )
    )
    for node in original.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "test_current_exact_paths_and_all_original_blobs"
        ):
            node.decorator_list.append(
                ast.Name(id="sprint15_historical_test", ctx=ast.Load())
            )
    assert canonical(
        ast.parse((guard.ROOT / guard.MIGRATED).read_text(encoding="utf-8"))
    ) == canonical(original)


def test_history_cache_is_isolated_with_original_archive_implementation():
    from sprint8_history import _snapshot as original
    from sprint14b_history import _snapshot as previous

    assert _snapshot is not original and _snapshot is not previous
    assert _snapshot.__wrapped__ is original.__wrapped__ is previous.__wrapped__


def test_original_scope_replay_rejects_real_protected_source_mutation(tmp_path):
    with pytest.raises(AssertionError, match="Unauthorized Sprint 15 path"):
        guard.assert_scope(["app/main.py"], {guard.MIGRATED, guard.STREAMLIT_ENTRYPOINT})
    directory, env = _snapshot(tmp_path, guard.BASE)
    path = directory / "app/main.py"
    path.write_bytes(path.read_bytes() + b"\n# deliberate old-scope source mutation\n")
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "tests/test_sprint14b_preservation.py::test_current_exact_paths_and_all_original_blobs",
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


def test_new_guard_rejects_real_frozen_v2_source_mutation(tmp_path, monkeypatch):
    baseline = guard.load_baseline()
    directory, env = _snapshot(tmp_path, guard.BASE)
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.setenv(name, env[name])
    monkeypatch.setattr(guard, "ROOT", directory)
    assert guard.verify_protected_blobs(baseline) == 795
    path = directory / "app/qualified_soc_v2.py"
    path.write_bytes(path.read_bytes() + b"\n# deliberate frozen v2 mutation\n")
    with pytest.raises(AssertionError, match="Original protected Git blob changed"):
        guard.verify_protected_blobs(baseline)


def test_baseline_byte_mutation_is_rejected(tmp_path, monkeypatch):
    baseline = tmp_path / guard.BASELINE
    baseline.parent.mkdir(parents=True)
    baseline.write_bytes((guard.ROOT / guard.BASELINE).read_bytes() + b" ")
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="Immutable Sprint 15 baseline changed"):
        guard.load_baseline()
