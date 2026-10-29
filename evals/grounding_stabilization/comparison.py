"""Offline paired accounting; no semantic scorer or model calls."""

import statistics
from collections import Counter

from evals.grounding_stabilization.runner import cases, digest, identity, request_for

DIMENSIONS = (
    "incorrect_incident_classification",
    "unsupported_factual_claim",
    "unsupported_authority_claim",
    "benign_control_false_positive",
    "positive_control_information_lost",
    "source_applicability",
)


def measurements(report: dict) -> dict:
    rows = report["records"]
    returned = [r for r in rows if r["result"] is not None]
    repaired = [r for r in rows if r["diagnostics"]["repair_attempted"]]
    attempts = [a for r in rows for a in r["model_attempts"]]
    return {
        "case_trials": len(rows),
        "returned": len(returned),
        "withheld": len(rows) - len(returned),
        "first_pass_returned": sum(
            not r["diagnostics"]["repair_attempted"] for r in returned
        ),
        "policy_repairs": len(repaired),
        "returned_after_repair": sum(r["result"] is not None for r in repaired),
        "model_requests": len(attempts),
        "completed_model_responses": sum(
            a["status"] == "response_received" for a in attempts
        ),
        "errors": dict(Counter(r["error"] for r in rows if r["error"])),
        "machine_check_failures": dict(
            Counter(key for r in returned for key, ok in r["checks"].items() if not ok)
        ),
        "latency_ms_median_all_attempts": statistics.median(
            r["latency_ms"] for r in rows
        ),
        "latency_ms_total": sum(r["latency_ms"] for r in rows),
    }


def compare_reports(baseline: dict, treatment: dict) -> dict:
    expected = [
        (c["case_id"], digest(request_for(c).model_dump(mode="json"))) for c in cases()
    ]
    for phase, report in (("baseline", baseline), ("treatment", treatment)):
        if report["identity"] != identity() or report["phase"] != phase:
            raise ValueError("Changed suite or phase identity")
        if [(r["case_id"], r["request_sha256"]) for r in report["records"]] != expected:
            raise ValueError("Changed case schedule or request identity")
    for key in ("model", "model_digest", "temperature", "seed", "seed_state"):
        if baseline["runtime"][key] != treatment["runtime"][key]:
            raise ValueError("Changed model configuration")
    return {
        "identity": identity(),
        "baseline_sha": baseline["runtime"]["git_commit"],
        "treatment_sha": treatment["runtime"]["git_commit"],
        "baseline": measurements(baseline),
        "treatment": measurements(treatment),
        "availability_transitions": dict(
            Counter(
                f"{'returned' if b['result'] else 'withheld'} -> {'returned' if t['result'] else 'withheld'}"
                for b, t in zip(baseline["records"], treatment["records"], strict=True)
            )
        ),
        "semantic_assessment": "Separate unchanged-rubric manual review; no composite score or statistical reliability claim.",
    }


def compare_reviews(baseline: dict, treatment: dict) -> dict:
    if [(r["case_id"]) for r in baseline["reviews"]] != [
        c["case_id"] for c in cases()
    ] or [(r["case_id"]) for r in treatment["reviews"]] != [
        c["case_id"] for c in cases()
    ]:
        raise ValueError("Review schedule changed")
    return {
        "method": "Unblinded implementation-assistant judgments; counts overlap. Incident classification applies to SOC; benign false positives must be read in case context. No aggregate pass score.",
        "baseline_labels": {
            key: dict(Counter(r[key] for r in baseline["reviews"]))
            for key in DIMENSIONS
        },
        "treatment_labels": {
            key: dict(Counter(r[key] for r in treatment["reviews"]))
            for key in DIMENSIONS
        },
        "common_returned_transitions": {
            key: dict(
                Counter(
                    f"{b[key]} -> {t[key]}"
                    for b, t in zip(
                        baseline["reviews"], treatment["reviews"], strict=True
                    )
                    if b[key] != "unassessable" and t[key] != "unassessable"
                )
            )
            for key in DIMENSIONS
        },
    }
