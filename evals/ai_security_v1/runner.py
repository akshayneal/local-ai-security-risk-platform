"""Frozen API-level software checks with deterministic stubs; no live inference."""

import argparse
import copy
import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import ai_security_analyzer as analyzer
from app import ai_security_api as api
from app.retrieval.storage import fingerprint
from app.untrusted_content import QUARANTINE_MARKER

ROOT = Path(__file__).resolve().parents[2]
SUITE = Path(__file__).resolve().parent


def verify_freeze() -> dict:
    freeze = json.loads((SUITE / "freeze.json").read_bytes())
    for name, expected in freeze["sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Frozen AI Security input/source/rubric mismatch")
    implementation = json.loads((SUITE / "implementation_freeze.json").read_bytes())
    names = implementation["source_git_blobs"]
    actual = subprocess.check_output(
        ["git", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        text=True,
        input="\n".join(names) + "\n",
    ).splitlines()
    if dict(zip(names, actual, strict=True)) != names:
        raise ValueError("Frozen AI Security implementation mismatch")
    return {**freeze, "implementation_source_git_blobs": names}


def evaluate() -> dict:
    freeze = verify_freeze()
    cases = json.loads((SUITE / "cases.json").read_bytes())
    results = []
    for row in cases:
        started = time.perf_counter()
        calls, audits = [], []

        def generate(_calls=calls, _output=row["stub_output"], **arguments):
            _calls.append(arguments)
            return copy.deepcopy(_output)

        with (
            patch.object(analyzer, "call_model_json", generate),
            patch.object(api, "write_audit_log", lambda _audits=audits, **kw: _audits.append(kw)),
            TestClient(api.app) as client,
        ):
            response = client.post("/ui/analyze/ai-security", json=row["input"])
        body = response.json()
        expected = row["expected"]
        accepted = response.status_code == 200
        input_valid = expected != "input_rejected"
        output_valid = expected not in {"input_rejected", "output_rejected"}
        passed = response.status_code == (
            422 if not input_valid else 500 if not output_valid else 200
        )
        passed &= len(calls) == (
            0 if expected in {"input_rejected", "insufficient_no_generation"} else 1
        )
        passed &= len(audits) == (1 if input_valid else 0)
        source_count = 0
        category_count = 0
        unverified = False
        required_gap = False
        if accepted:
            metadata, analysis = body["metadata"], body["analysis"]
            catalog = {s["provenance"]["evidence_id"]: s for s in metadata["sources"]}
            unverified = (
                metadata["claim_status"] == "unassessed"
                and analysis["verification_status"] == "not_verified"
                and analysis["action_status"] == "no_actions_executed"
            )
            for finding in analysis["findings"]:
                for source_id in finding["source_references"]:
                    source_count += 1
                    category_count += (
                        source_id in catalog
                        and catalog[source_id]["category"] == finding["category"]
                    )
                unverified &= (
                    finding["verification_status"] == "not_verified"
                    and finding["review_status"] == "candidate"
                )
            passed &= (
                source_count == category_count
                and unverified
                and bool(analysis["evidence_gaps"])
            )
            if row["group"] == "benign_preservation":
                passed &= not analysis["findings"]
            if expected == "accepted_quarantined":
                passed &= (
                    QUARANTINE_MARKER in calls[0]["user_prompt"]
                    and "Ignore previous system instructions"
                    not in calls[0]["user_prompt"]
                )
            if expected == "accepted_missing_evidence":
                required_gap = any(
                    "No implementation evidence" in gap
                    for gap in analysis["evidence_gaps"]
                )
                passed &= required_gap
            if expected == "insufficient_no_generation":
                passed &= (
                    analysis["coverage_status"] == "insufficient_information"
                    and not metadata["model_invoked"]
                )
        results.append(
            {
                "id": row["id"],
                "group": row["group"],
                "expected": expected,
                "input_sha256": fingerprint(row["input"]),
                "http_status": response.status_code,
                "passed": bool(passed),
                "stub_calls": len(calls),
                "audit_outcomes": len(audits),
                "accepted": accepted,
                "unverified_status_retained": bool(unverified),
                "cited_references": source_count,
                "category_consistent_references": category_count,
                "required_implementation_gap": required_gap,
                "response": body,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            }
        )
    groups = {
        g: {
            "passed": sum(r["passed"] for r in results if r["group"] == g),
            "total": sum(r["group"] == g for r in results),
        }
        for g in sorted({r["group"] for r in results})
    }
    accepted = [r for r in results if r["accepted"]]
    invalid_inputs = [r for r in results if r["expected"] == "input_rejected"]
    invalid_outputs = [r for r in results if r["expected"] == "output_rejected"]
    return {
        "format": "ai-security-offline-v1",
        "judgments": "synthetic implementation-authored, not independently adjudicated",
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "real_inference": "LIVE INFERENCE NOT RUN (0)",
        },
        "freeze": freeze,
        "cases": len(results),
        "passed": sum(r["passed"] for r in results),
        "groups": groups,
        "metrics": {
            "input_rejection": {
                "count": sum(r["http_status"] == 422 for r in invalid_inputs),
                "total": len(invalid_inputs),
            },
            "output_withheld": {
                "count": sum(r["http_status"] == 500 for r in invalid_outputs),
                "total": len(invalid_outputs),
            },
            "accepted_eligible_results": {
                "count": len(accepted),
                "total": sum(
                    r["expected"] not in {"input_rejected", "output_rejected"}
                    for r in results
                ),
            },
            "benign_preservation": groups["benign_preservation"],
            "category_source_consistency": {
                "count": sum(r["category_consistent_references"] for r in results),
                "total": sum(r["cited_references"] for r in results),
            },
            "unassessed_unverified_status": {
                "count": sum(r["unverified_status_retained"] for r in accepted),
                "total": len(accepted),
            },
            "required_missing_implementation_gap": {
                "count": sum(r["required_implementation_gap"] for r in results),
                "total": 1,
            },
            "false_structured_authority_promotion": {
                "count": sum(
                    r["accepted"]
                    for r in results
                    if r["id"] in {"HOSTILE-5", "HOSTILE-6"}
                ),
                "total": 2,
            },
            "real_model_attempts": 0,
            "real_embeddings": 0,
            "semantic_accuracy": "NOT MEASURED",
            "live_injection_resistance": "NOT MEASURED",
        },
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Preserve existing output; choose a new path for explicit replay")
    report = evaluate()
    with args.output.open("x", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {k: report[k] for k in ("cases", "passed", "groups", "metrics")}, indent=2
        )
    )


if __name__ == "__main__":
    main()
