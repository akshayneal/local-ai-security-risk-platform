"""Run the same fixed retrieval cases against selected local candidates."""

import argparse
import hashlib
import json
import platform
import sqlite3
import statistics
import subprocess
import tempfile
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from pydantic import Field, model_validator

from app.retrieval.contracts import Contract, EvidenceRecord, RetrievalQuery
from app.retrieval.legacy import LegacyRetriever
from app.retrieval.lexical import LexicalRetriever
from app.retrieval.storage import canonical_json, fingerprint, write_snapshot
from evals.retrieval.metrics import policy_violations, ranking_metrics

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent


class RetrievalCase(Contract):
    case_id: str
    category: str
    query: RetrievalQuery
    relevance: dict[str, int] = Field(min_length=1)
    required: tuple[str, ...]
    forbidden: tuple[str, ...] = ()

    @model_validator(mode="after")
    def valid_judgments(self):
        if any(grade not in {1, 2, 3} for grade in self.relevance.values()):
            raise ValueError("relevance grades must be 1..3")
        if (
            set(self.required) - self.relevance.keys()
            or set(self.forbidden) & self.relevance.keys()
        ):
            raise ValueError("inconsistent judgments")
        return self


def load_suite(
    corpus_path: Path = FIXTURES / "corpus.json",
    cases_path: Path = FIXTURES / "cases.json",
):
    records = tuple(
        EvidenceRecord.model_validate(value)
        for value in json.loads(corpus_path.read_bytes())
    )
    cases = [
        RetrievalCase.model_validate(value)
        for value in json.loads(cases_path.read_bytes())
    ]
    ids = {r.evidence_id for r in records}
    if len(ids) != len(records) or len({c.case_id for c in cases}) != len(cases):
        raise ValueError("Duplicate corpus or case identities")
    from app.retrieval.filtering import eligible

    for case in cases:
        if (set(case.relevance) | set(case.forbidden)) - ids:
            raise ValueError(f"Unknown judgment ID: {case.case_id}")
        if any(
            not eligible(r, case.query)
            for r in records
            if r.evidence_id in case.relevance
        ):
            raise ValueError(f"Relevant judgment is ineligible: {case.case_id}")
    return records, cases


