"""Frozen-plan fresh-query comparison with separate no-answer denominators."""

import argparse
import hashlib
import json
import platform
import statistics
import subprocess
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from pydantic import Field, model_validator

from app.retrieval.contracts import Contract, EvidenceRecord, RetrievalQuery
from app.retrieval.dense import DenseRetriever, document_text
from app.retrieval.embeddings import CachedEmbeddingProvider, OllamaEmbeddingProvider
from app.retrieval.filtering import eligible
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.legacy import LegacyRetriever
from app.retrieval.lexical import LexicalRetriever
from app.retrieval.storage import canonical_value, fingerprint
from evals.retrieval.metrics import policy_violations, ranking_metrics

ROOT = Path(__file__).resolve().parents[2]
SUITE = Path(__file__).parent


class Case(Contract):
    case_id: str
    category: str
    query: RetrievalQuery
    relevance: dict[str, int]
    required: tuple[str, ...]
    required_groups: tuple[tuple[str, ...], ...] = ()
    forbidden: tuple[str, ...]
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def judgments(self):
        if bool(self.relevance) == (self.category == "no_answer"):
            raise ValueError("Only no-answer cases have empty relevance")
        groups = {key for group in self.required_groups for key in group}
        if (set(self.required) | groups) - self.relevance.keys() or set(
            self.forbidden
        ) & self.relevance.keys():
            raise ValueError("Inconsistent required/forbidden judgments")
        if any(g not in {1, 2, 3} for g in self.relevance.values()) or any(
            not g for g in self.required_groups
        ):
            raise ValueError("Invalid relevance grade or required group")
        return self


def load_suite():
    records = tuple(
        EvidenceRecord.model_validate(r)
        for r in json.loads((SUITE / "corpus.json").read_bytes())
    )
    cases = [
        Case.model_validate(c) for c in json.loads((SUITE / "cases.json").read_bytes())
    ]
    by_id = {r.evidence_id: r for r in records}
    if len(by_id) != len(records) or len({c.case_id for c in cases}) != len(cases):
        raise ValueError("Duplicate suite identity")
    for case in cases:
        if (set(case.relevance) | set(case.forbidden)) - by_id.keys():
            raise ValueError("Unknown judgment identity")
        if any(not eligible(by_id[key], case.query) for key in case.relevance):
            raise ValueError("Ineligible relevant record")
    return records, cases


def suite_identity(records, cases) -> dict:
    return {
        "corpus_sha256": fingerprint(records),
        "cases_sha256": fingerprint(cases),
        "fixture_bytes_sha256": {
            n: hashlib.sha256((SUITE / n).read_bytes()).hexdigest()
            for n in ("corpus.json", "cases.json")
        },
    }


def score(hits, case: Case) -> dict:
    ids = [h.record.evidence_id for h in hits]
    metrics = ranking_metrics(
        ids, case.relevance, list(case.required), case.query.top_k
    )
    if case.category == "no_answer":
        metrics["mrr"] = None
        metrics["false_retrieval"] = bool(ids)
        metrics["correct_abstention"] = not ids
    else:
        metrics["required_group_recall"] = (
            sum(bool(set(group) & set(ids)) for group in case.required_groups)
            / len(case.required_groups)
            if case.required_groups
            else None
        )
    return metrics


