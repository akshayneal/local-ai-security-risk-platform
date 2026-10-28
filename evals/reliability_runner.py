"""Sequential current-state V2 evaluation: --trials 3 [--dry-run]."""

import argparse
import json
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median
from time import perf_counter
from typing import Any
from unittest.mock import patch

from app.analysis_trace import AnalysisTrace
from app.ollama_client import client
from app.reference_loader import get_relevant_references
from app.schemas import (
    GovernanceRiskRequest,
    GovernanceRiskResponse,
    SocAlertRequest,
    SocAlertResponse,
)
from evals.observables import extract_observables
from evals.provenance import collect_provenance, suite_hashes
from evals.reliability_schemas import (
    CaseReliabilitySummary,
    FieldStability,
    LatencySummary,
    ModelCall,
    ReliabilitySuite,
    RepeatedEvaluationReport,
    RuntimeProvenance,
    TrialResult,
    TrialTotals,
    ValueCount,
)
from evals.runner import RESULT_DIR, run_case, select_cases
from evals.schemas import EvaluationCase
from evals.validators import flatten_text, validate_check

CASE_PATH = Path(__file__).parent / "cases" / "adversarial_v2.json"


def load_suite(path: Path = CASE_PATH) -> ReliabilitySuite:
    return ReliabilitySuite.model_validate_json(path.read_bytes())


def validate_cases(cases: list[EvaluationCase]) -> None:
    """Validate all selected requests/references before the first generation."""
    for case in cases:
        schema = SocAlertRequest if case.mode == "soc_alert" else GovernanceRiskRequest
        request = schema.model_validate(case.input)
        references = case.reference_overrides
        if references is None:
            references = get_relevant_references(
                mode=case.mode,
                query=request.model_dump_json(),
                limit=5 if case.mode == "soc_alert" else 6,
            )
        ids = [reference.get("source_id") for reference in references]
        if any(
            not isinstance(value, str) or not value.strip() or value != value.strip()
            for value in ids
        ):
            raise ValueError(f"Unusable reference source ID in {case.test_id}")
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate reference source ID in {case.test_id}")
        response_schema = (
            SocAlertResponse if case.mode == "soc_alert" else GovernanceRiskResponse
        )
        fields = response_schema.model_fields
        for check in case.checks:
            if check.field is not None and check.field not in fields:
                raise ValueError(
                    f"Unknown response field in {case.test_id}: {check.field}"
                )
            if (
                check.type == "required_observable_present"
                and check.value
                not in extract_observables(
                    flatten_text(case.input), check.observable_type
                )
            ):
                raise ValueError(
                    f"Required observable absent from input: {case.test_id}"
                )


def preflight(
    path: Path = CASE_PATH,
    *,
    trials: int = 3,
    case_id: str | None = None,
    category: str | None = None,
) -> tuple[ReliabilitySuite, list[EvaluationCase], tuple[str, str], RuntimeProvenance]:
    if trials < 1:
        raise ValueError("Trials must be a positive integer")
    suite = load_suite(path)
    # Validate the entire suite even when a filtered run is requested.
    validate_cases(suite.cases)
    cases = select_cases(suite, case_id=case_id, category=category)
    hashes = suite_hashes(path)
    provenance = collect_provenance()
    return suite, cases, hashes, provenance


def latency(durations: list[float]) -> LatencySummary:
    return LatencySummary(
        completed=len(durations),
        minimum_seconds=min(durations) if durations else None,
        median_seconds=median(durations) if durations else None,
        mean_seconds=mean(durations) if durations else None,
        maximum_seconds=max(durations) if durations else None,
    )


def trial_totals(trials: list[TrialResult], requested: int) -> TrialTotals:
    valid = [trial for trial in trials if trial.result.error is None]
    passed = sum(trial.result.passed for trial in valid)
    return TrialTotals(
        trials_requested=requested,
        trials_attempted=len(trials),
        trials_completed=len(valid),
        trials_passed=passed,
        trials_failed=len(valid) - passed,
        application_error_count=len(trials) - len(valid),
        pass_rate=100 * passed / len(valid) if valid else 0,
    )


