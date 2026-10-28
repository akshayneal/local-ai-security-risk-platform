"""Non-official V3.1 transitions under V3.2; never a corrected pass rate."""

import json
from typing import Any

from evals.provenance import ROOT
from evals.semantic_runner_v31 import verify_report as verify_v31
from evals.semantic_runner_v32 import load_suite
from evals.semantic_schemas_v31 import SemanticReport as V31Report
from evals.semantic_validators_v32 import score_response


def diagnostic_rescore() -> dict[str, Any]:
    directory = ROOT / "Documentation/evaluation_v3_1"
    report = V31Report.model_validate_json(
        (directory / "semantic_baseline_3trial.json").read_bytes()
    )
    verify_v31(report)
    cases = {c.legacy_case_id: c for c in load_suite().cases if c.legacy_case_id}
    targets = {
        ("V31-SOC-007", 1): (
            "attempt_vs_completion",
            "fact_grounding",
            "process_execution",
            None,
            True,
        ),
        ("V31-SOC-008", 2): (
            "possessive_claim",
            "fact_grounding",
            "maintenance_authorized",
            None,
            True,
        ),
        ("V31-GOV-005", 3): (
            "known_frequency_missingness",
            "known_value_consistency",
            None,
            "audit_frequency",
            False,
        ),
        ("V31-SOC-009", 3): (
            "proposed_step_ip",
            "proposed_identity_integrity",
            None,
            "ipv4",
            False,
        ),
    }
    rows = []
    for summary in report.cases:
        for trial in summary.trials:
            if trial.response is None:
                continue
            checks = score_response(cases[summary.test_id], trial.response)
            target = targets.get((summary.test_id, trial.trial))
            if target:
                label, kind, fact, key, expected = target
                selected = [
                    c
                    for c in checks
                    if c.check.type == kind
                    and c.check.fact == fact
                    and (
                        key is None
                        or c.check.value_key == key
                        or c.check.observable == key
                    )
                ]
                rows.append(
                    {
                        "case_id": summary.test_id,
                        "trial": trial.trial,
                        "target": label,
                        "expected_check_pass": expected,
                        "expectation_met": bool(selected)
                        and all(c.passed == expected for c in selected),
                        "historical_official_outcome": "pass"
                        if trial.passed
                        else "fail",
                        "diagnostic_checks": [
                            c.model_dump(mode="json") for c in selected
                        ],
                    }
                )
    return {
        "label": "non-official diagnostic transitions",
        "scorer_version": "3.2",
        "official_v31_unchanged": "37/39",
        "no_aggregate_rescored_pass_rate": True,
        "targets_met": sum(r["expectation_met"] for r in rows),
        "targets": len(rows),
        "moderate_support_scope": "V31-SOC-009/1 unclear authorization context remains manual review; absolute absence and explicit external scope are the conservative scored boundary.",
        "transitions": rows,
    }


def main() -> None:
    result = diagnostic_rescore()
    path = ROOT / "evals/results/v31_diagnostic_transitions_v32.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in result.items() if k != "transitions"}, indent=2))
    print(f"Diagnostic only: {path}")


if __name__ == "__main__":
    main()
