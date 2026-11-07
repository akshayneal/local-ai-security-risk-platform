"""Exact Sprint 14B scope and hash-only inherited source/artifact preservation."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "130c95454378394ca197d8851a7bae99adf8439a"
BASELINE = "Documentation/qualified_soc_contract_v2/preservation_baseline.json"
SCOPE = "Documentation/qualified_soc_contract_v2/scope.json"
MIGRATED = "tests/test_sprint14_preservation.py"
BASELINE_SHA256 = "dfe1185a5f1fdebfa9d675f2270aa2115742eb066950d07ac14c5a6658bf3326"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def digest(path: Path) -> str:
    """Hash only; private historical content is never parsed or imported."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_baseline() -> dict:
    path = ROOT / BASELINE
    if digest(path) != BASELINE_SHA256:
        raise ValueError("Immutable Sprint 14B baseline changed")
    value = json.loads(path.read_bytes())
    if value["base_commit"] != BASE:
        raise ValueError("Wrong Sprint 14B starting commit")
    return value


def assert_scope(names: list[str], allowed: set[str]) -> None:
    unexpected = set(names) - allowed
    if unexpected:
        raise AssertionError(
            "Unauthorized Sprint 14B path: " + ", ".join(sorted(unexpected))
        )


def verify_protected_blobs(baseline: dict) -> int:
    """Protect v1 source and data as well as every older baseline blob."""
    protected = {
        path: value for path, value in baseline["git_blobs"].items() if path != MIGRATED
    }
    actual = subprocess.check_output(
        ["git", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        text=True,
        input="\n".join(protected) + "\n",
    ).splitlines()
    if dict(zip(protected, actual, strict=True)) != protected:
        raise AssertionError("Original protected Git blob changed")
    return len(protected)


def verify_scope() -> dict:
    baseline = load_baseline()
    scope = json.loads((ROOT / SCOPE).read_bytes())
    if scope["base_commit"] != BASE or scope["authorized_existing"] != {
        MIGRATED: baseline["git_blobs"][MIGRATED]
    }:
        raise AssertionError("Only the immediately preceding scope guard may migrate")
    new_paths = scope["authorized_new"]
    if len(new_paths) != len(set(new_paths)) or set(new_paths) & set(
        baseline["git_blobs"]
    ):
        raise AssertionError("New paths must be unique and absent from the baseline")
    untracked = [
        path
        for path in git("ls-files", "--others", "--exclude-standard").splitlines()
        if not path.startswith("evals/results/s4check/")
    ]
    changed = git("diff", BASE, "--name-only").splitlines() + untracked
    assert_scope(changed, set(scope["authorized_existing"]) | set(new_paths))
    return {
        "base_commit": BASE,
        "changed_paths": sorted(set(changed)),
        "protected_blobs": verify_protected_blobs(baseline),
    }


def verify_raw() -> dict:
    """Preserve exact inherited sets; absent hosted roots are not preservation."""
    baseline = load_baseline()
    checked = 0
    omitted = []
    for group, record in baseline["raw_groups"].items():
        roots = [ROOT / path for path in record["roots"]]
        if not any(path.exists() for path in roots):
            omitted.append(group)
            continue
        actual = {
            path.relative_to(ROOT).as_posix()
            for directory in roots
            for path in directory.rglob("*")
            if path.is_file()
        }
        if actual != set(record["sha256"]):
            raise AssertionError("Inherited artifact set changed: " + group)
        for path, expected in record["sha256"].items():
            if digest(ROOT / path) != expected:
                raise AssertionError("Inherited artifact bytes changed: " + path)
            checked += 1
    if (ROOT / "evals/results/s4check").exists() and digest(
        ROOT / "AGENTS.md"
    ) != baseline["installed_agents_sha256"]:
        raise AssertionError("Installed AGENTS bytes changed")
    if git("ls-files", "--", "evals/results/s4check"):
        raise AssertionError("Private inherited source entered Git")
    return {
        "local_raw_files_checked": checked,
        "absent_groups_not_claimed_preserved": omitted,
    }


if __name__ == "__main__":
    print(json.dumps({"scope": verify_scope(), "raw": verify_raw()}, indent=2))
