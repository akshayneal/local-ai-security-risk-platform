"""Explicit foreground experiments, preserving every attempt without live imports."""

import argparse
import json
import os
import subprocess
import time
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import requests

from evals.inference_lab_v1.transport import (
    CAPS,
    DIGEST,
    HOST,
    MODEL,
    SprintBudget,
    encoded,
    fingerprinted_session_class,
    provider_client,
    sha,
)

ROOT = Path(__file__).resolve().parents[2]
WORKSPACES = ROOT / "knowledge_base/workspaces"
ACCOUNTING = WORKSPACES / "cedar-sprint9-lab/accounting"
SOURCE_PATHS = (
    "app/ai_security_contracts.py",
    "app/ai_security_analyzer.py",
    "app/ollama_client.py",
    "app/inference_context.py",
    "app/prompts.py",
    "app/soc_analyzer.py",
    "app/governance_analyzer.py",
    "app/schemas.py",
    "app/evidence_ledger.py",
    "evals/inference_lab_v1/transport.py",
    "evals/inference_lab_v1/runner.py",
)


def read(path):
    return json.loads(path.read_bytes())


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def preflight():
    """Fixed loopback metadata only; no redirect, proxy, warm-up or download."""
    with requests.Session() as session:
        session.trust_env = False

        def get(path, payload=None):
            method = session.get if payload is None else session.post
            kwargs = {} if payload is None else {"json": payload}
            response = method(HOST + path, timeout=5, allow_redirects=False, **kwargs)
            if response.status_code != 200 or len(response.content) > 256_000:
                raise ValueError("Read-only provider preflight unavailable")
            return response.json()

        version, tags = get("/api/version"), get("/api/tags")
        if version.get("version") != "0.40.13":
            raise ValueError("Frozen installed runtime unavailable")
        model = next(
            (m for m in tags.get("models", []) if m.get("name") == MODEL), None
        )
        if not model or model.get("digest") != DIGEST:
            raise ValueError("Exact installed model unavailable")
        show = get("/api/show", {"model": MODEL})
        return {
            "version": version["version"],
            "model": MODEL,
            "digest": DIGEST,
            "capabilities": show.get("capabilities", []),
            "show_sha256": sha(encoded(show)),
            "thinking_supported": "thinking" in show.get("capabilities", []),
            "metadata_generation_attempts": 0,
        }


def verify_freeze():
    suite = ROOT / "evals/controlled_acceptance_v1"
    freeze = read(suite / "freeze.json")
    for name, digest in freeze["sha256"].items():
        literal = (ROOT / name).read_bytes()
        committed = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=ROOT)
        if sha(literal) != digest or sha(committed) != digest:
            raise ValueError("Sealed acceptance identity changed: " + name)
    return freeze


def write(budget, path, value):
    budget.store(path, encoded(value) + b"\n")


def execute(cases, budget, directory, variant):
    from app.evidence_ledger import evidence_ledger_mode
    from fastapi.testclient import TestClient

    from app import ai_security_api, main, ollama_client
    from app.ai_security_analyzer import candidate_protocol
    from app.inference_context import workflow_model_context
    from app.model_metrics import local_model_metrics
    from app.prompts import SYSTEM_PROMPT

    results = []

    def audit(**row):
        budget.event(
            event="audit",
            case_id=budget.case_id,
            mode=row["mode"],
            success=row["success"],
        )

    with ExitStack() as stack:
        stack.enter_context(
            patch.dict(
                os.environ,
                {
                    "RETRIEVAL_BACKEND": "legacy",
                    "RETRIEVAL_SHADOW_BACKEND": "",
                    "LOCAL_KNOWLEDGE_WORKSPACE": "",
                },
            )
        )
        stack.enter_context(patch.object(main, "write_audit_log", audit))
        stack.enter_context(patch.object(ai_security_api, "write_audit_log", audit))
        provider = provider_client(budget)
        stack.callback(provider._client.close)
        stack.enter_context(patch.object(ollama_client, "client", provider))
        stack.enter_context(patch.object(ollama_client, "OLLAMA_HOST", HOST))
        # Evaluation-only selection of the existing strict no-truncation route;
        # nested SOC context scopes cannot silently select its SDK alternative.
        stack.enter_context(
            patch.object(ollama_client, "complete_context_required", lambda: True)
        )
        stack.enter_context(
            patch.object(requests, "Session", fingerprinted_session_class(budget))
        )
        stack.enter_context(candidate_protocol(variant["protocol"] == "compact"))
        stack.enter_context(evidence_ledger_mode(variant["ledger"] == "on"))
        if variant["system"] == "global":
            stack.enter_context(workflow_model_context(SYSTEM_PROMPT))
        client = stack.enter_context(
            TestClient(ai_security_api.app, raise_server_exceptions=False)
        )
        source = {
            p: sha((ROOT / p).read_bytes()) for p in SOURCE_PATHS if (ROOT / p).exists()
        }
        for case in cases:
            if budget.blocked or budget.counts[budget.track] >= CAPS[budget.track]:
                results.append(
                    {
                        "id": case["id"],
                        "state": "NOT RUN",
                        "reason": "budget/unknown attempt",
                    }
                )
                continue
            budget.begin(
                budget.track,
                case["id"],
                directory,
                trial=directory.name,
                treatment=variant,
                input_sha256=sha(encoded(case["input"])),
                case_sha256=sha(encoded(case)),
                commit=git("rev-parse", "HEAD"),
                source_sha256=source,
            )
            first, started = budget.count, time.monotonic()
            budget.event(event="submitted", case_id=case["id"], track=budget.track)
            with local_model_metrics(num_ctx=8192) as metrics:
                response = client.post(case["endpoint"], json=case["input"])
            body = response.json()
            write(budget, directory / (case["id"] + ".json"), body)
            row = {
                "id": case["id"],
                "pillar": case["pillar"],
                "control": case["control"],
                "state": "RETURNED" if response.status_code == 200 else "WITHHELD",
                "http_status": response.status_code,
                "raw_attempts": budget.count - first,
                "wall_seconds": round(time.monotonic() - started, 6),
                "metrics": metrics.attempts,
                "author_fidelity_judgment": "PENDING",
                "supported_finding_flags": "PENDING",
                "unsupported_finding_flags": "PENDING",
                "output_sha256": sha(encoded(body) + b"\n"),
            }
            results.append(row)
            budget.event(event="submission_finished", **row)
            print(json.dumps(row), flush=True)
    return results


