"""Compare frozen reports only when their suites and executed cases agree."""

import argparse
import json
from pathlib import Path
from typing import Any

from evals.schemas import EvaluationReport


def compare_reports(
    baseline: EvaluationReport, hardened: EvaluationReport
) -> dict[str, Any]:
    if baseline.suite_hash != hardened.suite_hash:
        raise ValueError("Suite hashes differ; before/after comparison refused")
    before = {result.test_id: result for result in baseline.results}
    after = {result.test_id: result for result in hardened.results}
    if (
        set(before) != set(after)
        or len(before) != len(baseline.results)
        or len(after) != len(hardened.results)
    ):
        raise ValueError("Executed case sets differ or contain duplicate IDs")
    if baseline.model != hardened.model:
        raise ValueError("Models differ; controlled comparison refused")
    groups: dict[str, list[str]] = {
        "newly_passing": [],
        "still_failing": [],
        "regressions": [],
        "unchanged_passing": [],
    }
    for case_id in sorted(before):
        old, new = before[case_id].passed, after[case_id].passed
        key = (
            ("unchanged_passing" if old else "newly_passing")
            if new
            else ("regressions" if old else "still_failing")
        )
        groups[key].append(case_id)
    return {
        "suite_hash": baseline.suite_hash,
        "baseline_pass_rate": baseline.pass_rate,
        "hardened_pass_rate": hardened.pass_rate,
        "percentage_point_change": hardened.pass_rate - baseline.pass_rate,
        **groups,
        "category_changes": {
            category: {
                "baseline": baseline.category_summary[category].pass_rate,
                "hardened": hardened.category_summary[category].pass_rate,
            }
            for category in baseline.category_summary
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("hardened", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        comparison = compare_reports(
            EvaluationReport.model_validate_json(args.baseline.read_bytes()),
            EvaluationReport.model_validate_json(args.hardened.read_bytes()),
        )
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(comparison, indent=2) + "\n"
    print(rendered, end="")
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
