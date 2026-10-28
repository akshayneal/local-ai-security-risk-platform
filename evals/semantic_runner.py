"""Sequential V3 measurement: python -m evals.semantic_runner --trials 3 [--dry-run]."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from app.schemas import (
    GovernanceRiskRequest,
    GovernanceRiskResponse,
    SocAlertRequest,
    SocAlertResponse,
)
from evals.observables import extract_observables
from evals.provenance import (
    BEHAVIOR_FILES,
    ROOT,
    byte_hash,
    collect_provenance,
    suite_hashes,
)
from evals.reliability_runner import run_trial as run_application_trial
from evals.reliability_schemas import RuntimeProvenance, TrialTotals
from evals.schemas import EvalCheck, EvaluationCase
from evals.semantic_schemas import (
    SemanticCase,
    SemanticCaseReport,
    SemanticReport,
    SemanticSuite,
    SemanticTrial,
)
from evals.semantic_validators import score_response, strings

CASE_PATH = ROOT / "evals/cases/semantic_grounding_v3.json"
RESULT_DIR = ROOT / "evals/results"
V3_FILES = (
    "evals/cases/semantic_grounding_v3.json",
    "evals/semantic_schemas.py",
    "evals/semantic_validators.py",
    "evals/semantic_runner.py",
)


def response_type(
    case: SemanticCase,
) -> type[SocAlertResponse] | type[GovernanceRiskResponse]:
    return SocAlertResponse if case.mode == "soc_alert" else GovernanceRiskResponse


def load_suite(path: Path = CASE_PATH) -> SemanticSuite:
    suite = SemanticSuite.model_validate_json(path.read_bytes())
    for case in suite.cases:
        request = SocAlertRequest if case.mode == "soc_alert" else GovernanceRiskRequest
        request.model_validate(case.input)
        ids = [r.get("source_id") for r in case.reference_overrides]
        if any(not isinstance(i, str) or not i.strip() for i in ids) or len(ids) != len(
            set(ids)
        ):
            raise ValueError("Invalid reference identity")
        for reference in case.reference_overrides:
            if any(
                not isinstance(reference.get(k), str) or not reference[k].strip()
                for k in ["title", "framework", "content"]
            ):
                raise ValueError("Reference metadata missing")
        for fact in case.facts:
            if not set(fact.permitted_source_ids) <= set(ids):
                raise ValueError("Unknown permitted support source")
            evidence = strings(list(case.input.values())) + [
                r["content"]
                for r in case.reference_overrides
                if not fact.permitted_source_ids
                or r["source_id"] in fact.permitted_source_ids
            ]
            if not any(fact.evidence in text for text in evidence):
                raise ValueError("Fact evidence is absent from supplied scenario")
        for check in case.checks:
            if not set(check.fields) <= set(response_type(case).model_fields) - {
                "source_references"
            }:
                raise ValueError("Invalid response field")
            if check.type == "observable_integrity" and not extract_observables(
                "\n".join(strings(list(case.input.values()))), check.observable
            ):
                raise ValueError("Observable check needs supplied token")
    return suite


def behavior_hashes() -> dict[str, str]:
    return {
        name: byte_hash(ROOT / name) for name in sorted(set(BEHAVIOR_FILES + V3_FILES))
    }


def preflight(path: Path = CASE_PATH, trials: int = 3) -> SemanticSuite:
    if trials < 1:
        raise ValueError("Trials must be positive")
    return load_suite(path)


def run_trial(case: SemanticCase, number: int) -> SemanticTrial:
    # Reuse existing real-analyzer invocation and call/repair instrumentation.
    # The historical carrier's schema check is discarded, never a V3 score.
    carrier = EvaluationCase(
        test_id=f"{'SOC' if case.mode == 'soc_alert' else 'GOV'}-VTHREE-001",
        name=case.name,
        description=case.basis,
        category="unsupported_claims",
        severity="high",
        mode=case.mode,
        input=case.input,
        reference_overrides=case.reference_overrides,
        expected_safe_behavior="Measurement only",
        checks=[EvalCheck(type="schema_valid")],
    )
    application = run_application_trial(carrier, number)
    result = application.result
    checks = score_response(case, result.response) if result.error is None else []
    return SemanticTrial(
        trial=number,
        passed=result.error is None and all(c.passed for c in checks),
        response=result.response,
        error=result.error,
        checks=checks,
        duration_seconds=result.duration_seconds,
        provided_source_ids=result.provided_source_ids,
        model_calls=application.model_calls,
        analysis_trace=application.analysis_trace,
    )


def totals(trials: list[SemanticTrial], requested: int) -> TrialTotals:
    valid = [t for t in trials if t.error is None]
    passed = sum(t.passed for t in valid)
    return TrialTotals(
        trials_requested=requested,
        trials_attempted=len(trials),
        trials_completed=len(valid),
        trials_passed=passed,
        trials_failed=len(valid) - passed,
        application_error_count=len(trials) - len(valid),
        pass_rate=100 * passed / len(valid) if valid else 0,
    )


def build_report(
    suite: SemanticSuite,
    records: dict[str, list[SemanticTrial]],
    *,
    trials: int,
    hashes: tuple[str, str],
    provenance: RuntimeProvenance,
    file_hashes: dict[str, str],
    started: str,
    ended: str,
) -> SemanticReport:
    cases = []
    for case in suite.cases:
        summary = totals(records[case.test_id], trials)
        stability = (
            "infrastructure_error"
            if not summary.trials_completed
            else "stable_pass"
            if summary.trials_passed == summary.trials_completed
            else "stable_fail"
            if not summary.trials_passed
            else "mixed"
        )
        cases.append(
            SemanticCaseReport(
                test_id=case.test_id,
                category=case.category,
                positive_control=case.positive_control,
                totals=summary,
                stability=stability,
                trials=records[case.test_id],
            )
        )
    all_trials = [t for c in cases for t in c.trials]
    positive = [c for c in cases if c.positive_control]
    calls = [call for t in all_trials for call in t.model_calls]
    return SemanticReport(
        suite_byte_sha256=hashes[0],
        suite_semantic_sha256=hashes[1],
        provenance=provenance,
        file_sha256=file_hashes,
        started_utc=started,
        ended_utc=ended,
        trials_per_case=trials,
        totals=totals(all_trials, len(cases) * trials),
        category_summary={
            category: totals(
                [t for c in cases if c.category == category for t in c.trials],
                sum(c.category == category for c in cases) * trials,
            )
            for category in sorted({c.category for c in cases})
        },
        positive_control_totals=totals(
            [t for c in positive for t in c.trials], len(positive) * trials
        ),
        stability_counts={
            kind: sum(c.stability == kind for c in cases)
            for kind in ["stable_pass", "stable_fail", "mixed", "infrastructure_error"]
        },
        total_model_calls=len(calls),
        failed_model_calls=sum(not c.completed for c in calls),
        cases=cases,
    )


def verify_report(report: SemanticReport, path: Path = CASE_PATH) -> None:
    suite = load_suite(path)
    if [c.test_id for c in suite.cases] != [c.test_id for c in report.cases]:
        raise ValueError("Case inventory mismatch")
    for case, summary in zip(suite.cases, report.cases, strict=True):
        if [t.trial for t in summary.trials] != list(
            range(1, report.trials_per_case + 1)
        ):
            raise ValueError("Trial inventory mismatch")
        for trial in summary.trials:
            if trial.error is None:
                response_type(case).model_validate(trial.response)
                checks = score_response(case, trial.response)
                if checks != trial.checks or trial.passed != all(
                    c.passed for c in checks
                ):
                    raise ValueError("Scoring mismatch")
    rebuilt = build_report(
        suite,
        {c.test_id: c.trials for c in report.cases},
        trials=report.trials_per_case,
        hashes=suite_hashes(path),
        provenance=report.provenance,
        file_hashes=report.file_sha256,
        started=report.started_utc,
        ended=report.ended_utc,
    )
    if rebuilt != report:
        raise ValueError("Aggregate/hash mismatch")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        suite = preflight(trials=args.trials)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    hashes, provenance, files = (
        suite_hashes(CASE_PATH),
        collect_provenance(),
        behavior_hashes(),
    )
    print(
        f"V3 preflight PASS: {len(suite.cases)} cases; {len({c.category for c in suite.cases})} categories; "
        f"{args.trials} trials/case; {len(suite.cases) * args.trials} planned analyses\n"
        f"Byte SHA-256: {hashes[0]}\nSemantic SHA-256: {hashes[1]}\n"
        f"Provenance: {provenance.model_dump_json()}",
        flush=True,
    )
    if args.dry_run:
        print("No model generations executed.")
        return 0
    if provenance.model != "qwen3:8b" or not provenance.model_digest:
        parser.error("Configured local qwen3:8b is not verified installed")
    RESULT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    checkpoint = RESULT_DIR / f"semantic_v3_{stamp}.jsonl"
    started = datetime.now(UTC).isoformat()
    records = {}
    for case in suite.cases:
        records[case.test_id] = []
        for number in range(1, args.trials + 1):
            print(f"[RUN] {case.test_id} trial {number}", flush=True)
            trial = run_trial(case, number)
            records[case.test_id].append(trial)
            with checkpoint.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(
                    json.dumps(
                        {
                            "test_id": case.test_id,
                            "trial": trial.model_dump(mode="json"),
                        }
                    )
                    + "\n"
                )
            outcome = "ERROR" if trial.error else "PASS" if trial.passed else "FAIL"
            print(
                f"[{outcome}] {case.test_id} trial {number} ({trial.duration_seconds:.2f}s)",
                flush=True,
            )
    if files != behavior_hashes():
        raise ValueError(
            "Behavior files changed during inference; preserve checkpoint as invalid experiment"
        )
    report = build_report(
        suite,
        records,
        trials=args.trials,
        hashes=hashes,
        provenance=provenance,
        file_hashes=files,
        started=started,
        ended=datetime.now(UTC).isoformat(),
    )
    verify_report(report)
    path = checkpoint.with_suffix(".json")
    path.write_text(
        report.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        f"Report: {path}\nTotals: {report.totals.model_dump_json()}\nStability: {report.stability_counts}",
        flush=True,
    )
    return (
        2
        if report.totals.application_error_count
        else 1
        if report.totals.trials_failed
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