def run(
    *, track, trial, case_ids=(), protocol="compact", ledger="on", system="default"
):
    if (
        track not in CAPS
        or not trial
        or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in trial)
    ):
        raise ValueError("Invalid explicit trial")
    os.environ.update(
        PYTHON_DOTENV_DISABLED="1",
        PYTHONDONTWRITEBYTECODE="1",
        OLLAMA_HOST=HOST,
        OLLAMA_MODEL=MODEL,
    )
    verify_freeze()  # Both tracks require a committed sealed acceptance suite.
    suite = ROOT / (
        "evals/inference_lab_v1" if track == "lab" else "evals/controlled_acceptance_v1"
    )
    cases = read(suite / "cases.json")
    if track == "acceptance":
        if case_ids or protocol != "compact" or ledger != "on" or system != "default":
            raise ValueError("Acceptance variants and case selection forbidden")
        acceptance = WORKSPACES / "cedar-sprint9-acceptance"
        # A different run ID cannot bypass the one-run acceptance seal.
        if acceptance.exists():
            raise FileExistsError("Acceptance already attempted")
        if git("diff", "HEAD", "--", *SOURCE_PATHS):
            raise ValueError("Final implementation must be committed")
        directory = acceptance / trial
    else:
        directory = WORKSPACES / "cedar-sprint9-lab" / trial
        if case_ids:
            if not set(case_ids) <= {c["id"] for c in cases}:
                raise ValueError("Unknown development case")
            cases = [c for c in cases if c["id"] in case_ids]
    for path in (WORKSPACES, directory.parent, directory, ACCOUNTING):
        if path.is_symlink() or path.is_junction():
            raise ValueError("Linked output root refused")
    directory.mkdir(parents=True, exist_ok=False)
    budget = SprintBudget(ACCOUNTING)
    budget.track = track
    report = {
        "track": track,
        "trial": trial,
        "implementation_commit": git("rev-parse", "HEAD"),
        "scheduled": len(cases),
        "variant": {"protocol": protocol, "ledger": ledger, "system": system},
    }
    try:
        budget.event(event="trial_started", **report)
        try:
            report["provider"] = preflight()
        except (requests.RequestException, ValueError, KeyError):
            report.update(
                status="LIVE NOT RUN",
                results=[{"id": c["id"], "state": "NOT RUN"} for c in cases],
            )
        else:
            report.update(
                status="completed",
                results=execute(cases, budget, directory, report["variant"]),
            )
        report["global_raw_attempts"] = budget.count
        report["track_raw_attempts"] = budget.counts
        report["independent_review"] = "PENDING"
        write(budget, directory / "report.json", report)
        budget.event(
            event="trial_finished", track=track, trial=trial, raw_counts=budget.counts
        )
        return report
    except BaseException as exc:
        budget.event(
            event="trial_interrupted",
            exception_type=type(exc).__name__,
            pending=budget.pending,
        )
        raise
    finally:
        budget.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trial", required=True)
    parser.add_argument("--cases", nargs="*", default=[])
    parser.add_argument(
        "--protocol", choices=("baseline", "compact"), default="compact"
    )
    parser.add_argument("--ledger", choices=("on", "off"), default="on")
    parser.add_argument("--system", choices=("default", "global"), default="default")
    args = parser.parse_args()
    run(
        track="lab",
        trial=args.trial,
        case_ids=args.cases,
        protocol=args.protocol,
        ledger=args.ledger,
        system=args.system,
    )


if __name__ == "__main__":
    main()
