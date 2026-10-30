"""One explicit foreground run; actual app inference, isolated audit, never resume."""

import hashlib
import json
import os
import subprocess
import time
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import requests

from evals.cross_pillar_v1.transport import HOST, CountedHttpx, counted_session_class
from evals.reliability_v1.transport import MAX_CALLS, SixAttemptBudget

ROOT = Path(__file__).resolve().parents[2]
SUITE = Path(__file__).resolve().parent
RESULTS = ROOT / "knowledge_base/workspaces/maple-sprint8-live/sprint8-primary-001"


def read(name: str):
    return json.loads((SUITE / name).read_bytes())


def verify_freeze() -> dict:
    freeze = read("freeze.json")
    for name, digest in freeze["sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Frozen prospective suite changed: " + name)
    return freeze


def store(budget, name: str, value) -> None:
    budget.store(budget.directory / name, (json.dumps(value, indent=2) + "\n").encode())


def preflight() -> dict:
    with requests.Session() as session:
        session.trust_env = False
        version = session.get(HOST + "/api/version", timeout=5, allow_redirects=False)
        tags = session.get(HOST + "/api/tags", timeout=5, allow_redirects=False)
        version.raise_for_status()
        tags.raise_for_status()
        model = next(
            (m for m in tags.json().get("models", []) if m.get("name") == "qwen3:8b"),
            None,
        )
        if not model or model.get("digest") != read("plan.json")["model_digest"]:
            raise ValueError("Exact installed model unavailable")
        return {"version": version.json()["version"], "model": model}


def execute(budget) -> list[dict]:
    from fastapi.testclient import TestClient
    from ollama import Client

    from app import ai_security_api, main, ollama_client
    from app.model_metrics import local_model_metrics

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
        provider = Client(
            host=HOST,
            transport=CountedHttpx(budget),
            timeout=180,
            trust_env=False,
            follow_redirects=False,
        )
        stack.callback(provider._client.close)
        stack.enter_context(patch.object(ollama_client, "client", provider))
        stack.enter_context(patch.object(ollama_client, "OLLAMA_HOST", HOST))
        stack.enter_context(
            patch.object(requests, "Session", counted_session_class(budget))
        )
        client = stack.enter_context(
            TestClient(ai_security_api.app, raise_server_exceptions=False)
        )
        for case in read("cases.json"):
            if budget.count >= MAX_CALLS or budget.clock() - budget.started >= 1500:
                results.append(
                    {
                        "id": case["id"],
                        "state": "NOT RUN",
                        "reason": "global budget/deadline",
                    }
                )
                continue
            budget.case_id = case["id"]
            budget.event(event="submitted", case_id=case["id"])
            first, started = budget.count, time.monotonic()
            with local_model_metrics(num_ctx=8192) as metrics:
                response = client.post(case["endpoint"], json=case["input"])
            try:
                body = response.json()
            except ValueError:
                body = {"detail": "non_json_application_error"}
            store(budget, case["id"] + ".json", body)
            item = {
                "id": case["id"],
                "state": "RETURNED" if response.status_code == 200 else "WITHHELD",
                "http_status": response.status_code,
                "raw_attempts": budget.count - first,
                "wall_seconds": round(time.monotonic() - started, 6),
                "metrics": metrics.attempts,
            }
            results.append(item)
            budget.event(event="submission_finished", **item)
            print(json.dumps(item), flush=True)
    return results


def main() -> None:
    # Set these before any application import; don't read private .env config.
    os.environ.update(
        PYTHON_DOTENV_DISABLED="1", OLLAMA_HOST=HOST, OLLAMA_MODEL="qwen3:8b"
    )
    freeze = verify_freeze()
    for path in (RESULTS.parent.parent, RESULTS.parent, RESULTS):
        if path.is_symlink() or path.is_junction():
            raise ValueError("Linked output root refused")
    RESULTS.mkdir(parents=True, exist_ok=False)
    budget = SixAttemptBudget(RESULTS)
    report = {
        "freeze": freeze,
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "scheduled": 6,
        "runtime": read("plan.json")["runtime"],
        "source_git_blobs": {
            p: subprocess.check_output(
                ["git", "hash-object", p], cwd=ROOT, text=True
            ).strip()
            for p in read("plan.json")["implementation_paths"]
        },
    }
    try:
        budget.event(event="run_started", git_commit=report["git_commit"])
        try:
            report["provider"] = preflight()
        except (requests.RequestException, ValueError, KeyError):
            report.update(
                status="LIVE NOT RUN",
                results=[
                    {"id": c["id"], "state": "NOT RUN"} for c in read("cases.json")
                ],
            )
        else:
            report.update(status="completed", results=execute(budget))
        report["raw_attempts"] = budget.count
        store(budget, "report.json", report)
        budget.event(
            event="run_finished", status=report["status"], raw_attempts=budget.count
        )
    except BaseException as exc:
        budget.event(
            event="interrupted",
            exception_type=type(exc).__name__,
            raw_attempts=budget.count,
        )
        raise
    finally:
        budget.close()


if __name__ == "__main__":
    main()