def timings(values) -> dict:
    values = sorted(values)
    return {
        "median": statistics.median(values),
        "p95": values[max(0, (len(values) * 95 + 99) // 100 - 1)],
    }


def summarize(rows) -> dict:
    positive = [r for r in rows if r["category"] != "no_answer"]
    negative = [r for r in rows if r["category"] == "no_answer"]
    keys = (
        "recall_at_k",
        "required_recall_at_k",
        "required_group_recall",
        "mrr",
        "ndcg_at_k",
    )
    metrics = {}
    for key in keys:
        values = [
            r["metrics"][key] for r in positive if r["metrics"].get(key) is not None
        ]
        metrics[key] = {
            "mean": statistics.mean(values) if values else None,
            "cases": len(values),
        }
    violations = Counter()
    for row in rows:
        violations.update(row["violations"])
    return {
        "positive_cases": len(positive),
        "no_answer_cases": len(negative),
        "metrics": metrics,
        "false_retrieval_rate": statistics.mean(
            int(r["metrics"]["false_retrieval"]) for r in negative
        )
        if negative
        else None,
        "correct_abstention_count": sum(
            r["metrics"]["correct_abstention"] for r in negative
        ),
        "violations": dict(violations),
        "fresh_query_ms": timings([r["fresh_ms"] for r in rows]),
        "warm_query_ms": timings([r["warm_ms"] for r in rows]),
    }


def run(backends=("legacy", "lexical"), provider_factory=None) -> dict:
    records, cases = load_suite()
    report = {
        "format": "retrieval-benchmark-v2",
        "created_utc": datetime.now(UTC).isoformat(),
        **suite_identity(records, cases),
        "records": len(records),
        "cases": len(cases),
        "categories": dict(Counter(c.category for c in cases)),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "git_dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ).strip()
        ),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "source_sha256": {
            p.relative_to(ROOT).as_posix(): hashlib.sha256(
                p.read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            for folder in (ROOT / "app/retrieval", SUITE)
            for p in sorted(folder.glob("*.py"))
        },
        "candidates": {},
    }
    for name in backends:
        provider = None
        prep = {}
        if name in {"dense", "hybrid"}:
            if provider_factory is None:
                raise ValueError("Explicit local embedding provider required")
            provider = provider_factory(name)  # Independent caches for each candidate.
            texts = [
                document_text(r)
                for r in records
                if any(eligible(r, c.query) for c in cases)
            ]
            started = time.perf_counter()
            provider.embed_documents(texts[:1])
            prep["first_embedding_and_client_initialization_ms"] = (
                time.perf_counter() - started
            ) * 1000
            started = time.perf_counter()
            provider.embed_documents(texts)
            prep["remaining_document_preparation_ms"] = (
                time.perf_counter() - started
            ) * 1000
            prep["eligible_union_documents"] = len(texts)
            retriever = (
                DenseRetriever(records, provider)
                if name == "dense"
                else HybridRetriever(records, provider)
            )
        elif name == "legacy":
            retriever = LegacyRetriever(records)
        elif name == "lexical":
            retriever = LexicalRetriever(records)
        else:
            raise ValueError("Unknown candidate")
        rows = []
        for case in cases:
            started = time.perf_counter()
            hits = retriever.search(case.query)
            fresh_ms = (time.perf_counter() - started) * 1000
            started = time.perf_counter()
            warm = retriever.search(case.query)
            warm_ms = (time.perf_counter() - started) * 1000
            if hits != warm:
                raise ValueError("Fresh/warm rankings differ")
            rows.append(
                {
                    "case_id": case.case_id,
                    "category": case.category,
                    "ranking": canonical_value(hits),
                    "metrics": score(hits, case),
                    "violations": policy_violations(
                        [h.record for h in hits], case.query, list(case.forbidden)
                    ),
                    "fresh_ms": fresh_ms,
                    "warm_ms": warm_ms,
                }
            )
        candidate = {
            "preparation": prep,
            "results": rows,
            "summary": summarize(rows),
            "category_summary": {
                category: summarize([r for r in rows if r["category"] == category])
                for category in report["categories"]
            },
        }
        if provider is not None:
            candidate["provider"] = provider.provenance()
        report["candidates"][name] = candidate
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--vectors-dir", type=Path)
    args = parser.parse_args()
    backends = (
        ("legacy", "lexical", "dense", "hybrid")
        if args.live or args.vectors_dir
        else ("legacy", "lexical")
    )
    providers = {}

    def factory(name):
        provider = (
            CachedEmbeddingProvider(args.vectors_dir / f"{name}.json")
            if args.vectors_dir and not args.live
            else OllamaEmbeddingProvider()
        )
        providers[name] = provider
        return provider

    report = run(backends, factory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.live and args.vectors_dir:
        args.vectors_dir.mkdir(parents=True, exist_ok=True)
        for name, provider in providers.items():
            provider.save_cache(args.vectors_dir / f"{name}.json")
    args.output.write_text(
        json.dumps(canonical_value(report), indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
