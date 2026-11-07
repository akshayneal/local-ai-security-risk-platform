"""Active exact scope, raw preservation, immutable guard replay and mutations."""

import ast
import hashlib
import json
import subprocess
import sys

import pytest
from sprint14_history import _snapshot

from evals.evidence_qualification_v1 import preservation as guard


def test_current_exact_paths_and_all_original_blobs():
    assert guard.verify_scope()["protected_blobs"] == 708


def test_all_inherited_raw_files_remain_exact_and_unknown_stays_unknown():
    result = guard.verify_raw()
    if not result["absent_groups_not_claimed_preserved"]:
        assert result["local_raw_files_checked"] == 990
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
        "willow13": 79,
    }
    assert baseline["historical_unknown"] == {
        "path": "knowledge_base/workspaces/cedar-sprint9-lab/accounting/journal.jsonl",
        "outcomes": {"RESPONSE": 5, "unknown_no_retry": 1},
        "sha256": "9038413a62a475ab5ebf9a343b705012f347739b25593cea8986d8b0519d0b56",
    }


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


def test_immediate_guard_migration_adds_only_import_and_decorator():
    original = ast.parse(guard.git("show", guard.BASE + ":" + guard.MIGRATED))
    original.body.append(
        ast.ImportFrom(
            module="sprint14_history",
            names=[ast.alias("historical_test", "sprint14_historical_test")],
            level=0,
        )
    )
    for node in original.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "test_current_exact_paths_and_all_original_blobs"
        ):
            node.decorator_list.append(
                ast.Name(id="sprint14_historical_test", ctx=ast.Load())
            )
    assert canonical(
        ast.parse((guard.ROOT / guard.MIGRATED).read_text(encoding="utf-8"))
    ) == canonical(original)


def test_history_cache_is_separate_and_archive_body_is_unchanged():
    from sprint8_history import _snapshot as original
    from sprint13_history import _snapshot as previous

    assert _snapshot is not original and _snapshot is not previous
    assert _snapshot.__wrapped__ is original.__wrapped__ is previous.__wrapped__


def test_unlisted_path_and_real_original_source_mutation_are_rejected(tmp_path):
    with pytest.raises(AssertionError, match="Unauthorized Sprint 14 path"):
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
            "tests/test_sprint13_preservation.py::test_current_exact_paths_and_all_original_blobs",
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


def test_changed_baseline_hash_is_rejected(tmp_path, monkeypatch):
    baseline = tmp_path / guard.BASELINE
    baseline.parent.mkdir(parents=True)
    baseline.write_bytes((guard.ROOT / guard.BASELINE).read_bytes() + b" ")
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="Immutable Sprint 14 baseline changed"):
        guard.load_baseline()


def test_reviewer_template_preserves_masked_ids_and_all_judgments_are_empty():
    packet_path = "Documentation/adaptive_security_reasoning_v1/review_packet.json"
    raw = (guard.ROOT / packet_path).read_bytes()
    packet = json.loads(raw)
    template = json.loads(
        (guard.ROOT / "Documentation/evidence_qualification_v1/adjudication_template.json")
        .read_bytes()
    )
    assert template["packet_path"] == packet_path
    assert template["packet_sha256"] == hashlib.sha256(raw).hexdigest()
    assert template["review_status"] == "INDEPENDENT HUMAN REVIEW PENDING"
    assert template["completed_count"] == 0
    assert len(template["items"]) == len(packet["items"]) == 60
    assert [row["review_id"] for row in template["items"]] == [
        row["review_id"] for row in packet["items"]
    ]
    assert all(value is None for value in template["reviewer"].values())
    assert all(
        value is None
        for row in template["items"]
        for key, value in row.items()
        if key != "review_id"
    )
