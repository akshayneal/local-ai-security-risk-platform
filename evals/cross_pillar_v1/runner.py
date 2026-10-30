"""One explicitly invoked foreground run. Tests exercise helpers, never live main."""

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import time
from contextlib import ExitStack
from datetime import date
from pathlib import Path
from unittest.mock import patch

import requests

from evals.cross_pillar_v1.transport import (
    HOST,
    Budget,
    CountedHttpx,
    counted_session_class,
    safe_bytes,
)

ROOT = Path(__file__).resolve().parents[2]
SUITE = Path(__file__).resolve().parent
RESULTS = ROOT / "evals/results/cross_pillar_v1"


def read(name):
    return json.loads((SUITE / name).read_bytes())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, value, budget=None):
    data = (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode()
    safe_bytes(data)
    if budget:
        budget.store(path, data)
        return
    with path.open("xb") as output:
        output.write(data)


def verify_freeze():
    freeze = read("freeze.json")
    for name, digest in freeze["sha256"].items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError("Frozen evaluation bytes changed: " + name)
    blobs = freeze["implementation_git_blobs"]
    actual = subprocess.check_output(
        ["git", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        text=True,
        input="\n".join(blobs) + "\n",
    ).splitlines()
    if dict(zip(blobs, actual, strict=True)) != blobs:
        raise ValueError("Frozen application implementation changed")
    return freeze


def preflight():
    with requests.Session() as session:
        session.trust_env = False
        version = session.get(HOST + "/api/version", timeout=5, allow_redirects=False)
        tags = session.get(HOST + "/api/tags", timeout=5, allow_redirects=False)
        if version.status_code != 200 or tags.status_code != 200:
            raise RuntimeError("Loopback provider unavailable")
        model = next(
            (m for m in tags.json().get("models", []) if m.get("name") == "qwen3:8b"),
            None,
        )
        plan = read("plan.json")
        if (
            not model
            or model.get("digest") != plan["model_digest"]
            or version.json().get("version") != plan["ollama_version"]
        ):
            raise RuntimeError("Frozen provider identity unavailable")
        return {"version": version.json()["version"], "model": model}


def create_workspace(directory):
    """Fresh experiment only. Copy pre-reviewed exact bytes; never approve a draft."""
    from app import knowledge_workspace as kw

    corpus = read("corpus.json")
    kw.initialize_workspace("sprint7-evaluation")
    workspace = kw.workspace_path("sprint7-evaluation")
    # initialize creates default empty operator config; only this fresh file is set.
    (workspace / "workspace.json").write_text(
        json.dumps(corpus["workspace"], indent=2), encoding="utf-8"
    )
    for item in corpus["documents"]:
        data = item["body"].encode()
        if sha(data) != item["review"]["content_hash"]:
            raise ValueError("Frozen document/version mismatch")
        with (workspace / "documents" / item["review"]["source_path"]).open(
            "xb"
        ) as out:
            out.write(data)
    write_new(
        workspace / "reviewed.json",
        {
            "format": "local-knowledge-reviews-v1",
            "documents": [d["review"] for d in corpus["documents"]],
        },
    )
    kw.register_workspace("sprint7-evaluation")
    loaded = kw.load_workspace("sprint7-evaluation")
    write_new(
        directory / "workspace_provenance.json",
        {
            "corpus_sha256": sha((SUITE / "corpus.json").read_bytes()),
            "records": [r.model_dump(mode="json") for r in loaded.records],
            "review_origin": "precommitted implementation-authored synthetic operator review",
        },
    )


def structural_checks(case, body):
    """Membership/identity only. Natural-language correctness needs separate review."""
    from app.ai_security_analyzer import validate_envelope_binding
    from app.ai_security_contracts import AiSecurityEnvelope, AiSecurityRequest
    from app.ui_schemas import GovernanceAnalysisEnvelope, SocAnalysisEnvelope

    pillar = case["pillar"]
    if pillar == "ai_security":
        envelope = AiSecurityEnvelope.model_validate(body)
        validate_envelope_binding(
            AiSecurityRequest.model_validate(case["input"]), envelope
        )
        selected = [s.provenance.evidence_id for s in envelope.metadata.sources]
        cited = [
            s.provenance.evidence_id
            for s in envelope.metadata.sources
            if s.cited_by_finding_ids
        ]
        identity = envelope.analysis.application_id == case["input"]["application_id"]
        provenance = all(
            s.version == "local-ai-security-guidance-v1"
            and s.provenance.authority == "local_reference_guidance"
            for s in envelope.metadata.sources
        )
        coverage = None
    else:
        model = SocAnalysisEnvelope if pillar == "soc" else GovernanceAnalysisEnvelope
        envelope = model.model_validate(body)
        inspector = envelope.metadata.evidence_inspector
        selected = [s.provenance.source_id for s in inspector.sources]
        cited = [s.source_id for s in envelope.analysis.source_references]
        field = "alert_id" if pillar == "soc" else "system_name"
        identity = getattr(envelope.analysis, field) == case["input"][field]
        corpus = {
            d["review"]["document_version_id"]: d["review"]
            for d in read("corpus.json")["documents"]
        }
        local = [
            s.provenance for s in inspector.sources if s.provenance.document_version_id
        ]
        provenance = all(
            p.document_version_id in corpus
            and p.authority == corpus[p.document_version_id]["metadata"]["authority"]
            and p.registry_check == "passed"
            and p.version_status == "current"
            for p in local
        )
        coverage = (
            inspector.local_knowledge.model_dump(mode="json")
            if inspector.local_knowledge
            else None
        )
    return {
        "schema_valid": True,
        "immutable_identifier": identity,
        "cited_source_membership": set(cited) <= set(selected),
        "source_version_authority_preserved": provenance,
        "selected_ids": selected,
        "cited_ids": cited,
        "selected_not_cited": sorted(set(selected) - set(cited)),
        "knowledge_coverage": coverage,
        "semantic_support": "unassessed; independent human adjudication pending",
    }


def execute(directory, budget):
    from fastapi.testclient import TestClient
    from ollama import Client

    from app import ai_security_api as api
    from app import knowledge_workspace as kw
    from app import main
    from app import ollama_client as provider
    from app.model_metrics import local_model_metrics

    frozen_query = kw.workspace_query

    def dated_query(*args, **kwargs):
        kwargs["as_of"] = date(2026, 10, 30)
        return frozen_query(*args, **kwargs)

    def audit(**row):
        budget.event(
            event="audit",
            case_id=budget.case_id,
            mode=row["mode"],
            success=row["success"],
        )

    results = []
    with ExitStack() as stack:
        # Only fresh experiment state and transport/audit/config seams are injected.
        stack.enter_context(
            patch.object(kw, "WORKSPACE_ROOT", directory / "workspaces")
        )
        stack.enter_context(patch.object(kw, "workspace_query", dated_query))
        stack.enter_context(
            patch.dict(
                os.environ,
                {
                    "LOCAL_KNOWLEDGE_WORKSPACE": "sprint7-evaluation",
                    "RETRIEVAL_BACKEND": "legacy",
                    "RETRIEVAL_SHADOW_BACKEND": "",
                },
            )
        )
        stack.enter_context(patch.object(main, "write_audit_log", audit))
        stack.enter_context(patch.object(api, "write_audit_log", audit))
        counted_client = Client(
            host=HOST,
            transport=CountedHttpx(budget),
            timeout=180,
            trust_env=False,
            follow_redirects=False,
        )
        stack.callback(counted_client._client.close)
        stack.enter_context(patch.object(provider, "client", counted_client))
        stack.enter_context(patch.object(provider, "OLLAMA_HOST", HOST))
        stack.enter_context(
            patch.object(requests, "Session", counted_session_class(budget))
        )
        create_workspace(directory)
        client = stack.enter_context(TestClient(api.app, raise_server_exceptions=False))
        for case in read("cases.json"):
            budget.remaining()
            budget.case_id = case["id"]
            budget.event(
                event="case_started",
                case_id=case["id"],
                input_sha256=sha(json.dumps(case["input"], sort_keys=True).encode()),
            )
            first = budget.count
            started = time.monotonic()
            with local_model_metrics(num_ctx=8192) as metrics:
                response = client.post(case["endpoint"], json=case["input"])
            wall = time.monotonic() - started
            body = response.json()
            write_new(directory / (case["id"] + ".json"), body, budget)
            checks = (
                structural_checks(case, body) if response.status_code == 200 else None
            )
            result = {
                "case_id": case["id"],
                "pillar": case["pillar"],
                "http_status": response.status_code,
                "returned": response.status_code == 200,
                "withheld": response.status_code != 200,
                "context_rejected": isinstance(body.get("detail"), dict)
                and body["detail"].get("code") == "complete_context_unavailable",
                "raw_provider_attempts": budget.count - first,
                "wall_seconds": round(wall, 6),
                "metrics": metrics.attempts,
                "output_sha256": sha((directory / (case["id"] + ".json")).read_bytes()),
                "checks": checks,
            }
            results.append(result)
            budget.event(event="case_finished", **result)
            print(
                json.dumps(
                    {
                        k: result[k]
                        for k in (
                            "case_id",
                            "http_status",
                            "raw_provider_attempts",
                            "wall_seconds",
                        )
                    }
                ),
                flush=True,
            )
        budget.case_id = None
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"sprint7-baseline-[0-9]{3}", args.run_id):
        parser.error("Use a bounded explicit baseline attempt ID")
    # Disable dotenv before importing any application module; no private config read.
    os.environ.update(
        PYTHON_DOTENV_DISABLED="1", OLLAMA_HOST=HOST, OLLAMA_MODEL="qwen3:8b"
    )
    freeze = verify_freeze()
    directory = RESULTS / args.run_id
    for path in (RESULTS.parent, RESULTS, directory):
        if path.is_symlink() or path.is_junction():
            raise ValueError("Linked result paths refused")
    directory.mkdir(parents=True, exist_ok=False)
    budget = Budget(directory)
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    provenance = {
        "git_commit": head,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "freeze": freeze,
        "scheduled_submissions": 12,
        "raw_attempt_cap": 32,
        "qualitative_review": "implementation-authored; independent adjudication pending",
    }
    try:
        budget.event(event="run_started", git_commit=head, scheduled_submissions=12)
        try:
            provenance["provider"] = preflight()
        except (requests.RequestException, ValueError, RuntimeError, StopIteration):
            provenance.update(
                status="LIVE INFERENCE NOT RUN", results=[], raw_provider_attempts=0
            )
        else:
            provenance["results"] = execute(directory, budget)
            provenance.update(status="completed", raw_provider_attempts=budget.count)
        write_new(directory / "report.json", provenance, budget)
        budget.event(
            event="run_finished",
            status=provenance["status"],
            raw_provider_attempts=budget.count,
            completed_submissions=len(provenance["results"]),
        )
    except BaseException as exc:
        budget.event(
            event="run_interrupted",
            raw_provider_attempts=budget.count,
            exception_type=type(exc).__name__,
        )
        raise
    finally:
        budget.close()


if __name__ == "__main__":
    main()
