"""Active exact scope, immutable baseline, original guard and mutation proofs."""

import ast
import subprocess
import sys

import pytest
from sprint13_history import _snapshot

from evals.adaptive_security_reasoning_v1 import preservation as guard


def test_current_exact_paths_and_all_original_blobs():
    guard.verify_scope()


def test_inherited_raw_bytes_and_unknowns_stay_preserved():
    result = guard.verify_raw()
    if not result["absent_groups_not_claimed_preserved"]:
        assert result["local_raw_files_checked"] == 911
    baseline = guard.load_baseline()
    assert baseline["raw_group_counts"] == {
        "s4check": 590,
        "northstar": 13,
        "cedar7": 36,
        "maple8": 14,
        "birch9": 18,
        "elm10": 71,
        "larch11": 72,
        "spruce12": 97,
    }
    previous = baseline["journal_summary"][
        "knowledge_base/workspaces/cedar-sprint9-lab/accounting/journal.jsonl"
    ]
    assert previous["outcomes"]["unknown_no_retry"] == 1
    assert baseline["inherited_visible_untracked"] == 405
    assert baseline["inherited_ignored_s4check"] == 185


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


def test_historical_migration_adds_only_one_import_and_decorator():
    original = ast.parse(guard.git("show", guard.BASE + ":" + guard.MIGRATED))
    original.body.append(
        ast.ImportFrom(
            module="sprint13_history",
            names=[ast.alias("historical_test", "sprint13_historical_test")],
            level=0,
        )
    )
    for node in original.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "test_current_exact_paths_and_all_other_base_blobs"
        ):
            node.decorator_list.append(
                ast.Name(id="sprint13_historical_test", ctx=ast.Load())
            )
    assert canonical(
        ast.parse((guard.ROOT / guard.MIGRATED).read_text(encoding="utf-8"))
    ) == canonical(original)


def test_isolated_cache_preserves_original_archive_body():
    from sprint8_history import _snapshot as original
    from sprint12_history import _snapshot as previous

    assert _snapshot is not original and _snapshot is not previous
    assert _snapshot.__wrapped__ is original.__wrapped__ is previous.__wrapped__


def test_unlisted_path_and_mutated_original_source_are_rejected(tmp_path):
    with pytest.raises(AssertionError, match="Unauthorized Sprint 13 path"):
        guard.assert_scope(["app/main.py"], {guard.MIGRATED})
    directory, env = _snapshot(tmp_path, guard.BASE)
    path = directory / "app/main.py"
    path.write_bytes(path.read_bytes() + b"\n# deliberate negative mutation\n")
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "tests/test_sprint12_preservation.py::test_current_exact_paths_and_all_other_base_blobs",
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


def test_baseline_hash_change_is_rejected(tmp_path, monkeypatch):
    baseline = tmp_path / guard.BASELINE
    baseline.parent.mkdir(parents=True)
    baseline.write_bytes((guard.ROOT / guard.BASELINE).read_bytes() + b" ")
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="Immutable Sprint 13 baseline changed"):
        guard.load_baseline()
