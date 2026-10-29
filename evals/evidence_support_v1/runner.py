"""Frozen ranking/assessment accounting; gold never reaches the application assessor."""

import argparse
import hashlib
import json
import statistics
import subprocess
import time
from pathlib import Path

from app.retrieval.contracts import (
    Authority,
    EvidenceRecord,
    RetrievalQuery,
    RetrievedEvidence,
)
from app.retrieval.dense import DenseRetriever
from app.retrieval.embeddings import OllamaEmbeddingProvider
from app.retrieval.filtering import eligible, filter_records
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.legacy import LegacyRetriever
from app.retrieval.lexical import LexicalRetriever
from evals.provenance import ROOT, collect_provenance

DIRECTORY = Path(__file__).resolve().parent


def load_suite():
    records = [
        EvidenceRecord.model_validate(r)
        for r in json.loads((DIRECTORY / "corpus.json").read_bytes())
    ]
    cases = json.loads((DIRECTORY / "cases.json").read_bytes())
    current = json.loads((DIRECTORY / "registry_current.json").read_bytes())

    def gate(record):
        return (
            record.document_id is None
            or current.get(record.document_id) == record.document_version_id
        )

    return records, cases, gate


def identity() -> dict:
    names = (
        "corpus.json",
        "cases.json",
        "registry_current.json",
        "plan.json",
        "methodology.md",
        "build_suite.py",
        "runner.py",
    )
    return {
        name: hashlib.sha256((DIRECTORY / name).read_bytes()).hexdigest()
        for name in names
    }


def validate_suite() -> None:
    records, cases, gate = load_suite()
    lookup = {r.evidence_id: r for r in records}
    assert len(lookup) == len(records) and len({c["case_id"] for c in cases}) == len(
        cases
    )
    for case in cases:
        query = RetrievalQuery.model_validate(case["query"])
        allowed = {r.evidence_id for r in filter_records(records, query, gate)}
        gold = case["gold"]
        assert set(gold["relevant_ids"]) <= allowed
        assert set(gold["conflict_ids"]) <= allowed
        for group in gold["required_evidence_groups"]:
            assert set(group) <= allowed
        if gold["relationship"] == "directly_supports":
            assert all(gold["required_evidence_groups"])


def ranking_metrics(case: dict, ids: list[str]) -> dict:
    found = set(ids)
    gold = case["gold"]
    relevant = set(gold["relevant_ids"])
    groups = [set(g) for g in gold["required_evidence_groups"] if g]
    return {
        "relevant_recall_at_k": len(found & relevant) / len(relevant)
        if relevant
        else None,
        "required_group_recall": sum(bool(found & group) for group in groups)
        / len(groups)
        if groups
        else None,
        "support_sufficient_at_k": all(
            bool(found & set(group)) for group in gold["required_evidence_groups"]
        )
        if gold["relationship"] == "directly_supports"
        else None,
    }


def rank(provider) -> dict:
    records, cases, gate = load_suite()
    dense = DenseRetriever(records, provider, gate)
    backends = {
        "legacy": LegacyRetriever(records, gate),
        "lexical": LexicalRetriever(records, gate),
        "dense": dense,
        "hybrid": HybridRetriever(records, provider, gate, dense=dense),
    }
    rows = []
    journal = ROOT / "evals/results/evidence_support_v1_rankings.jsonl"
    if journal.exists():
        raise ValueError("Existing ranking journal; no implicit restart")
    for case in cases:
        query = RetrievalQuery.model_validate(case["query"])
        for name, backend in backends.items():
            started = time.perf_counter()
            hits = backend.search(query)
            elapsed = (time.perf_counter() - started) * 1000
            ids = [h.record.evidence_id for h in hits]
            row = {
                "case_id": case["case_id"],
                "backend": name,
                "ranking": [
                    {
                        "evidence_id": h.record.evidence_id,
                        "score": h.score,
                        "rank": h.rank,
                    }
                    for h in hits
                ],
                "metrics": ranking_metrics(case, ids),
                "eligible_source_violations": [
                    h.record.evidence_id
                    for h in hits
                    if not eligible(h.record, query) or not gate(h.record)
                ],
                "latency_ms": elapsed,
            }
            rows.append(row)
            with journal.open("a", encoding="utf-8", newline="\n") as file:
                file.write(json.dumps(row) + "\n")
        print(f"{len(rows) // 4}/{len(cases)} ranking queries complete", flush=True)
    return {
        "identity": identity(),
        "runtime": collect_provenance().model_dump(mode="json"),
        "embedding": provider.provenance(),
        "records": rows,
    }


