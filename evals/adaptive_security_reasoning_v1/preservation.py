"""Read-only Sprint 13 scope and original-byte checks; never import old artifacts."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "95fdfbe1d5f5cacf0d814e7c3a67bb56ce18f57a"
BASELINE = "Documentation/adaptive_security_reasoning_v1/preservation_baseline.json"
SCOPE = "Documentation/adaptive_security_reasoning_v1/scope.json"
MIGRATED = "tests/test_sprint12_preservation.py"
BASELINE_SHA256 = "408946e0105165932f4efa2d57108d797419d2d9be3843e346728576ebe742d8"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_baseline() -> dict:
    path = ROOT / BASELINE
    if digest(path) != BASELINE_SHA256:
        raise ValueError("Immutable Sprint 13 baseline changed")
    value = json.loads(path.read_bytes())
    if value["base_commit"] != BASE:
        raise ValueError("Wrong Sprint 13 starting commit")
    return value


def assert_scope(names: list[str], allowed: set[str]) -> None:
    if set(names) - allowed:
        raise AssertionError(
            "Unauthorized Sprint 13 path: " + ", ".join(sorted(set(names) - allowed))
        )


def verify_scope() -> dict:
    """Every current change needs an exact listed path; old blobs stay exact."""
    baseline = load_baseline()
    scope = json.loads((ROOT / SCOPE).read_bytes())
    if scope["authorized_existing"] != {MIGRATED: baseline["git_blobs"][MIGRATED]}:
        raise AssertionError("Only the immediately preceding guard may migrate")
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
    return {
        "base_commit": BASE,
        "changed_paths": sorted(set(changed)),
        "protected_blobs": len(protected),
    }


def verify_raw() -> dict:
    """Hash only: private inherited source is never parsed, imported or executed."""
    baseline = load_baseline()
    checked = 0
    omitted = []
    for group, record in baseline["raw_groups"].items():
        roots = [ROOT / path for path in record["roots"]]
        if not any(path.exists() for path in roots):
            omitted.append(group)  # A hosted clone does not prove local preservation.
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
