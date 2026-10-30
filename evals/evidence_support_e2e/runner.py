"""Once-only local UI-route diagnostic; no new server or raw rejected output."""

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from app import main
from app.model_metrics import local_model_metrics
from app.schemas import GovernanceRiskRequest
from app.soc_inputs import MicrosoftSocAdapter
from evals.provenance import ROOT, collect_provenance

DIRECTORY = Path(__file__).resolve().parent


def cases():
    return json.loads((DIRECTORY / "cases.json").read_bytes())


def request_for(case):
    return (
        MicrosoftSocAdapter().normalize(case["bundle"]).request
        if case["workflow"] == "soc_alert"
        else GovernanceRiskRequest(**case["request"])
    )


def identity():
    return {
        name: hashlib.sha256((DIRECTORY / name).read_bytes()).hexdigest()
        for name in ("cases.json", "rubric.md", "plan.json", "runner.py")
    }


def trial(case):
    request = request_for(case)
    audits = []
    started = time.perf_counter()
    with (
        local_model_metrics() as metrics,
        patch.object(
            main,
            "write_audit_log",
            lambda **kw: audits.append(
                {"success": kw["success"], "source_ids": kw.get("source_ids", [])}
            ),
        ),
    ):
        try:
            response = (
                main.ui_soc_endpoint
                if case["workflow"] == "soc_alert"
                else main.ui_governance_endpoint
            )(request)
            body = response.model_dump(mode="json")
            inspector = body["metadata"]["evidence_inspector"]
            ids = {s["provenance"]["evidence_id"] for s in inspector["sources"]}
            key = "alert_id" if case["workflow"] == "soc_alert" else "system_name"
            checks = {
                "case_identity_exact": body["analysis"][key] == getattr(request, key),
                "cited_sources_captured": {
                    s["source_id"] for s in body["analysis"]["source_references"]
                }
                <= ids,
                "model_claims_unassessed": all(
                    c["assessment"]["relationship"] == "unassessed"
                    and c["assessment"]["verification_status"] == "not_verified"
                    and c["assessment"]["provenance"] == "model_proposed"
                    for c in inspector["claims"]
                ),
                "one_audit": len(audits) == 1,
                "retrieval_captured": inspector["retrieval_status"] == "captured",
            }
            error = None
        except HTTPException as exc:
            body, checks = None, None
            code = exc.detail.get("code") if isinstance(exc.detail, dict) else None
            error = (
                code
                if code
                in {"integrity_validation_failed", "complete_context_unavailable"}
                else "analysis_failed"
            )
        except Exception:  # noqa: BLE001 -- retain the attempt, never raw payloads/errors.
            body, checks, error = None, None, "analysis_failed"
    return {
        "case_id": case["case_id"],
        "request_sha256": hashlib.sha256(
            request.model_dump_json().encode()
        ).hexdigest(),
        "response": body,
        "error": error,
        "checks": checks,
        "audit_outcomes": audits,
        "model_attempts": metrics.attempts,
        "latency_ms": (time.perf_counter() - started) * 1000,
    }


def run():
    if identity() != json.loads((DIRECTORY / "freeze.json").read_bytes()):
        raise ValueError("Changed frozen live diagnostic")
    if os.getenv("RETRIEVAL_BACKEND", "legacy") != "legacy" or os.getenv(
        "RETRIEVAL_SHADOW_BACKEND"
    ):
        raise ValueError("Plan requires legacy without shadow")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("Commit before live diagnostic")
    target = ROOT / "evals/results/evidence_support_e2e.json"
    journal = target.with_suffix(".jsonl")
    if target.exists() or journal.exists():
        raise ValueError("Existing experiment; no overwrite/rerun")
    report = {
        "identity": identity(),
        "runtime": collect_provenance().model_dump(mode="json"),
        "records": [],
    }
    for case in cases():
        row = trial(case)
        report["records"].append(row)
        with journal.open("a", encoding="utf-8", newline="\n") as file:
            file.write(json.dumps(row) + "\n")
        print(
            f"{len(report['records'])}/8 {case['case_id']} {'returned' if row['response'] else 'withheld'}",
            flush=True,
        )
    target.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    run()
