"""Run the real local analyzers: python -m evals.runner [--case ID]."""

import argparse
import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from app.governance_analyzer import analyze_governance_risk
from app.ollama_client import OLLAMA_MODEL
from app.reference_loader import get_reference_ids, get_relevant_references
from app.schemas import GovernanceRiskRequest, SocAlertRequest
from app.soc_analyzer import analyze_soc_alert
from evals.schemas import (
    EvaluationCase,
    EvaluationReport,
    EvaluationResult,
    EvaluationSuite,
    Summary,
)
from evals.validators import validate_check

CASE_PATH = Path(__file__).parent / "cases" / "adversarial.json"
RESULT_DIR = Path(__file__).parent / "results"


def load_suite(path: Path = CASE_PATH) -> tuple[EvaluationSuite, str]:
    data = path.read_bytes()
    return EvaluationSuite.model_validate_json(data), hashlib.sha256(data).hexdigest()


def select_cases(
    suite: EvaluationSuite,
    *,
    case_id: str | None = None,
    category: str | None = None,
) -> list[EvaluationCase]:
    cases = [
        case
        for case in suite.cases
        if (case_id is None or case.test_id == case_id)
        and (category is None or case.category == category)
    ]
    if not cases:
        raise ValueError("No cases match the requested selection")
    return cases


def run_case(case: EvaluationCase) -> EvaluationResult:
    start = perf_counter()
    source_ids: list[str] = []
    try:
        request_type = (
            SocAlertRequest if case.mode == "soc_alert" else GovernanceRiskRequest
        )
        request = request_type.model_validate(case.input)
        references = case.reference_overrides
        if references is None:
            references = get_relevant_references(
                mode=case.mode,
                query=request.model_dump_json(),
                limit=5 if case.mode == "soc_alert" else 6,
            )
        source_ids = sorted(get_reference_ids(references))
        analyzer = (
            analyze_soc_alert if case.mode == "soc_alert" else analyze_governance_risk
        )
        response = analyzer(request, references=references).model_dump(mode="json")
        checks = [
            validate_check(
                check, response, mode=case.mode, provided_source_ids=source_ids
            )
            for check in case.checks
        ]
        return EvaluationResult(
            test_id=case.test_id,
            category=case.category,
            severity=case.severity,
            mode=case.mode,
            passed=all(check.passed for check in checks),
            check_results=checks,
            response=response,
            provided_source_ids=source_ids,
            duration_seconds=perf_counter() - start,
        )
    except Exception as exc:  # noqa: BLE001 - isolate every application case failure
        # Deliberately omit exception payloads: they can include prompts, paths,
        # connection details, or raw model output. The class identifies failure type.
        return EvaluationResult(
            test_id=case.test_id,
            category=case.category,
            severity=case.severity,
            mode=case.mode,
            passed=False,
            error=f"Application call failed ({type(exc).__name__})",
            provided_source_ids=source_ids,
            duration_seconds=perf_counter() - start,
        )


def summarize(results: list[EvaluationResult]) -> Summary:
    passed = sum(result.passed for result in results)
    return Summary(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        pass_rate=100 * passed / len(results) if results else 0,
    )


def build_report(results: list[EvaluationResult], suite_hash: str) -> EvaluationReport:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    summary = summarize(results)
    return EvaluationReport(
        model=OLLAMA_MODEL,
        timestamp_utc=datetime.now(UTC).isoformat(),
        git_commit=commit,
        suite_hash=suite_hash,
        selected_case_ids=[result.test_id for result in results],
        total_cases=summary.total,
        passed=summary.passed,
        failed=summary.failed,
        pass_rate=summary.pass_rate,
        category_summary={
            category: summarize([r for r in results if r.category == category])
            for category in sorted({r.category for r in results})
        },
        severity_summary={
            severity: summarize([r for r in results if r.severity == severity])
            for severity in sorted({r.severity for r in results})
        },
        results=results,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", dest="case_id")
    parser.add_argument("--category")
    args = parser.parse_args(argv)
    try:
        suite, suite_hash = load_suite()
        cases = select_cases(suite, case_id=args.case_id, category=args.category)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"AI Security Evaluation\nModel: {OLLAMA_MODEL}", flush=True)
    results = []
    for case in cases:
        print(f"[RUN] {case.test_id} - {case.name}", flush=True)
        result = run_case(case)
        results.append(result)
        print(
            f"[{'PASS' if result.passed else 'FAIL'}] {case.test_id}"
            f" ({result.duration_seconds:.1f}s) {result.error or ''}",
            flush=True,
        )
    report = build_report(results, suite_hash)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    path = RESULT_DIR / f"evaluation_{stamp}.json"
    path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(
        f"Cases: {report.total_cases}\nPassed: {report.passed}\nFailed: {report.failed}"
        f"\nPass rate: {report.pass_rate:.1f}%\nReport: {path}",
        flush=True,
    )
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
