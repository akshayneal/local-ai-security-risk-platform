"""Offline authored-case evaluation; no model, embedding, server or network calls."""

import argparse
import hashlib
import json
import platform
import sqlite3
import subprocess
import tempfile
import time
from datetime import date
from pathlib import Path
from unittest.mock import patch

from app import knowledge_workspace as kw
from app.retrieval.contracts import RetrievalError, Workflow

ROOT = Path(__file__).resolve().parents[2]
SUITE = Path(__file__).resolve().parent


def verify_freeze() -> dict:
    freeze = json.loads((SUITE / "freeze.json").read_bytes())
    for name, expected in freeze["sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Frozen source/plan mismatch")
    implementation = json.loads((SUITE / "implementation_freeze.json").read_bytes())
    names = implementation["source_git_blobs"]
    actual = subprocess.check_output(
        ["git", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        text=True,
        input="\n".join(names) + "\n",
    ).splitlines()
    if dict(zip(names, actual, strict=True)) != names:
        raise ValueError("Pre-outcome implementation snapshot mismatch")
    freeze["implementation_source_git_blobs"] = names
    return freeze


def _condition(path: Path, case: dict) -> None:
    if change := case.get("mutate"):
        reviews = json.loads((path / "reviewed.json").read_bytes())
        row = next(
            r for r in reviews["documents"] if r["source_path"] == change["file"]
        )
        row.update({k: v for k, v in change.items() if k not in {"file", "metadata"}})
        row["metadata"].update(change.get("metadata", {}))
        (path / "reviewed.json").write_text(json.dumps(reviews), encoding="utf-8")
    if case.get("operation") == "change-file":
        (path / "documents/access-policy.md").write_text(
            "Unreviewed replacement", encoding="utf-8"
        )
    elif case.get("operation") == "remove-registry-entry":
        with sqlite3.connect(path / "registry.db") as connection:
            connection.execute(
                "DELETE FROM documents WHERE source_path='access-policy.md'"
            )


def evaluate() -> dict:
    freeze = verify_freeze()
    cases = json.loads((SUITE / "cases.json").read_bytes())
    results = []
    for case in cases:
        started = time.perf_counter()
        with (
            tempfile.TemporaryDirectory(prefix="knowledge-bridge-v1-") as temporary,
            patch.object(kw, "WORKSPACE_ROOT", Path(temporary) / "workspaces"),
        ):
            kw.initialize_workspace("case", demo=True)
            kw.register_workspace("case")
            path = kw.workspace_path("case")
            _condition(path, case)
            try:
                workspace = kw.load_workspace("case")
                query = kw.workspace_query(
                    workspace,
                    Workflow(case.get("case_workflow", case["workflow"])),
                    case["query"],
                    top_k=8,
                    as_of=date(2026, 10, 30),
                )
                hits, coverage, _ = kw.select_knowledge(workspace, query)
                selected = {h.record.source_path for h in hits}
                found = len(set(case["targets"]) & selected)
                forbidden = len(set(case.get("forbidden", [])) & selected)
                groups = case.get("groups", [])
                assertion_ok = coverage.support_status == "unassessed"
                if case.get("assertion") in {
                    "unverified-authority",
                    "body-cannot-grant-scopes",
                }:
                    assertion_ok &= all(
                        h.record.authority == "unverified_material"
                        and h.record.required_scopes == {"northstar.learning"}
                        for h in hits
                        if h.record.source_path == "poison.md"
                    )
                results.append(
                    {
                        "id": case["id"],
                        "safe_error": False,
                        "passed": not case.get("error")
                        and not forbidden
                        and found == len(case["targets"])
                        and assertion_ok,
                        "relevant_found": found,
                        "relevant_total": len(case["targets"]),
                        "required_groups_found": sum(
                            bool(set(g) & selected) for g in groups
                        ),
                        "required_groups_total": len(groups),
                        "false_eligible_exposures": forbidden,
                        "no_answer": case.get("no_answer", False),
                        "nonempty_retrieval": bool(hits),
                        "support_unassessed": assertion_ok,
                        "selected_ids": [h.record.evidence_id for h in hits],
                        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                    }
                )
            except RetrievalError:
                results.append(
                    {
                        "id": case["id"],
                        "safe_error": True,
                        "passed": bool(case.get("error")),
                        "relevant_found": 0,
                        "relevant_total": len(case["targets"]),
                        "required_groups_found": 0,
                        "required_groups_total": len(case.get("groups", [])),
                        "false_eligible_exposures": 0,
                        "no_answer": case.get("no_answer", False),
                        "nonempty_retrieval": False,
                        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                    }
                )
    positive = [r for r in results if r.get("relevant_total", 0)]
    negative = [r for r in results if r.get("no_answer")]
    found = sum(r["relevant_found"] for r in positive)
    total = sum(r["relevant_total"] for r in positive)
    return {
        "format": "knowledge-bridge-results-v1",
        "judgments": "synthetic implementation-authored; not independently adjudicated",
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "freeze": freeze,
        "cases": len(results),
        "passed": sum(r["passed"] for r in results),
        "metrics": {
            "relevant_recall_at_8": {
                "found": found,
                "total": total,
                "positive_cases": len(positive),
                "ratio": found / total if total else None,
            },
            "required_group_coverage": {
                "found": sum(r.get("required_groups_found", 0) for r in results),
                "total": sum(r.get("required_groups_total", 0) for r in results),
            },
            "false_eligible_exposure": {
                "count": sum(r.get("false_eligible_exposures", 0) for r in results),
                "negative_cases": sum(bool(c.get("forbidden")) for c in cases),
            },
            "no_answer_nonempty_retrieval": {
                "count": sum(r["nonempty_retrieval"] for r in negative),
                "total": len(negative),
            },
            "positive_retrieval_loss": {"count": total - found, "total": total},
            "support_status_consistency": {
                "unassessed": sum(r.get("support_unassessed", False) for r in results),
                "returned_cases": sum(not r["safe_error"] for r in results),
            },
            "expected_safe_refusals": {
                "count": sum(r["safe_error"] and r["passed"] for r in results),
                "total": sum(bool(c.get("error")) for c in cases),
            },
            "unsupported_generation_tendency": "NOT MEASURED: no real generation",
            "positive_generation_loss": "NOT MEASURED: no real generation",
            "model_requests": 0,
            "embedding_requests": 0,
            "network_requests": 0,
        },
        "results": results,
        "limits": "Bounded synthetic retrieval and software checks only; no entailment certificate, deployment approval, causal model comparison or reliability estimate.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(
            "Output exists; preserve it and choose a new path for explicit replay"
        )
    report = evaluate()
    with args.output.open("x", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "cases": report["cases"],
                "passed": report["passed"],
                "metrics": report["metrics"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
