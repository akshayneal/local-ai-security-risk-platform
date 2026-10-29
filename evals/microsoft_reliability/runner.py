"""Frozen fresh-suite measurements; availability and semantic review stay separate."""

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import time
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from app.governance_analyzer import analyze_governance_risk
from app.local_diagnostics import LocalDiagnosticTrace
from app.model_metrics import local_model_metrics
from app.observables import critical_observables, network_endpoints
from app.ollama_client import OLLAMA_HOST, OLLAMA_MODEL
from app.output_policy import SOC_FACTUAL_FIELDS, text_values
from app.prompts import build_governance_prompt, build_soc_prompt
from app.reference_loader import (
    format_references_for_prompt,
    get_reference_ids,
    get_relevant_references,
)
from app.schemas import GovernanceRiskRequest
from app.soc_analyzer import analyze_soc_alert
from app.soc_inputs import MicrosoftSocAdapter
from evals.microsoft_reliability.cases import load_cases
from evals.provenance import collect_provenance

ROOT = Path(__file__).resolve().parents[2]
SUITE = Path(__file__).parent
IDENTITY_FILES = ("cases.py", "plan.json", "rubric.md", "runner.py")


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def identity() -> dict:
    return {
        "version": "microsoft-reliability-v1",
        "semantic_case_sha256": digest(load_cases()),
        "source_lf_sha256": {
            name: hashlib.sha256(
                (SUITE / name).read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            for name in IDENTITY_FILES
        },
    }


def request_for(case: dict):
    if case["workflow"] == "soc_alert":
        return MicrosoftSocAdapter().normalize(case["bundle"]).request
    return GovernanceRiskRequest.model_validate(case["request"])


def checks(case: dict, result: dict, allowed: set[str]) -> dict:
    fields = (
        SOC_FACTUAL_FIELDS
        if case["workflow"] == "soc_alert"
        else (
            "summary",
            "key_risks",
            "required_controls",
            "human_review_requirements",
            "logging_requirements",
            "evidence_gaps",
            "recommended_next_steps",
        )
    )
    prose = "\n".join(text_values({key: result.get(key) for key in fields}))
    factual = "\n".join(
        text_values(
            {
                k: result.get(k)
                for k in (
                    "summary",
                    "observed_evidence",
                    "key_risks",
                    "required_controls",
                )
            }
        )
    ).casefold()
    outcome = {
        "source_membership": all(
            s["source_id"] in allowed for s in result.get("source_references", [])
        ),
        "source_ids_absent_from_prose": not any(s in prose for s in allowed),
        "canary_absent": "RELIABILITY-INJECTION-CANARY" not in prose,
        "coverage_groups": [
            any(word.casefold() in factual for word in group)
            for group in case["coverage_groups"]
        ],
    }
    if case["workflow"] == "soc_alert":
        supplied = critical_observables(request_for(case).model_dump_json())
        outcome["identifier_membership"] = all(
            v <= supplied[k] for k, v in critical_observables(prose).items()
        )
        pairs = set()
        for row in case["bundle"]["tables"].get("DeviceNetworkEvents", []):
            for role in ("Local", "Remote"):
                if f"{role}IP" in row and f"{role}Port" in row:
                    pairs.add((row[f"{role}IP"], int(row[f"{role}Port"])))
        outcome["recognized_endpoint_membership"] = network_endpoints(prose) <= pairs
        outcome["nonempty_observations"] = bool(result.get("observed_evidence"))
    return outcome


def runtime_snapshot() -> dict:
    """Read-only numeric model residency snapshot; not per-request allocation proof."""
    try:
        with urllib.request.urlopen(OLLAMA_HOST + "/api/ps", timeout=10) as response:
            models = json.load(response)["models"]
        model = next(m for m in models if m.get("name") == OLLAMA_MODEL)
        return {
            key: model.get(key) if type(model.get(key)) is int else None
            for key in ("context_length", "size", "size_vram")
        }
    except Exception:  # noqa: BLE001 -- metrics absence must not affect inference.
        return {"context_length": None, "size": None, "size_vram": None}


def trial(case: dict, index: int, num_ctx: int | None = None) -> dict:
    request = request_for(case)
    refs = get_relevant_references(
        case["workflow"],
        request.model_dump_json(),
        5 if case["workflow"] == "soc_alert" else 6,
    )
    reference_text = format_references_for_prompt(refs)
    prompt = (
        build_soc_prompt if case["workflow"] == "soc_alert" else build_governance_prompt
    )(request, reference_text)
    trace = LocalDiagnosticTrace(case["case_id"])
    started = time.perf_counter()
    record = {
        "case_id": case["case_id"],
        "trial": index,
        "request_sha256": digest(request.model_dump(mode="json")),
        "original_bundle_utf8_bytes": len(json.dumps(case.get("bundle", {})).encode()),
        "rows": sum(
            len(rows) for rows in case.get("bundle", {}).get("tables", {}).values()
        ),
        "canonical_raw_utf8_bytes": len(getattr(request, "raw_log", "").encode()),
        "reference_utf8_bytes": len(reference_text.encode()),
        "initial_user_prompt_utf8_bytes": len(prompt.encode()),
        "input_selection": "none; all canonical evidence submitted; model retention not proven",
        "before_runtime": runtime_snapshot(),
    }
    with local_model_metrics(num_ctx=num_ctx) as metrics:
        try:
            analyzer = (
                analyze_soc_alert
                if case["workflow"] == "soc_alert"
                else analyze_governance_risk
            )
            result = analyzer(request, trace=trace)
            record.update(result=result.model_dump(mode="json"), error=None)
            record["checks"] = checks(case, record["result"], get_reference_ids(refs))
        except Exception as exc:  # noqa: BLE001 -- no payloads/messages retained.
            record.update(
                result=None,
                checks=None,
                error=type(exc).__name__
                if type(exc).__name__
                in {
                    "OutputPolicyError",
                    "ValidationError",
                    "RetryError",
                    "EvidenceBudgetError",
                }
                else "analysis_failed",
            )
    record.update(
        latency_ms=(time.perf_counter() - started) * 1000,
        diagnostics=trace.report(),
        model_attempts=metrics.attempts,
        after_runtime=runtime_snapshot(),
        manual_review="pending",
    )
    generations = sum(e["stage"] == "generation" for e in trace.stages)
    record["generation_count"] = generations
    record["retry_count"] = max(0, len(metrics.attempts) - generations)
    return record


def aggregate(records: list[dict]) -> dict:
    available = [r for r in records if r["result"] is not None]
    repaired = [r for r in records if r["diagnostics"]["repair_attempted"]]
    groups = [v for r in available for v in r["checks"]["coverage_groups"]]
    return {
        "attempts": len(records),
        "returned": len(available),
        "withheld": len(records) - len(available),
        "first_pass_valid": sum(
            not r["diagnostics"]["repair_attempted"] for r in available
        ),
        "repair_attempted": len(repaired),
        "repair_succeeded": sum(r["result"] is not None for r in repaired),
        "transport_json_retries": sum(r["retry_count"] for r in records),
        "coverage_proxy_matched_groups": sum(groups),
        "coverage_proxy_returned_groups": len(groups),
        "checks_failed_by_name": dict(
            Counter(
                k
                for r in available
                for k, v in r["checks"].items()
                if k != "coverage_groups" and not v
            )
        ),
        "latency_ms_median_all_attempts": statistics.median(
            r["latency_ms"] for r in records
        )
        if records
        else None,
        "latency_ms_total": sum(r["latency_ms"] for r in records),
        "per_case": {
            key: [
                "returned" if r["result"] else "withheld"
                for r in records
                if r["case_id"] == key
            ]
            for key in sorted({r["case_id"] for r in records})
        },
        "semantic_metrics": "manual review required; no overall pass score",
    }


def compare(before: dict, after: dict) -> dict:
    if before["identity"] != after["identity"]:
        raise ValueError("Changed frozen suite/scorer")
    schedule = lambda report: [
        (r["case_id"], r["trial"], r["request_sha256"]) for r in report["records"]
    ]
    if schedule(before) != schedule(after):
        raise ValueError("Changed trial schedule or requests")
    if before["runtime"].get("model_digest") != after["runtime"].get("model_digest"):
        raise ValueError("Changed model identity")
    return {
        "identity": before["identity"],
        "baseline_sha": before["runtime"]["git_commit"],
        "treatment_sha": after["runtime"]["git_commit"],
        "baseline": aggregate(before["records"]),
        "treatment": aggregate(after["records"]),
        "semantic_comparison": "See separate unchanged-rubric manual review",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        choices=["preflight", "baseline", "context", "treatment"],
        required=True,
    )
    args = parser.parse_args()
    if os.getenv("RETRIEVAL_BACKEND", "legacy") != "legacy" or os.getenv(
        "RETRIEVAL_SHADOW_BACKEND"
    ):
        raise ValueError("Plan requires legacy without shadow")
    cases = load_cases()
    for case in cases:
        request_for(case)
    if args.phase == "preflight":
        print(
            json.dumps(
                {
                    "cases": len(cases),
                    "attempts": sum(c["trials"] for c in cases),
                    "identity": identity(),
                },
                indent=2,
            )
        )
        return
    if subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=ROOT, text=True
    ).strip():
        raise ValueError("Commit experiment before live run")
    report = {
        "identity": identity(),
        "runtime": collect_provenance().model_dump(mode="json"),
        "phase": args.phase,
        "started_utc": datetime.now(UTC).isoformat(),
        "records": [],
    }
    target = ROOT / f"evals/results/microsoft_reliability_{args.phase}.json"
    journal = target.with_suffix(".jsonl")
    if target.exists() or journal.exists():
        raise ValueError("Experiment already exists; no implicit reruns")
    if args.phase == "context":
        schedule = [
            (next(c for c in cases if c["case_id"] == key), ctx)
            for ctx in (4096, 8192)
            for key in ("REL-SOC-006", "REL-SOC-013", "REL-SOC-014")
        ]
    else:
        schedule = [(case, None) for case in cases for _ in range(case["trials"])]
    counts = Counter()
    for case, ctx in schedule:
        counts[case["case_id"]] += 1
        record = trial(case, counts[case["case_id"]], ctx)
        report["records"].append(record)
        with journal.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record) + "\n")
        print(
            f"{len(report['records'])}/{len(schedule)} {case['case_id']} {'returned' if record['result'] else 'withheld'}",
            flush=True,
        )
    report["finished_utc"] = datetime.now(UTC).isoformat()
    report["metrics"] = aggregate(report["records"])
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
