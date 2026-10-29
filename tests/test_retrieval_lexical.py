"""SQLite ranking/storage and independent benchmark verification, offline."""

import json
import sqlite3
import subprocess
import sys
from contextlib import closing

import pytest
from test_retrieval_contracts import query, record

from app.retrieval.contracts import RetrievalError, Workflow
from app.retrieval.lexical import LexicalRetriever, lexical_tokens
from app.retrieval.storage import fingerprint, read_snapshot, write_snapshot
from evals.retrieval.metrics import policy_violations, ranking_metrics
from evals.retrieval.runner import aggregate, load_suite, run_benchmark


@pytest.mark.parametrize(
    "identifier",
    [
        "CVE-2099-41001",
        "203.0.113.42",
        "AC-7",
        "T1053.005",
        "powershell.exe",
        "SYN-POL-17",
        "203.0.113.42:8443",
    ],
)
def test_whole_identifier_and_ranking(identifier):
    exact = record(
        evidence_id="exact",
        source_id=identifier,
        title=identifier,
        content=f"Inspect {identifier}.",
    )
    near = record(
        evidence_id="near",
        title="General guidance",
        content=identifier[:-1] + "9 " + " ".join(lexical_tokens(identifier)[:2]),
    )
    hits = LexicalRetriever([near, exact]).search(query(text=identifier))
    assert hits[0].record.evidence_id == "exact"


def test_lexical_determinism_eligibility_and_literal_queries():
    retriever = LexicalRetriever(
        [
            record(
                evidence_id="restricted",
                required_scopes=["private"],
                content="isolation " * 100,
            ),
            record(evidence_id="wrong", workflows=[Workflow.AI_RISK]),
            record(evidence_id="stale", status="inactive"),
            record(),
        ]
    )
    assert [h.record.evidence_id for h in retriever.search(query())] == ["one"]
    assert retriever.search(query()) == retriever.search(query())
    assert retriever.search(query(text='" OR NOT * : ()')) == []
    assert retriever.search(query(text="☃")) == []


def test_forbidden_records_do_not_affect_bm25_statistics():
    alone = LexicalRetriever([record()]).search(query())
    with_forbidden = LexicalRetriever(
        [
            record(),
            record(
                evidence_id="no",
                required_scopes=["restricted"],
                content="approval " * 200,
            ),
        ]
    ).search(query())
    assert alone == with_forbidden


def test_fts_failure_is_predictable(monkeypatch):
    def unavailable(*args, **kwargs):
        raise sqlite3.OperationalError("no fts5")

    monkeypatch.setattr("app.retrieval.lexical.sqlite3.connect", unavailable)
    with pytest.raises(RetrievalError, match="FTS5"):
        LexicalRetriever([record()]).search(query())


def test_snapshot_roundtrip_integrity_and_file_handle_release(tmp_path):
    path = tmp_path / "index.db"
    records = [record(), record(evidence_id="two", required_scopes=["b", "a"])]
    manifest = write_snapshot(path, records)
    assert manifest["records"] == 2 and manifest["bytes"] > 0
    assert read_snapshot(path) == tuple(records)
    assert fingerprint(records) == manifest["corpus_sha256"]
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "UPDATE evidence SET payload=? WHERE ordinal=0",
            (records[0].model_copy(update={"title": "modified"}).model_dump_json(),),
        )
    with pytest.raises(RetrievalError, match="integrity"):
        read_snapshot(path)
    path.unlink()  # catches unclosed connections on Windows


@pytest.mark.parametrize("kind", ["missing", "corrupt", "empty", "bad-format"])
def test_index_failure_never_creates_or_falls_back(tmp_path, kind):
    path = tmp_path / "bad.db"
    if kind == "corrupt":
        path.write_text("not sqlite")
    if kind == "empty":
        path.touch()
    if kind == "bad-format":
        write_snapshot(path, [])
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("UPDATE manifest SET version='unknown'")
    with pytest.raises(RetrievalError):
        read_snapshot(path)
    if kind == "missing":
        assert not path.exists()


@pytest.mark.parametrize(
    ("returned", "expected"),
    [
        (["a", "b"], (1.0, 1.0)),
        (["x", "a"], (0.5, 0.5)),
        (["x"], (0.0, 0.0)),
        ([], (0.0, 0.0)),
    ],
)
def test_known_recall_mrr(returned, expected):
    metrics = ranking_metrics(returned, {"a": 2, "b": 1}, ["a"])
    assert (metrics["recall_at_k"], metrics["mrr"]) == expected


def test_ndcg_uses_k_not_number_returned():
    metrics = ranking_metrics(["a"], {"a": 2, "b": 2}, ["a"])
    assert 0 < metrics["ndcg_at_k"] < 1
    assert ranking_metrics(["a", "b"], {"a": 2, "b": 1}, ["a"])["ndcg_at_k"] == 1
    with pytest.raises(ValueError):
        ranking_metrics(["a", "a"], {"a": 1}, ["a"])
    assert ranking_metrics([], {}, [])["recall_at_k"] is None


def test_violation_scorer_is_not_vacuous():
    violations = policy_violations(
        [
            record(
                status="inactive",
                required_scopes=["private"],
                workflows=[Workflow.AI_RISK],
                authority="organizational_policy",
                policy_scope="wrong",
                effective_date="2027-01-01",
            )
        ],
        query(),
        ["one"],
    )
    assert violations == {
        "access": 1,
        "stale_version": 1,
        "workflow": 1,
        "authority_scope": 1,
        "applicability": 0,
        "validity": 1,
        "source_type": 0,
        "forbidden_judgment": 1,
    }


def test_fixed_suite_ground_truth_and_candidate_reproducibility():
    records, cases = load_suite()
    assert len(cases) == 48 and len(records) > 60
    assert {c.category for c in cases} == {
        "exact",
        "semantic",
        "workflow",
        "authority",
        "version",
        "access",
        "poison",
        "positive",
    }
    first = run_benchmark()
    second = run_benchmark()
    assert first["corpus_sha256"] == second["corpus_sha256"]
    assert first["cases_sha256"] == second["cases_sha256"]
    for name in ("legacy", "lexical"):
        for row, other in zip(
            first["candidates"][name]["results"],
            second["candidates"][name]["results"],
            strict=True,
        ):
            assert row["ranking"] == other["ranking"]
            assert row["metrics"] == other["metrics"]
            assert not any(row["violations"].values())
        assert aggregate(first["candidates"][name]["results"])["cases"] == 48


def test_canonical_hash_is_independent_of_process_hash_seed():
    code = "from app.retrieval.storage import fingerprint; print(fingerprint(frozenset(['a','b','c'])))"
    assert subprocess.check_output(
        [sys.executable, "-c", code], text=True
    ).strip() == fingerprint(frozenset(["c", "b", "a"]))


def test_cli_build_status(tmp_path):
    path = tmp_path / "index.db"
    for action in ("build", "status"):
        result = subprocess.check_output(
            [sys.executable, "-m", "app.retrieval.index", action, "--path", str(path)],
            text=True,
        )
        assert json.loads(result)["records"] > 0