def structured_stability(
    trials: list[TrialResult], mode: str
) -> dict[str, FieldStability]:
    responses = [
        trial.result.response for trial in trials if trial.result.error is None
    ]
    fields = (
        ["severity", "likely_incident_type"]
        if mode == "soc_alert"
        else ["risk_level", "decision"]
    )
    summary = {}
    for field in [*fields, "source_id_set"]:
        values = [
            sorted(
                {
                    source["source_id"]
                    for source in response.get("source_references", [])
                }
            )
            if field == "source_id_set"
            else response.get(field)
            for response in responses
        ]
        counts = Counter(json.dumps(value, sort_keys=True) for value in values)
        summary[field] = FieldStability(
            observed_values=[
                ValueCount(value=json.loads(value), count=count)
                for value, count in sorted(counts.items())
            ],
            identical=len(counts) == 1 if values else None,
        )
    return summary


def summarize_case(
    case: EvaluationCase, trials: list[TrialResult], requested: int
) -> CaseReliabilitySummary:
    totals = trial_totals(trials, requested)
    if not totals.trials_completed:
        stability = "infrastructure_error"
    elif totals.trials_passed == totals.trials_completed:
        stability = "stable_pass"
    elif totals.trials_failed == totals.trials_completed:
        stability = "stable_fail"
    else:
        stability = "mixed"
    return CaseReliabilitySummary(
        **totals.model_dump(),
        test_id=case.test_id,
        category=case.category,
        severity=case.severity,
        mode=case.mode,
        stability=stability,
        latency=latency(
            [
                trial.result.duration_seconds
                for trial in trials
                if trial.result.error is None
            ]
        ),
        structured_output_stability=structured_stability(trials, case.mode),
        trials=trials,
    )


def run_trial(case: EvaluationCase, number: int) -> TrialResult:
    calls = []
    trace = AnalysisTrace()
    original_chat = client.chat

    def timed_chat(*args: Any, **kwargs: Any) -> Any:
        start = perf_counter()
        try:
            response = original_chat(*args, **kwargs)
        except Exception as exc:  # Observe, then preserve existing retry behavior.
            calls.append(
                ModelCall(
                    duration_seconds=perf_counter() - start,
                    completed=False,
                    error_type=type(exc).__name__,
                    generation="repair" if trace.repair_attempted else "initial",
                )
            )
            raise
        calls.append(
            ModelCall(
                duration_seconds=perf_counter() - start,
                completed=True,
                generation="repair" if trace.repair_attempted else "initial",
            )
        )
        return response

    # Evaluation-only instrumentation; no production retry/sampling changes.
    with patch.object(client, "chat", timed_chat):
        result = run_case(case, trace=trace)
    return TrialResult(
        trial=number, result=result, model_calls=calls, analysis_trace=asdict(trace)
    )


def build_report(
    suite: ReliabilitySuite,
    cases: list[EvaluationCase],
    trials_by_case: dict[str, list[TrialResult]],
    *,
    trials: int,
    hashes: tuple[str, str],
    provenance: RuntimeProvenance,
    started_utc: str,
    ended_utc: str,
) -> RepeatedEvaluationReport:
    summaries = [
        summarize_case(case, trials_by_case[case.test_id], trials) for case in cases
    ]
    all_trials = [trial for summary in summaries for trial in summary.trials]
    calls = [call for trial in all_trials for call in trial.model_calls]
    totals = trial_totals(all_trials, len(cases) * trials)
    return RepeatedEvaluationReport(
        suite_name=suite.name,
        suite_version=suite.version,
        suite_byte_sha256=hashes[0],
        suite_semantic_sha256=hashes[1],
        provenance=provenance,
        started_utc=started_utc,
        ended_utc=ended_utc,
        trials_per_case=trials,
        selected_case_ids=[case.test_id for case in cases],
        total_cases=len(cases),
        totals=totals,
        total_model_calls_attempted=len(calls),
        total_completed_model_calls=sum(call.completed for call in calls),
        model_call_error_count=sum(not call.completed for call in calls),
        total_infrastructure_errors=totals.application_error_count,
        stability_counts={
            kind: sum(summary.stability == kind for summary in summaries)
            for kind in ["stable_pass", "stable_fail", "mixed", "infrastructure_error"]
        },
        category_summary={
            category: trial_totals(
                [
                    trial
                    for summary in summaries
                    if summary.category == category
                    for trial in summary.trials
                ],
                sum(summary.category == category for summary in summaries) * trials,
            )
            for category in sorted({case.category for case in cases})
        },
        latency=latency(
            [
                trial.result.duration_seconds
                for trial in all_trials
                if trial.result.error is None
            ]
        ),
        model_call_latency=latency(
            [call.duration_seconds for call in calls if call.completed]
        ),
        cases=summaries,
    )


