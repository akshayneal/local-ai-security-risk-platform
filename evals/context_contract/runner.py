"""Five predeclared direct-local-API probes; never retain generated content."""

import argparse
import hashlib
import json
import time
from pathlib import Path
from urllib.parse import urlsplit

import requests

from app.ollama_client import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TEMPERATURE
from app.prompts import SYSTEM_PROMPT, build_soc_prompt
from app.reference_loader import format_references_for_prompt, get_relevant_references
from app.schemas import SocAlertResponse
from evals.microsoft_reliability.cases import load_cases
from evals.microsoft_reliability.runner import ROOT, request_for, runtime_snapshot
from evals.provenance import collect_provenance

SUITE = Path(__file__).parent
USAGE = (
    "prompt_eval_count",
    "eval_count",
    "total_duration",
    "load_duration",
    "prompt_eval_duration",
    "eval_duration",
)
CAPACITY_MESSAGE = "the prompt is longer than the context length currently available to the model; shorten the prompt, adjust the context length in settings, or use a model with a longer context length"


def local_url() -> str:
    parsed = urlsplit(OLLAMA_HOST)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Context contract probes require a plain local Ollama host")
    return OLLAMA_HOST.rstrip("/")


def probe(spec: dict, session) -> dict:
    case = next(c for c in load_cases() if c["case_id"] == spec["case_id"])
    request = request_for(case)
    refs = get_relevant_references("soc_alert", request.model_dump_json(), 5)
    prompt = build_soc_prompt(request, format_references_for_prompt(refs))
    body = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "truncate": False,
        "shift": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "format": SocAlertResponse.model_json_schema(),
        "options": {
            "temperature": OLLAMA_TEMPERATURE,
            "num_ctx": spec["num_ctx"],
            "num_predict": spec["num_predict"],
        },
    }
    record = {
        "probe": spec,
        "user_utf8_bytes": len(prompt.encode()),
        "before_runtime": runtime_snapshot(),
    }
    started = time.perf_counter()
    try:
        response = session.post(local_url() + "/api/chat", json=body, timeout=300)
        data = response.json()
        record["http_status"] = response.status_code
        if response.ok:
            record["status"] = "response"
            record["done_reason"] = (
                data.get("done_reason")
                if data.get("done_reason") in {"stop", "length"}
                else "unknown"
            )
            record["usage"] = {
                k: data.get(k) if type(data.get(k)) is int and data[k] >= 0 else None
                for k in USAGE
            }
        else:
            record["status"] = (
                "input_capacity_rejection"
                if data.get("error") == CAPACITY_MESSAGE
                else "other_server_error"
            )
    except Exception:  # noqa: BLE001 -- fixed status only, no raw bodies/errors.
        record["status"] = "request_failed"
    record["elapsed_ms"] = (time.perf_counter() - started) * 1000
    record["after_runtime"] = runtime_snapshot()
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", required=True)
    parser.parse_args()
    target = ROOT / "evals/results/ollama_context_contract.json"
    if target.exists():
        raise ValueError("Contract experiment already exists; no implicit rerun")
    plan = json.loads((SUITE / "plan.json").read_bytes())
    report = {
        "plan": plan,
        "source_sha256": {
            n: hashlib.sha256((SUITE / n).read_bytes()).hexdigest()
            for n in ("plan.json", "runner.py")
        },
        "runtime": collect_provenance().model_dump(mode="json"),
        "records": [],
    }
    if report["runtime"]["git_dirty"]:
        raise ValueError("Commit capability experiment before live run")
    with requests.Session() as session:
        session.trust_env = False  # Local-only probes never use environment proxies.
        for spec in plan["probes"]:
            record = probe(spec, session)
            report["records"].append(record)
            print(spec["id"], record["status"], flush=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
