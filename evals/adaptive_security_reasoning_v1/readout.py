"""Package saved Sprint 13 evidence without provider calls or diagnostic replay.

All decisions are read from hash-verified saved application artifacts. Hashes
identify bytes, not source authenticity or semantic truth. Outputs are exclusive.
"""

import hashlib
import json
import subprocess
from pathlib import Path

from evals.adaptive_security_reasoning_v1.review import reviewer_packet, write_packet
from evals.adaptive_security_reasoning_v1.transport import plain_path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "Documentation/adaptive_security_reasoning_v1"
RAW_ROOTS = (
    "knowledge_base/workspaces/willow-sprint13-development",
    "knowledge_base/workspaces/willow-sprint13-campaign",
)
DATA_FILES = (
    tuple(
        "Documentation/adaptive_security_reasoning_v1/" + name
        for name in (
            "author_review_D0.json",
            "author_review_D1.json",
            "author_review_D3.json",
            "development_readout_D0.json",
            "development_readout.json",
            "recovery_accounting.json",
            "demo_shortcut_recovery.json",
            "selection.json",
            "diagnostic_run.json",
            "diagnostic_outputs.json",
            "diagnostic_scores.json",
            "review_packet.json",
            "reviewer_key.json",
            "preservation_baseline.json",
        )
    )
    + tuple(
        "evals/adaptive_security_reasoning_v1/" + name
        for name in (
            "dev_cases.json",
            "dev_key.json",
            "freeze.json",
            "protocol.json",
            "rubric.md",
            "batches/D0.json",
            "batches/D1.json",
            "batches/D3.json",
        )
    )
    + tuple(
        "evals/adaptive_security_holdout_v1/" + name
        for name in ("cases.json", "author_key.json", "freeze.json")
    )
)


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    plain_path(path)
    if path.stat().st_size > 32_000_000:
        raise ValueError("artifact_byte_budget")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, value):
    # Same exclusive fsynced artifact writer as the locked offline runner.
    from evals.adaptive_security_holdout_v1.runner import write_new as store

    store(path, value)


def source_files():
    tracked = subprocess.check_output(
        ["git", "ls-files", "*.py"], cwd=ROOT, text=True
    ).splitlines()
    return sorted(
        set(tracked)
        | {
            "evals/adaptive_security_reasoning_v1/readout.py",
            "tests/test_adaptive_completion.py",
        }
    )