def verify_report(report: RepeatedEvaluationReport, path: Path = CASE_PATH) -> None:
    """Recompute all aggregates/diagnostics from trials before freezing or reuse."""
    suite = load_suite(path)
    cases = [case for case in suite.cases if case.test_id in report.selected_case_ids]
    if [case.test_id for case in cases] != report.selected_case_ids:
        raise ValueError("Unknown, duplicated or reordered selected case IDs")
    if [case.test_id for case in cases] != [case.test_id for case in report.cases]:
        raise ValueError("Report case inventory mismatch")
    for case, summary in zip(cases, report.cases, strict=True):
        if [trial.trial for trial in summary.trials] != list(
            range(1, report.trials_per_case + 1)
        ):
            raise ValueError("Missing or duplicated trial numbers")
        for trial in summary.trials:
            result = trial.result
            if (result.test_id, result.category, result.severity, result.mode) != (
                case.test_id,
                case.category,
                case.severity,
                case.mode,
            ):
                raise ValueError("Trial identity mismatch")
            if result.error is None:
                checks = [
                    validate_check(
                        check,
                        result.response,
                        mode=case.mode,
                        provided_source_ids=result.provided_source_ids,
                        original_input=case.input,
                    )
                    for check in case.checks
                ]
                if checks != result.check_results or result.passed != all(
                    check.passed for check in checks
                ):
                    raise ValueError("Trial scoring mismatch")
    rebuilt = build_report(
        suite,
        cases,
        {case.test_id: case.trials for case in report.cases},
        trials=report.trials_per_case,
        hashes=suite_hashes(path),
        provenance=report.provenance,
        started_utc=report.started_utc,
        ended_utc=report.ended_utc,
    )
    if rebuilt != report:
        raise ValueError("Report aggregation, hash or stability mismatch")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--case", dest="case_id")
    parser.add_argument("--category")
    args = parser.parse_args(argv)
    try:
        suite, cases, hashes, provenance = preflight(
            trials=args.trials, case_id=args.case_id, category=args.category
        )
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(
        f"Evaluation V2 Preflight\nCases: {len(cases)}\nCategories: {len({case.category for case in cases})}"
        f"\nTrials per case: {args.trials}\nPlanned model calls: {len(cases) * args.trials} (before any existing retries)"
        f"\nByte suite hash: {hashes[0]}\nSemantic suite hash: {hashes[1]}"
        "\nRequest validation: PASS\nCheck validation: PASS\nReference validation: PASS\nProvenance collection: PASS",
        flush=True,
    )
    if provenance.unavailable:
        print(
            "Optional provenance unavailable: " + "; ".join(provenance.unavailable),
            flush=True,
        )
    if args.dry_run:
        print("No Ollama generations executed.", flush=True)
        return 0
    started = datetime.now(UTC).isoformat()
    results = {}
    for case in cases:
        results[case.test_id] = []
        for number in range(1, args.trials + 1):
            print(f"[RUN] {case.test_id} trial {number}/{args.trials}", flush=True)
            trial = run_trial(case, number)
            results[case.test_id].append(trial)
            outcome = (
                "ERROR"
                if trial.result.error
                else "PASS"
                if trial.result.passed
                else "FAIL"
            )
            print(
                f"[{outcome}] {case.test_id} trial {number} ({trial.result.duration_seconds:.2f}s)",
                flush=True,
            )
    report = build_report(
        suite,
        cases,
        results,
        trials=args.trials,
        hashes=hashes,
        provenance=provenance,
        started_utc=started,
        ended_utc=datetime.now(UTC).isoformat(),
    )
    verify_report(report)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    path = RESULT_DIR / f"reliability_v2_{stamp}.json"
    path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(
        f"Report: {path}\nTrial pass rate: {report.totals.pass_rate:.1f}%\nStability: {report.stability_counts}\nApplication/runtime errors: {report.total_infrastructure_errors}",
        flush=True,
    )
    return (
        2
        if report.total_infrastructure_errors
        else 1
        if report.totals.trials_failed
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
