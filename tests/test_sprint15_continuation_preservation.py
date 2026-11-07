"""Bound the continuation while replaying the prior live scope at its final tip.

Only the immediate scope assertion migrates. Its unchanged body still executes
on the complete historical source. This guard additionally checks every prior
tracked blob except the explicitly reviewed continuation edit paths. Frozen
plans, tests, keys, scorers, journals and reports remain live-byte protected.
"""

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest
from sprint15_continuation_history import END, _snapshot

from evals.native_evidence_workflow_v1 import preservation as prior_guard

ROOT = Path(__file__).resolve().parents[1]
BASE = "9be773070f2176d40e3e80beccf65feaefdc03c0"
SCOPE = "Documentation/sprint15_continuation/scope.json"
MIGRATED = "tests/test_sprint15_preservation.py"
AUTHORIZED_EXISTING = {
    MIGRATED,
    "app/native_evidence_api.py",
    "dashboard/native_evidence.py",
    "dashboard/native_evidence_client.py",
    "app/ollama_client.py",
    "dashboard/workflows.py",
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def baseline_blobs() -> dict[str, str]:
    """Use Git's immutable tree rather than another generated artifact inventory."""
    entries = git("ls-tree", "-r", "--full-tree", BASE).splitlines()
    result = {}
    for entry in entries:
        metadata, path = entry.split("\t", 1)
        mode, kind, blob = metadata.split()
        assert kind == "blob" and mode in {"100644", "100755"}
        result[path] = blob
    assert len(result) == 829
    return result


def load_scope(baseline: dict[str, str]) -> dict:
    scope = json.loads((ROOT / SCOPE).read_bytes())
    assert set(scope) == {"base_commit", "authorized_existing", "authorized_new"}
    assert scope["base_commit"] == BASE == END
    assert scope["authorized_existing"] == {
        path: baseline[path] for path in AUTHORIZED_EXISTING
    }, "Only explicitly reviewed continuation source paths may change"
    new = scope["authorized_new"]
    assert isinstance(new, list) and all(type(path) is str for path in new)
    assert len(new) == len(set(new))
    assert not set(new) & set(baseline), "New paths cannot exempt baseline blobs"
    assert all(
        not Path(path).is_absolute()
        and ".." not in Path(path).parts
        and not path.startswith("evals/results/s4check/")
        for path in new
    )
    return scope


def assert_scope(names: list[str], allowed: set[str]) -> None:
    unexpected = set(names) - allowed
    if unexpected:
        raise AssertionError(
            "Unauthorized Sprint 15 continuation path: " + ", ".join(sorted(unexpected))
        )


def verify_protected_blobs(baseline: dict[str, str]) -> int:
    protected = {
        path: blob for path, blob in baseline.items() if path not in AUTHORIZED_EXISTING
    }
    actual = subprocess.check_output(
        ["git", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        text=True,
        input="\n".join(protected) + "\n",
    ).splitlines()
    assert dict(zip(protected, actual, strict=True)) == protected, (
        "Original protected Git blob changed"
    )
    return len(protected)


def test_current_exact_paths_and_all_original_blobs():
    baseline = baseline_blobs()
    scope = load_scope(baseline)
    untracked = [
        path
        for path in git("ls-files", "--others", "--exclude-standard").splitlines()
        if not path.startswith("evals/results/s4check/")
    ]
    changed = git("diff", BASE, "--name-only").splitlines() + untracked
    assert_scope(changed, AUTHORIZED_EXISTING | set(scope["authorized_new"]))
    assert verify_protected_blobs(baseline) == 829 - len(AUTHORIZED_EXISTING)


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
    original = ast.parse(git("show", BASE + ":" + MIGRATED))
    original.body.append(
        ast.ImportFrom(
            module="sprint15_continuation_history",
            names=[
                ast.alias("historical_test", "sprint15_continuation_historical_test")
            ],
            level=0,
        )
    )
    for node in original.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "test_current_exact_paths_and_all_original_blobs"
        ):
            node.decorator_list.append(
                ast.Name(id="sprint15_continuation_historical_test", ctx=ast.Load())
            )
    assert canonical(
        ast.parse((ROOT / MIGRATED).read_text(encoding="utf-8"))
    ) == canonical(original)


def test_history_cache_and_wrapper_keep_original_archive_implementation():
    from sprint8_history import _snapshot as original
    from sprint15_history import _snapshot as previous

    assert _snapshot is not original and _snapshot is not previous
    assert _snapshot.__wrapped__ is original.__wrapped__ is previous.__wrapped__
    previous_module = ast.parse((ROOT / "tests/sprint15_history.py").read_bytes())
    current_module = ast.parse(
        (ROOT / "tests/sprint15_continuation_history.py").read_bytes()
    )
    previous_body = next(
        node
        for node in previous_module.body
        if isinstance(node, ast.FunctionDef) and node.name == "historical_test"
    )
    current_body = next(
        node
        for node in current_module.body
        if isinstance(node, ast.FunctionDef) and node.name == "historical_test"
    )
    assert ast.dump(previous_body) == ast.dump(current_body)


def test_original_scope_replay_rejects_real_protected_source_mutation(tmp_path):
    directory, env = _snapshot(tmp_path, BASE)
    path = directory / "app/main.py"
    path.write_bytes(path.read_bytes() + b"\n# deliberate original-scope mutation\n")
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "tests/test_sprint15_preservation.py::test_current_exact_paths_and_all_original_blobs",
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


def test_new_guard_rejects_real_frozen_native_source_mutation(tmp_path, monkeypatch):
    baseline = baseline_blobs()
    directory, env = _snapshot(tmp_path, BASE)
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.setenv(name, env[name])
    monkeypatch.setattr(sys.modules[__name__], "ROOT", directory)
    assert verify_protected_blobs(baseline) == 829 - len(AUTHORIZED_EXISTING)
    path = directory / "app/native_observations.py"
    path.write_bytes(path.read_bytes() + b"\n# deliberate frozen-native mutation\n")
    with pytest.raises(AssertionError, match="Original protected Git blob changed"):
        verify_protected_blobs(baseline)


def test_unlisted_paths_cannot_be_authorized_by_new_path_manifest(
    tmp_path, monkeypatch
):
    baseline = baseline_blobs()
    scope = load_scope(baseline)
    with pytest.raises(
        AssertionError, match="Unauthorized Sprint 15 continuation path"
    ):
        assert_scope(
            ["app/main.py"], AUTHORIZED_EXISTING | set(scope["authorized_new"])
        )
    scope["authorized_new"].append("app/main.py")
    path = tmp_path / SCOPE
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(scope), encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "ROOT", tmp_path)
    with pytest.raises(AssertionError, match="New paths cannot exempt baseline blobs"):
        load_scope(baseline)


def test_original_raw_guard_and_historical_unknown_accounting_stay_unchanged():
    # The original test still verifies all locally present 990 raw files. Reuse
    # that guard and metadata; do not copy or regenerate private artifact lists.
    baseline = prior_guard.load_baseline()
    assert sum(baseline["raw_group_counts"].values()) == 990
    assert baseline["inherited_visible_untracked"] == 405
    assert baseline["inherited_ignored_s4check"] == 185
    outcome = baseline["historical_unknown"]["outcomes"]["unknown_no_retry"]
    assert type(outcome) is int and outcome == 1
    assert (
        git(
            "hash-object",
            "--path=evals/native_evidence_workflow_v1/preservation.py",
            "evals/native_evidence_workflow_v1/preservation.py",
        )
        == baseline_blobs()["evals/native_evidence_workflow_v1/preservation.py"]
    )
