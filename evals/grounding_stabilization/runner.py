"""Once-per-phase bounded local experiment with actual retrieval provenance."""

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from app import governance_analyzer, soc_analyzer
from app.local_diagnostics import LocalDiagnosticTrace
from app.model_metrics import local_model_metrics
from app.schemas import GovernanceRiskRequest
from app.soc_inputs import MicrosoftSocAdapter
from evals.provenance import ROOT, collect_provenance

DIRECTORY = Path(__file__).resolve().parent


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def cases() -> list[dict]:
    return json.loads((DIRECTORY / "cases.json").read_bytes())


def identity() -> dict:
    return {
        "semantic_case_sha256": digest(cases()),
        "source_sha256": {
            name: hashlib.sha256((DIRECTORY / name).read_bytes()).hexdigest()
            for name in ("cases.json", "plan.json", "rubric.md", "runner.py")
        },
    }


def request_for(case: dict):
    if case["workflow"] == "soc_alert":
        return MicrosoftSocAdapter().normalize(case["bundle"]).request
    return GovernanceRiskRequest(**case["request"])


def checks(result: dict, retrieved_ids: list[str], case: dict) -> dict:
    sources = {s["source_id"] for s in result["source_references"]}
    ordinary = json.dumps({k: v for k, v in result.items() if k != "source_references"})
    identity_key = "alert_id" if case["workflow"] == "soc_alert" else "system_name"
    expected = (
        case["case_id"] if identity_key == "alert_id" else case["request"][identity_key]
    )
    return {
        "authorized_sources": sources <= set(retrieved_ids),
        "source_ids_absent_from_prose": not any(s in ordinary for s in retrieved_ids),
        "case_identity_exact": result[identity_key] == expected,
        "schema_accepted": True,
    }


def trial(case: dict) -> dict:
    request = request_for(case)
    module = soc_analyzer if case["workflow"] == "soc_alert" else governance_analyzer
    analyze = (
        module.analyze_soc_alert
        if case["workflow"] == "soc_alert"
        else module.analyze_governance_risk
    )
    retrieve = module.retrieve_for_analysis
    retrieval = []

    def capture(mode, query, limit, **kwargs):
        selected = retrieve(mode, query, limit, **kwargs)
        retrieval.append(
            {
                "query_sha256": hashlib.sha256(query.encode()).hexdigest(),
                "query_utf8_bytes": len(query.encode()),
                "source_ids": [c["source_id"] for c in selected.cards],
                "context_sha256": digest(selected.context),
            }
        )
        return selected

    trace = LocalDiagnosticTrace(case["case_id"])
    started = time.perf_counter()
    row = {
        "case_id": case["case_id"],
        "request_sha256": digest(request.model_dump(mode="json")),
    }
    with (
        local_model_metrics() as metrics,
        patch.object(module, "retrieve_for_analysis", capture),
    ):
        try:
            response = analyze(request, trace=trace)
            result = response.model_dump(mode="json")
            row.update(
                result=result,
                error=None,
                checks=checks(result, retrieval[0]["source_ids"], case),
            )
        except Exception as exc:  # noqa: BLE001 -- fixed class allowlist, never raw errors.
            name = type(exc).__name__
            row.update(
                result=None,
                error=name
                if name
                in {
                    "OutputPolicyError",
                    "ValidationError",
                    "RetryError",
                    "EvidenceBudgetError",
                }
                else "analysis_failed",
                checks=None,
            )
    row.update(
        latency_ms=(time.perf_counter() - started) * 1000,
        retrieval=retrieval,
        model_attempts=metrics.attempts,
        diagnostics=trace.report(),
    )
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase", required=True, choices=("baseline", "treatment", "preflight")
    )
    args = parser.parse_args()
    assert identity() == json.loads((DIRECTORY / "freeze.json").read_bytes())
    for case in cases():
        request_for(case)
    if args.phase == "preflight":
        print(json.dumps(identity(), indent=2))
        return
    if os.getenv("RETRIEVAL_BACKEND", "legacy") != "legacy" or os.getenv(
        "RETRIEVAL_SHADOW_BACKEND"
    ):
        raise ValueError("Frozen plan requires legacy without shadow")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("Commit before live experiment")
    if (
        args.phase == "baseline"
        and subprocess.check_output(
            ["git", "diff", "73fd92c", "--", "app", "reference_material"], cwd=ROOT
        ).strip()
    ):
        raise ValueError("Untreated production changed")
    target = ROOT / f"evals/results/grounding_stabilization_{args.phase}.json"
    journal = target.with_suffix(".jsonl")
    if target.exists() or journal.exists():
        raise ValueError("Existing phase: no reruns or overwrite")
    report = {
        "identity": identity(),
        "phase": args.phase,
        "runtime": collect_provenance().model_dump(mode="json"),
        "started_utc": datetime.now(UTC).isoformat(),
        "records": [],
    }
    for case in cases():
        row = trial(case)
        report["records"].append(row)
        with journal.open("a", encoding="utf-8", newline="\n") as file:
            file.write(json.dumps(row) + "\n")
        print(
            f"{len(report['records'])}/8 {case['case_id']} {'returned' if row['result'] else 'withheld'}",
            flush=True,
        )
    report["finished_utc"] = datetime.now(UTC).isoformat()
    target.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
