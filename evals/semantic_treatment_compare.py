"""Same-suite V3.2 treatment comparison; no new scoring or generations."""

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from evals.semantic_runner_v32 import verify_report
from evals.semantic_schemas_v32 import SemanticReport


def measurements(report: SemanticReport) -> dict[str, Any]:
    trials = [t for c in report.cases for t in c.trials]
    durations = [t.duration_seconds for t in trials]
    calls = [m for t in trials for m in t.model_calls]
    return {
        "totals": report.totals.model_dump(),
        "stability": report.stability_counts,
        "categories": {k: v.model_dump() for k, v in report.category_summary.items()},
        "positive_controls": report.positive_control_totals.model_dump(),
        "initial_generations": sum(m.generation == "initial" for m in calls),
        "repair_generations": sum(m.generation == "repair" for m in calls),
        "repair_attempted_trials": sum(
            bool(t.analysis_trace and t.analysis_trace.get("repair_attempted"))
            for t in trials
        ),
        "repair_failed_trials": sum(
            bool(t.analysis_trace and t.analysis_trace.get("repair_failed"))
            for t in trials
        ),
        "raw_calls": len(calls),
        "failed_raw_calls": sum(not m.completed for m in calls),
        "mean_trial_seconds": statistics.mean(durations),
        "median_trial_seconds": statistics.median(durations),
        "repair_generation_seconds": sum(
            m.duration_seconds for m in calls if m.generation == "repair"
        ),
    }


def compare_reports(before: SemanticReport, after: SemanticReport) -> dict[str, Any]:
    for key in (
        "report_version",
        "scorer_version",
        "suite_byte_sha256",
        "suite_semantic_sha256",
        "trials_per_case",
    ):
        if getattr(before, key) != getattr(after, key):
            raise ValueError(f"Incompatible {key}")
    for key in ("model", "model_digest", "temperature", "seed", "seed_state"):
        if getattr(before.provenance, key) != getattr(after.provenance, key):
            raise ValueError(f"Incompatible model configuration: {key}")
    verify_report(before)
    verify_report(after)
    old, new = measurements(before), measurements(after)
    return {
        "comparison_version": "3.2-treatment",
        "suite_byte_sha256": before.suite_byte_sha256,
        "suite_semantic_sha256": before.suite_semantic_sha256,
        "scorer_version": before.scorer_version,
        "baseline_runtime": before.provenance.model_dump(),
        "treatment_runtime": after.provenance.model_dump(),
        "before": old,
        "after": new,
        "pass_rate_percentage_point_change": after.totals.pass_rate
        - before.totals.pass_rate,
        "mean_trial_seconds_change": new["mean_trial_seconds"]
        - old["mean_trial_seconds"],
        "median_trial_seconds_change": new["median_trial_seconds"]
        - old["median_trial_seconds"],
        "case_transitions": [
            {
                "case_id": a.test_id,
                "before": a.stability,
                "after": b.stability,
                "before_outcomes": [
                    "error" if t.error else "pass" if t.passed else "fail"
                    for t in a.trials
                ],
                "after_outcomes": [
                    "error" if t.error else "pass" if t.passed else "fail"
                    for t in b.trials
                ],
                "before_totals": a.totals.model_dump(),
                "after_totals": b.totals.model_dump(),
            }
            for a, b in zip(before.cases, after.cases, strict=True)
        ],
        "changed_behavior_files": [
            n for n, h in before.file_sha256.items() if after.file_sha256.get(n) != h
        ],
        "interpretation": "One unseeded three-trial local before/after comparison, no ablation or population confidence. Official scores retain frozen lexical imperfections; manual review does not replace the aggregate. Runtime differences are recorded, not isolated causally.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("treatment", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    before = SemanticReport.model_validate_json(args.baseline.read_bytes())
    after = SemanticReport.model_validate_json(args.treatment.read_bytes())
    result = compare_reports(before, after)
    if args.output.exists():
        parser.error("Refusing to overwrite comparison evidence")
    args.output.write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                k: result[k]
                for k in [
                    "pass_rate_percentage_point_change",
                    "mean_trial_seconds_change",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
