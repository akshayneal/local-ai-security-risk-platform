"""Offline provider, cosine, fusion, ACL and unavailable-model regression tests."""

import json

import pytest
import requests
from test_retrieval_contracts import query, record

from app.retrieval.contracts import RetrievalError
from app.retrieval.dense import DenseRetriever, document_text
from app.retrieval.embeddings import (
    CachedEmbeddingProvider,
    OllamaEmbeddingProvider,
    normalized,
    text_key,
)
from app.retrieval.hybrid import HybridRetriever


class FakeProvider:
    def __init__(self):
        self.documents = []
        self.queries = []

    def embed_documents(self, texts):
        self.documents.extend(texts)
        return [[1.0, 0.0] if "approval" in text else [0.0, 1.0] for text in texts]

    def embed_query(self, text):
        self.queries.append(text)
        return [1.0, 0.0]

    def provenance(self):
        return {"provider": "deterministic-test-only"}


def test_dense_filters_before_provider_and_ranking():
    provider = FakeProvider()
    allowed = record()
    forbidden = record(
        evidence_id="forbidden",
        content="Secret text never sent",
        required_scopes=["private"],
    )
    retriever = DenseRetriever([forbidden, allowed], provider)
    hits = retriever.search(query())
    assert [hit.record for hit in hits] == [allowed]
    assert provider.documents == [document_text(allowed)]
    assert hits[0].score == 1.0
    retriever.search(query())
    assert len(provider.documents) == 1
    retriever.search(query(access_scopes=["private"]))
    assert len(provider.documents) == 2


@pytest.mark.parametrize(
    "vector",
    [[], [0, 0], [float("nan"), 1], [float("inf"), 1], ["no", 1], [True, False], "bad"],
)
def test_invalid_vectors(vector):
    with pytest.raises(RetrievalError):
        normalized(vector)


def test_embedding_dimension_mismatch_and_wrong_count():
    provider = FakeProvider()
    retriever = DenseRetriever([record()], provider)
    provider.embed_query = lambda text: [1, 0, 0]
    with pytest.raises(RetrievalError, match="dimensions"):
        retriever.search(query())
    provider.embed_documents = lambda texts: []
    with pytest.raises(RetrievalError, match="count"):
        DenseRetriever([record()], provider).search(query())


def test_dense_outage_has_no_fallback_or_filter_bypass():
    provider = FakeProvider()
    provider.embed_documents = lambda texts: (_ for _ in ()).throw(
        RetrievalError("offline")
    )
    for retriever in [
        DenseRetriever([record()], provider),
        HybridRetriever([record()], provider),
    ]:
        with pytest.raises(RetrievalError, match="offline"):
            retriever.search(query())
    assert (
        DenseRetriever([record(required_scopes=["restricted"])], provider).search(
            query()
        )
        == []
    )


def test_hybrid_rrf_scores_component_ranks_and_ties():
    provider = FakeProvider()
    records = [
        record(),
        record(
            evidence_id="two", title="Other", tags=[], content="Other general guidance"
        ),
    ]
    retriever = HybridRetriever(records, provider)
    results = retriever.search(query())
    assert results[0].record.evidence_id == "one"
    assert results[0].component_ranks == {"lexical": 1, "dense": 1}
    assert results[0].score == pytest.approx(2 / 61)
    assert results == retriever.search(query())
    assert results[1].component_ranks == {"dense": 2}
    with pytest.raises(ValueError, match="positive"):
        HybridRetriever(records, provider, rrf_constant=0)
    with pytest.raises(ValueError, match="share corpus"):
        HybridRetriever(records, provider, dense=DenseRetriever([record()], provider))


@pytest.mark.parametrize(
    "host",
    [
        "https://cloud.example",
        "http://192.168.1.3:11434",
        "http://localhost.evil",
        "http://user:pw@localhost",
        "http://localhost/path",
        "http://localhost?redirect=cloud",
    ],
)
def test_remote_embedding_hosts_are_refused(host):
    with pytest.raises(ValueError, match="loopback"):
        OllamaEmbeddingProvider(host=host)


def test_cloud_model_refused():
    with pytest.raises(ValueError, match="Cloud"):
        OllamaEmbeddingProvider(model="example:cloud")


def test_unavailable_local_ollama_is_predictable(monkeypatch):
    provider = OllamaEmbeddingProvider()

    def offline(*args, **kwargs):
        raise requests.ConnectionError()

    monkeypatch.setattr(provider.session, "request", offline)
    with pytest.raises(RetrievalError, match="unavailable"):
        provider.embed_query("text")


@pytest.mark.parametrize(
    "payload", [{"models": []}, {"models": [{"name": "embeddinggemma:300m"}]}]
)
def test_model_missing_or_not_embedding_capable(monkeypatch, payload):
    provider = OllamaEmbeddingProvider()
    monkeypatch.setattr(
        provider,
        "_request",
        lambda method, endpoint, **kwargs: (
            payload if endpoint == "/api/tags" else {"capabilities": ["completion"]}
        ),
    )
    with pytest.raises(RetrievalError):
        provider.embed_query("text")


def test_ollama_protocol_cache_and_replay(monkeypatch, tmp_path):
    provider = OllamaEmbeddingProvider()
    calls = []

    def request(method, endpoint, **kwargs):
        calls.append((method, endpoint, kwargs))
        if endpoint == "/api/tags":
            return {"models": [{"name": provider.model, "digest": "a" * 64, "size": 1}]}
        if endpoint == "/api/show":
            return {"capabilities": ["embedding"]}
        if endpoint == "/api/version":
            return {"version": "test"}
        assert kwargs["json"]["truncate"] is False
        return {"embeddings": [[3.0, 4.0] for text in kwargs["json"]["input"]]}

    monkeypatch.setattr(provider, "_request", request)
    assert provider.embed_documents(["text", "text"]) == [[0.6, 0.8], [0.6, 0.8]]
    assert provider.embed_query("text") == [0.6, 0.8]
    assert sum(endpoint == "/api/embed" for _, endpoint, _ in calls) == 1
    assert provider.session.trust_env is False
    path = tmp_path / "vectors.json"
    provider.save_cache(path)
    replay = CachedEmbeddingProvider(path)
    assert replay.embed_query("text") == [0.6, 0.8]
    assert replay.provenance()["execution"] == "offline-vector-replay"
    with pytest.raises(RetrievalError, match="not available"):
        replay.embed_query("different")
    payload = json.loads(path.read_bytes())
    payload["vectors"][text_key("text")][0] = 99
    path.write_text(json.dumps(payload))
    with pytest.raises(RetrievalError, match="corrupt"):
        CachedEmbeddingProvider(path)
