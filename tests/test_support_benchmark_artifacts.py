import hashlib
import json
import subprocess

from app.retrieval.contracts import RetrievalQuery
from app.retrieval.dense import DenseRetriever, document_text
from app.retrieval.embeddings import CachedEmbeddingProvider, text_key
from app.retrieval.filtering import eligible
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.legacy import LegacyRetriever
from app.retrieval.lexical import LexicalRetriever
from app.support_assessor import assess_support
from app.support_contracts import EvidenceClaim
from evals.evidence_support_v1.runner import (
    identity,
    load_suite,
    ranking_metrics,
    summarize,
)
from evals.provenance import ROOT

FOLDER = ROOT / "Documentation/evidence_support_v1"


def test_exact_ranking_artifact_and_four_backend_cached_replay():
    report = json.loads((FOLDER / "rankings.json").read_bytes())
    provenance = json.loads((FOLDER / "ranking_provenance.json").read_bytes())
    assert (
        hashlib.sha256((FOLDER / "rankings.json").read_bytes()).hexdigest()
        == provenance["ranking_sha256"]
    )
    assert (
        hashlib.sha256((FOLDER / "vectors.json").read_bytes()).hexdigest()
        == provenance["vectors_sha256"]
    )
    assert report["identity"] == identity()
    assert not report["runtime"]["git_dirty"]
    assert len(report["records"]) == 172
    records, cases, gate = load_suite()
    provider = CachedEmbeddingProvider(FOLDER / "vectors.json")
    dense = DenseRetriever(records, provider, gate)
    backends = {
        "legacy": LegacyRetriever(records, gate),
        "lexical": LexicalRetriever(records, gate),
        "dense": dense,
        "hybrid": HybridRetriever(records, provider, gate, dense=dense),
    }
    actual = {(r["case_id"], r["backend"]): r for r in report["records"]}
    for case in cases:
        query = RetrievalQuery.model_validate(case["query"])
        for name, backend in backends.items():
            hits = backend.search(query)
            ids = [h.record.evidence_id for h in hits]
            original = actual[case["case_id"], name]
            assert ids == [h["evidence_id"] for h in original["ranking"]]
            assert all(eligible(h.record, query) and gate(h.record) for h in hits)
            assert ranking_metrics(case, ids) == original["metrics"]
    cache = json.loads((FOLDER / "vectors.json").read_bytes())["vectors"]
    # These sources are never eligible for any trusted fixture query, so they must
    # not have reached even the local embedding provider during the campaign.
    for record in records:
        if record.evidence_id in {
            "RESTRICTED-0",
            "RESTRICTED-1",
            "OLD-0",
            "OLD-1",
            "OLD-2",
            "DATE-DECOY-0",
            "DATE-DECOY-1",
        } or record.evidence_id.startswith("WRONG-SCOPE"):
            assert text_key(document_text(record)) not in cache


def test_assessment_artifact_exact_replay_without_model_or_gold_in_candidate():
    from app.retrieval.contracts import RetrievedEvidence

    ranked = json.loads((FOLDER / "rankings.json").read_bytes())
    assessed = json.loads((FOLDER / "assessed.json").read_bytes())
    manifest = json.loads((FOLDER / "assessment_provenance.json").read_bytes())
    for name, expected in manifest["artifact_sha256"].items():
        assert hashlib.sha256((FOLDER / name).read_bytes()).hexdigest() == expected
    for name, expected in manifest["candidate_source_blobs"].items():
        assert subprocess.check_output(
            ["git", "hash-object", f"--path={name}", name], cwd=ROOT, text=True
        ).strip() == expected
    records, cases, gate = load_suite()
    lookup = {r.evidence_id: r for r in records}
    case_lookup = {c["case_id"]: c for c in cases}
    for ranking, row in zip(ranked["records"], assessed["records"], strict=True):
        case = case_lookup[row["case_id"]]
        hits = [
            RetrievedEvidence(
                record=lookup[h["evidence_id"]],
                rank=h["rank"],
                score=h["score"],
                retriever=row["backend"],
            )
            for h in ranking["ranking"]
        ]
        replay = assess_support(
            EvidenceClaim.model_validate(case["claim"]),
            RetrievalQuery.model_validate(case["query"]),
            hits,
            version_gate=gate,
        )
        assert replay.model_dump(mode="json") == row["assessment"]
    assert summarize(ranked, assessed["records"]) == assessed["summary"]
    for values in assessed["summary"].values():
        assert values["false_support"] == {"count": 0, "denominator": 25}
        assert values["false_abstention_positive_loss"] == {
            "count": 1,
            "denominator": 18,
        }
        assert values["correct_no_answer"] == {"count": 19, "denominator": 19}
        assert (
            values["partial_handling"]
            == values["conflict_handling"]
            == {"count": 3, "denominator": 3}
        )