def assess_rankings(rankings: dict) -> dict:
    from app.support_assessor import assess_support
    from app.support_contracts import EvidenceClaim

    if rankings["identity"] != identity():
        raise ValueError("Changed frozen ranking identity")
    records, cases, gate = load_suite()
    lookup = {r.evidence_id: r for r in records}
    case_lookup = {c["case_id"]: c for c in cases}
    rows = []
    for row in rankings["records"]:
        case = case_lookup[row["case_id"]]
        query = RetrievalQuery.model_validate(case["query"])
        hits = [
            RetrievedEvidence(
                record=lookup[r["evidence_id"]],
                score=r["score"],
                rank=r["rank"],
                retriever=row["backend"],
            )
            for r in row["ranking"]
        ]
        started = time.perf_counter()
        assessment = assess_support(
            EvidenceClaim.model_validate(case["claim"]), query, hits, version_gate=gate
        )
        result = assessment.model_dump(mode="json")
        wrong_authority = (
            any(
                lookup[key].authority != Authority.POLICY
                for key in assessment.supporting_evidence_ids
            )
            if any(a["kind"] == "requirement" for a in case["claim"]["components"])
            and assessment.relationship == "directly_supports"
            else False
        )
        rows.append(
            {
                "case_id": case["case_id"],
                "backend": row["backend"],
                "assessment": result,
                "wrong_authority_support": wrong_authority,
                "assessment_ms": (time.perf_counter() - started) * 1000,
            }
        )
    return {
        "identity": identity(),
        "runtime": collect_provenance().model_dump(mode="json"),
        "records": rows,
        "summary": summarize(rankings, rows),
    }


def summarize(rankings: dict, assessed: list[dict]) -> dict:
    _, cases, _ = load_suite()
    lookup = {c["case_id"]: c for c in cases}
    output = {}
    for backend in ("legacy", "lexical", "dense", "hybrid"):
        ranked = [r for r in rankings["records"] if r["backend"] == backend]
        rows = [r for r in assessed if r["backend"] == backend]
        full = [
            r
            for r in rows
            if lookup[r["case_id"]]["gold"]["relationship"] == "directly_supports"
        ]
        nonfull = [r for r in rows if r not in full]
        noanswer = [
            r
            for r in rows
            if lookup[r["case_id"]]["gold"]["relationship"]
            in {"related_but_insufficient", "no_eligible_evidence"}
        ]
        metrics = {
            key: [r["metrics"][key] for r in ranked if r["metrics"][key] is not None]
            for key in (
                "relevant_recall_at_k",
                "required_group_recall",
                "support_sufficient_at_k",
            )
        }
        output[backend] = {
            "queries": len(rows),
            "ranking": {
                key: {"mean": statistics.mean(values), "denominator": len(values)}
                for key, values in metrics.items()
            },
            "false_support": {
                "count": sum(
                    r["assessment"]["relationship"] == "directly_supports"
                    for r in nonfull
                ),
                "denominator": len(nonfull),
            },
            "false_abstention_positive_loss": {
                "count": sum(
                    r["assessment"]["relationship"] != "directly_supports" for r in full
                ),
                "denominator": len(full),
            },
            "correct_no_answer": {
                "count": sum(
                    r["assessment"]["relationship"]
                    in {"related_but_insufficient", "no_eligible_evidence"}
                    for r in noanswer
                ),
                "denominator": len(noanswer),
            },
            "partial_handling": {
                "count": sum(
                    r["assessment"]["relationship"] == "partially_supports"
                    for r in rows
                    if lookup[r["case_id"]]["gold"]["relationship"]
                    == "partially_supports"
                ),
                "denominator": 3,
            },
            "conflict_handling": {
                "count": sum(
                    r["assessment"]["relationship"] == "conflicting"
                    for r in rows
                    if lookup[r["case_id"]]["gold"]["relationship"] == "conflicting"
                ),
                "denominator": 3,
            },
            "eligible_source_violations": sum(
                len(r["eligible_source_violations"]) for r in ranked
            ),
            "wrong_authority_support": sum(r["wrong_authority_support"] for r in rows),
            "naive_any_hit_false_support": {
                "count": sum(
                    bool(r["ranking"])
                    for r in ranked
                    if lookup[r["case_id"]]["gold"]["relationship"]
                    != "directly_supports"
                ),
                "denominator": len(nonfull),
                "scope": "Diagnostic heuristic, not actual production or generated hallucination count",
            },
            "ranking_ms_median": statistics.median(r["latency_ms"] for r in ranked),
            "assessment_ms_median": statistics.median(r["assessment_ms"] for r in rows),
        }
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase", required=True, choices=("preflight", "rank", "assess")
    )
    args = parser.parse_args()
    validate_suite()
    if identity() != json.loads((DIRECTORY / "freeze.json").read_bytes()):
        raise ValueError("Changed frozen benchmark")
    if args.phase == "preflight":
        print(json.dumps(identity(), indent=2))
        return
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("Commit before experiment")
    target = (
        ROOT
        / f"evals/results/evidence_support_v1_{'rankings' if args.phase == 'rank' else 'assessed'}.json"
    )
    if target.exists():
        raise ValueError("Experiment exists; no overwrite")
    if args.phase == "rank":
        provider = OllamaEmbeddingProvider()
        report = rank(provider)
        provider.save_cache(ROOT / "evals/results/evidence_support_v1_vectors.json")
    else:
        report = assess_rankings(
            json.loads(
                (ROOT / "evals/results/evidence_support_v1_rankings.json").read_bytes()
            )
        )
    target.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