def git_blobs(paths):
    values = subprocess.check_output(
        ["git", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        text=True,
        input="\n".join(paths) + "\n",
    ).splitlines()
    return dict(zip(paths, values, strict=True))


def verify_hashes(root, hashes):
    for relative, expected in hashes.items():
        path = Path(relative)
        if path.is_absolute() or path.drive or ".." in path.parts or "\\" in relative:
            raise ValueError("unsafe_artifact_path")
        if sha(root / path) != expected:
            raise ValueError("artifact_hash_mismatch: " + relative)


def verify_inventory():
    manifest = read(DOCS / "artifact_manifest.json")
    if set(manifest["saved_data_sha256"]) != set(DATA_FILES):
        raise ValueError("saved_artifact_inventory_changed")
    verify_hashes(ROOT, manifest["saved_data_sha256"])
    if manifest["source_git_blobs"] != git_blobs(source_files()):
        raise ValueError("final_source_blob_changed")
    absent, checked = [], 0
    for relative in RAW_ROOTS:
        path = ROOT / relative
        expected = {
            p: v
            for p, v in manifest["local_raw_sha256"].items()
            if p.startswith(relative + "/")
        }
        if not path.exists():
            absent.append(relative)  # Clean CI cannot demonstrate local preservation.
            continue
        actual = {
            p.relative_to(ROOT).as_posix() for p in path.rglob("*") if p.is_file()
        }
        if actual != set(expected):
            raise ValueError("local_raw_inventory_changed")
        verify_hashes(ROOT, expected)
        checked += len(expected)
    if set(manifest["local_raw_sha256"]) - {
        p
        for p in manifest["local_raw_sha256"]
        if any(p.startswith(root + "/") for root in RAW_ROOTS)
    }:
        raise ValueError("unapproved_raw_namespace")
    return {
        "saved_data_files_checked": len(DATA_FILES),
        "local_raw_files_checked": checked,
        "absent_local_roots_not_claimed_preserved": absent,
        "source_files_checked": len(source_files()),
    }


def package_saved():
    dev = read(DOCS / "development_readout.json")
    outputs_path = DOCS / "diagnostic_outputs.json"
    outputs, scores = read(outputs_path), read(DOCS / "diagnostic_scores.json")
    if sha(outputs_path) != scores["outcomes_sha256"]:
        raise ValueError("diagnostic_output_score_binding")
    cases = read(ROOT / "evals/adaptive_security_reasoning_v1/dev_cases.json")
    keys = read(ROOT / "evals/adaptive_security_reasoning_v1/dev_key.json")
    records, assessments = list(dev["records"]), {}
    for record in records:
        if record["structural_status"] == "valid":
            value = record["report"]["assessment"]
            previous = assessments.setdefault(record["case_id"], value)
            if json.dumps(previous, sort_keys=True) != json.dumps(
                value, sort_keys=True
            ):
                raise ValueError("development_canonical_versions_differ")
    # Reuse existing canonical comparisons; no new development/diagnostic scoring.
    for case_id, assessment in list(assessments.items()):
        records.append(
            {
                "case_id": case_id,
                "arm": "D",
                "phase": "development_saved_projection",
                "assessment": assessment,
                "source_commit": outputs["selection"]["development_source_commits"][-1],
            }
        )
    cases += read(ROOT / "evals/adaptive_security_holdout_v1/cases.json")
    keys += read(ROOT / "evals/adaptive_security_holdout_v1/author_key.json")
    for record in outputs["outputs"]:
        assessment = record["report"]["assessment"]
        assessments[record["case_id"]] = assessment
        records.append(
            {
                "case_id": record["case_id"],
                "arm": "D",
                "phase": "diagnostic",
                "assessment": assessment,
                "source_commit": outputs["source_commit"],
            }
        )
    packet, key = reviewer_packet(
        records, cases, authored_key=keys, canonical_assessments=assessments
    )
    write_packet(DOCS / "review_packet.json", DOCS / "reviewer_key.json", packet, key)
    raw_files = [
        p for relative in RAW_ROOTS for p in (ROOT / relative).rglob("*") if p.is_file()
    ]
    manifest = {
        "format": "sprint13-final-evidence-inventory-v1",
        "saved_data_sha256": {p: sha(ROOT / p) for p in DATA_FILES},
        "source_git_blobs": git_blobs(source_files()),
        "local_raw_sha256": {
            p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(raw_files)
        },
        "local_raw_bytes": sum(p.stat().st_size for p in raw_files),
        "claim_limit": "Byte/source correlation only, not authentication or semantic truth. Narrative, append-only decision log, checkpoint, validation and this manifest are excluded from self-referential hashes; Git retains their final versions.",
    }
    write_new(DOCS / "artifact_manifest.json", manifest)
    result = {
        "format": "sprint13-final-readout-v1",
        "date": "2026-11-06",
        "starting_sprint12_sha": "95fdfbe1d5f5cacf0d814e7c3a67bb56ce18f57a",
        "resumed_head": "e11645b052aea01fb07c7571cf815e176f22cddc",
        "selection_and_diagnostic_commit": outputs["source_commit"],
        "selected_arm": "D",
        "model_generation_closed": True,
        "raw_accounting": dev["raw_accounting"],
        "remaining_send_ceilings_unspent": {
            "development": 60,
            "diagnostic": 24,
            "global": 84,
        },
        "D3": "NOT RUN; original persisted campaign elapsed cap expired; no reset",
        "model_label_matches_per_attempt": {"M": "4/12", "H": "10/12"},
        "semantic_author_reviews": {
            phase: read(DOCS / ("author_review_" + phase + ".json"))["summary"]
            for phase in ("D0", "D1")
        },
        "development_integrity": dev["integrity"],
        "cost": dev["cost"],
        "campaign_elapsed_at_last_completed_batch_seconds": 3115.289890050888,
        "diagnostic": scores,
        "diagnostic_model_sends": 0,
        "diagnostic_case_timer_seconds_sum": sum(
            r["wall_seconds"] for r in outputs["outputs"]
        ),
        "diagnostic_premise_bindings": sum(
            r["premise_bindings"] for r in outputs["outputs"]
        ),
        "masked_review_outputs": len(records),
        "distinct_case_count": len(cases),
        "independent_review": "PENDING; zero completed",
        "visual_qa": "USER VISUAL QA PENDING",
        "release": "NO-GO",
        "artifact_manifest_sha256": sha(DOCS / "artifact_manifest.json"),
        "validation_artifact": "Documentation/adaptive_security_reasoning_v1/validation.json",
        "final_commit_and_exact_SHA_CI": "Reported after final additive commit/push in the final handoff; no self-referential commit claim.",
    }
    write_new(DOCS / "readout.json", result)
    return verify_inventory()


if __name__ == "__main__":
    print(json.dumps(package_saved(), indent=2))