def aggregate(rows: list[dict]) -> dict:
    values = {
        key: statistics.mean(
            row["metrics"][key] for row in rows if row["metrics"][key] is not None
        )
        for key in ("recall_at_k", "required_recall_at_k", "mrr", "ndcg_at_k")
    }
    violations = Counter()
    for row in rows:
        violations.update(row["violations"])
    latency = sorted(row["latency_ms"] for row in rows)
    return {
        **values,
        "cases": len(rows),
        "violations": dict(violations),
        "latency_ms": {
            "mean": statistics.mean(latency),
            "median": statistics.median(latency),
            "p95": latency[max(0, (95 * len(latency) + 99) // 100 - 1)],
        },
    }


def run_benchmark(backends=("legacy", "lexical"), provider=None) -> dict:
    records, cases = load_suite()
    factories = {
        "legacy": lambda: LegacyRetriever(records),
        "lexical": lambda: LexicalRetriever(records),
    }
    if provider is not None:
        from app.retrieval.dense import DenseRetriever
        from app.retrieval.hybrid import HybridRetriever

        dense = None

        def make_dense():
            nonlocal dense
            if dense is None:
                dense = DenseRetriever(records, provider)
            return dense

        factories["dense"] = make_dense
        factories["hybrid"] = lambda: HybridRetriever(
            records, provider, dense=make_dense()
        )
    result = {
        "format": "retrieval-benchmark-v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "corpus_records": len(records),
        "synthetic_records": sum(r.synthetic for r in records),
        "chunk_records": sum(r.chunk_id is not None for r in records),
        "case_count": len(cases),
        "category_counts": dict(Counter(c.category for c in cases)),
        "corpus_sha256": fingerprint(records),
        "cases_sha256": fingerprint(cases),
        "fixture_bytes_sha256": {
            name: hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest()
            for name in ("corpus.json", "cases.json")
        },
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "sqlite": sqlite3.sqlite_version,
        },
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "git_dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ).strip()
        ),
        "source_sha256": {
            path.relative_to(ROOT).as_posix(): hashlib.sha256(
                path.read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            for folder in (ROOT / "app/retrieval", ROOT / "evals/retrieval")
            for path in sorted(folder.glob("*.py"))
        },
        "candidates": {},
    }
    with tempfile.TemporaryDirectory() as temporary:
        started = time.perf_counter()
        result["snapshot"] = write_snapshot(Path(temporary) / "evidence.db", records)
        result["snapshot"]["build_ms"] = (time.perf_counter() - started) * 1000
    for name in backends:
        if name not in factories:
            raise ValueError(
                f"Backend unavailable: {name}; supply a local embedding provider"
            )
        started = time.perf_counter()
        retriever = factories[name]()
        build_ms = (time.perf_counter() - started) * 1000
        rows = []
        provider_before = provider.provenance() if provider is not None else None
        for case in cases:
            started = time.perf_counter()
            hits = retriever.search(case.query)
            elapsed = (time.perf_counter() - started) * 1000
            returned = [hit.record.evidence_id for hit in hits]
            rows.append(
                {
                    "case_id": case.case_id,
                    "category": case.category,
                    "query": case.query,
                    "ranking": hits,
                    "latency_ms": elapsed,
                    "metrics": ranking_metrics(
                        returned, case.relevance, list(case.required), case.query.top_k
                    ),
                    "violations": policy_violations(
                        [hit.record for hit in hits], case.query, list(case.forbidden)
                    ),
                }
            )
        result["candidates"][name] = {
            "build_ms": build_ms,
            "summary": aggregate(rows),
            "by_category": {
                category: aggregate(
                    [row for row in rows if row["category"] == category]
                )
                for category in sorted({case.category for case in cases})
            },
            "results": rows,
        }
        if name in {"dense", "hybrid"}:
            result["candidates"][name]["embedding_before"] = provider_before
            result["candidates"][name]["embedding_after"] = provider.provenance()
            result["candidates"][name]["index_population"] = (
                "lazy; embedding time is included in query latency"
            )
    if provider is not None:
        result["embedding_provider"] = provider.provenance()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backends",
        nargs="+",
        choices=["legacy", "lexical", "dense", "hybrid"],
        default=["legacy", "lexical"],
    )
    parser.add_argument(
        "--output", type=Path, default=Path("evals/results/retrieval.json")
    )
    parser.add_argument("--model", default="embeddinggemma:300m")
    parser.add_argument(
        "--embedding-cache", type=Path, help="Offline replay of saved local vectors"
    )
    parser.add_argument(
        "--save-embedding-cache", type=Path, help="Persist vectors from this local run"
    )
    args = parser.parse_args()
    provider = None
    if set(args.backends) & {"dense", "hybrid"}:
        from app.retrieval.embeddings import (
            CachedEmbeddingProvider,
            OllamaEmbeddingProvider,
        )

        provider = (
            CachedEmbeddingProvider(args.embedding_cache)
            if args.embedding_cache
            else OllamaEmbeddingProvider(model=args.model)
        )
    result = run_benchmark(tuple(args.backends), provider)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        canonical_json(result) + "\n", encoding="utf-8", newline="\n"
    )
    if args.save_embedding_cache:
        if not isinstance(provider, OllamaEmbeddingProvider):
            parser.error(
                "--save-embedding-cache requires a live local dense/hybrid run"
            )
        provider.save_cache(args.save_embedding_cache)
    print(
        canonical_json(
            {
                name: candidate["summary"]
                for name, candidate in result["candidates"].items()
            }
        )
    )


if __name__ == "__main__":
    main()
