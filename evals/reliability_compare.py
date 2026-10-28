"""Compare same-suite repeated V2 experiments without changing their scores."""

import argparse
import json
from pathlib import Path
from typing import Any

from evals.reliability_runner import verify_report
from evals.reliability_schemas import RepeatedEvaluationReport


def compare_reports(
    before: RepeatedEvaluationReport, after: RepeatedEvaluationReport
) -> dict[str, Any]:
    for field in ("suite_semantic_sha256", "suite_byte_sha256", "trials_per_case"):
        if getattr(before, field) != getattr(after, field):
            raise ValueError(f"Incompatible {field}; comparison refused")
    if before.provenance.model != after.provenance.model:
        raise ValueError("Models differ; comparison refused")
    if before.selected_case_ids != after.selected_case_ids:
        raise ValueError("Case inventory differs; comparison refused")
    verify_report(before)
    verify_report(after)
    pairs = list(zip(before.cases, after.cases, strict=True))
    transitions = {
        old.test_id: {
            "before": old.stability,
            "after": new.stability,
            "before_pass_rate": old.pass_rate,
            "after_pass_rate": new.pass_rate,
            "percentage_point_change": new.pass_rate - old.pass_rate,
            "before_errors": old.application_error_count,
            "after_errors": new.application_error_count,
        }
        for old, new in pairs
    }
    latency = {}
    for scope in ("latency", "model_call_latency"):
        old, new = getattr(before, scope), getattr(after, scope)
        latency[scope] = {"before": old.model_dump(), "after": new.model_dump()}
        for metric in ("mean_seconds", "median_seconds"):
            a, b = getattr(old, metric), getattr(new, metric)
            latency[scope][f"{metric}_delta"] = (
                b - a if a is not None and b is not None else None
            )
    return {
        "suite_byte_sha256": before.suite_byte_sha256,
        "suite_semantic_sha256": before.suite_semantic_sha256,
        "model": before.provenance.model,
        "trials_per_case": before.trials_per_case,
        "before_totals": before.totals.model_dump(),
        "after_totals": after.totals.model_dump(),
        "percentage_point_change": after.totals.pass_rate - before.totals.pass_rate,
        "before_stability": before.stability_counts,
        "after_stability": after.stability_counts,
        "case_changes": transitions,
        "stable_failures_resolved": [
            a.test_id
            for a, b in pairs
            if a.stability == "stable_fail" and b.stability == "stable_pass"
        ],
        "stable_failures_became_mixed": [
            a.test_id
            for a, b in pairs
            if a.stability == "stable_fail" and b.stability == "mixed"
        ],
        "new_stable_failures": [
            a.test_id
            for a, b in pairs
            if a.stability != "stable_fail" and b.stability == "stable_fail"
        ],
        "mixed_to_stable_pass": [
            a.test_id
            for a, b in pairs
            if a.stability == "mixed" and b.stability == "stable_pass"
        ],
        "stable_pass_regressions": [
            a.test_id
            for a, b in pairs
            if a.stability == "stable_pass" and b.stability != "stable_pass"
        ],
        "pass_rate_regressions": [
            a.test_id for a, b in pairs if b.pass_rate < a.pass_rate
        ],
        "category_changes": {
            category: {
                "before": before.category_summary[category].model_dump(),
                "after": after.category_summary[category].model_dump(),
                "percentage_point_change": after.category_summary[category].pass_rate
                - before.category_summary[category].pass_rate,
            }
            for category in before.category_summary
        },
        "repairs": {"before": repair_metrics(before), "after": repair_metrics(after)},
        "application_errors": {
            "before": before.total_infrastructure_errors,
            "after": after.total_infrastructure_errors,
        },
        "raw_call_errors": {
            "before": before.model_call_error_count,
            "after": after.model_call_error_count,
        },
        "latency": latency,
    }


def repair_metrics(report: RepeatedEvaluationReport) -> dict[str, Any]:
    trials = [trial for case in report.cases for trial in case.trials]
    traces = [getattr(trial, "analysis_trace", None) for trial in trials]
    recorded = all(trace is not None for trace in traces)
    return {
        "tracing_recorded": recorded,
        "initial_generations": sum(
            stage["stage"] == "generation_started" and stage["generation"] == 0
            for trace in traces
            if trace
            for stage in trace["stages"]
        )
        if recorded
        else None,
        "repair_generations": sum(
            bool(trace["repair_attempted"]) for trace in traces if trace
        )
        if recorded
        else None,
        "failed_repairs": sum(bool(trace["repair_failed"]) for trace in traces if trace)
        if recorded
        else None,
        "total_raw_model_calls": report.total_model_calls_attempted,
        "repair_frequency": sum(
            bool(trace["repair_attempted"]) for trace in traces if trace
        )
        / len(trials)
        if recorded and trials
        else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = compare_reports(
            RepeatedEvaluationReport.model_validate_json(args.before.read_bytes()),
            RepeatedEvaluationReport.model_validate_json(args.after.read_bytes()),
        )
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2) + "\n"
    print(rendered, end="")
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
