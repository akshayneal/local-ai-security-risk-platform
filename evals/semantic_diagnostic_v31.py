"""Non-official diagnostic rescore of V3 final responses. Never a corrected V3 score."""

import json
from pathlib import Path
from typing import Any

from evals.provenance import ROOT
from evals.semantic_runner import verify_report as verify_v3
from evals.semantic_runner_v31 import load_suite
from evals.semantic_schemas import SemanticReport as V3Report
from evals.semantic_validators_v31 import score_response


def diagnostic_rescore() -> dict[str, Any]:
    directory = ROOT / "Documentation/evaluation_v3"
    report = V3Report.model_validate_json(
        (directory / "semantic_baseline_3trial.json").read_bytes()
    )
    verify_v3(report)
    ledger = json.loads((directory / "manual_review.json").read_bytes())
    cases = {c.legacy_case_id: c for c in load_suite().cases if c.legacy_case_id}
    records = {}
    for case in report.cases:
        adapted = cases[case.test_id].model_copy(deep=True)
        # Old V3 did NOT explicitly define protocol. The moderate SSH diagnostic
        # must not become retroactive authoritative truth through new metadata.
        adapted.checks = [
            c
            for c in adapted.checks
            if c.type not in {"protocol_grounding", "positive_protocol_present"}
        ]
        for trial in case.trials:
            if trial.response is not None:
                records[case.test_id, trial.trial] = score_response(
                    adapted, trial.response
                )
    rows = []
    for row in ledger["trials"]:
        checks = records.get((row["case_id"], row["trial"]), [])
        fixed = []
        for issue in row["validator_false_positives"]:
            kind, fact = issue["check"].split(":")
            found = [c for c in checks if c.check.type == kind and c.check.fact == fact]
            fixed.append(
                {
                    "check": issue["check"],
                    "resolved": bool(found) and all(c.passed for c in found),
                }
            )
        detected = []
        for issue in row["validator_false_negatives"]:
            kind = issue["kind"]
            observable = (
                "ipv4"
                if kind == "ipv4_field_scope"
                else "port"
                if kind == "port_scope"
                else None
            )
            found = (
                [
                    c
                    for c in checks
                    if c.check.type == "observable_integrity"
                    and c.check.observable == observable
                ]
                if observable
                else []
            )
            detected.append(
                {
                    "kind": kind,
                    "eligible": observable is not None,
                    "detected": any(not c.passed for c in found)
                    if observable
                    else None,
                }
            )
        omitted = (
            [
                c
                for c in checks
                if c.check.type == "positive_fact_present"
                and c.check.fact == "actor_attribution"
            ]
            if row["case_id"] == "V3-SOC-004"
            else []
        )
        rows.append(
            {
                "case_id": row["case_id"],
                "trial": row["trial"],
                "known_false_positive_checks": fixed,
                "known_missed_defects": detected,
                "supported_actor_omission_still_fails": all(
                    not c.passed for c in omitted
                )
                if omitted
                else None,
                "diagnostic_checks": [c.model_dump(mode="json") for c in checks],
            }
        )
    fps = [x for r in rows for x in r["known_false_positive_checks"]]
    fns = [x for r in rows for x in r["known_missed_defects"]]
    return {
        "label": "diagnostic rescore",
        "scorer_version": "3.1",
        "official_v3_unchanged": "27/36; 75.0%; evaluator version 3.0",
        "protocol_note": "Historical protocol not explicitly established; moderate SSH finding not adjudicated retroactively.",
        "known_false_positives_resolved": sum(x["resolved"] for x in fps),
        "known_false_positive_checks": len(fps),
        "known_high_confidence_missed_defects_detected": sum(
            x["detected"] is True for x in fns
        ),
        "known_high_confidence_missed_defects": sum(x["eligible"] for x in fns),
        "remaining_known_disagreements": [
            {"case_id": r["case_id"], "trial": r["trial"]}
            for r in rows
            if any(not x["resolved"] for x in r["known_false_positive_checks"])
            or any(
                x["eligible"] and not x["detected"] for x in r["known_missed_defects"]
            )
        ],
        "not_a_new_live_baseline": True,
        "no_aggregate_rescored_pass_rate": True,
        "trials": rows,
    }


def main() -> None:
    result = diagnostic_rescore()
    path = Path("evals/results/v3_diagnostic_rescore_v31.json")
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in result.items() if k != "trials"}, indent=2))
    print(f"Diagnostic only: {path}")


if __name__ == "__main__":
    main()
