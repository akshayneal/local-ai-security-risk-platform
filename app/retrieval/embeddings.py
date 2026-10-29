"""Local-only embedding protocol, Ollama provider and exact offline vector replay."""

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

import requests

from app.retrieval.contracts import RetrievalError
from app.retrieval.storage import canonical_json, fingerprint


class EmbeddingProvider(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...
    def provenance(self) -> dict: ...


def normalized(vector: list[float], dimensions: int | None = None) -> list[float]:
    if (
        not isinstance(vector, (list, tuple))
        or not vector
        or (dimensions is not None and len(vector) != dimensions)
    ):
        raise RetrievalError("Embedding dimensions are inconsistent")
    if any(
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
        for value in vector
    ):
        raise RetrievalError("Embedding contains invalid values")
    norm = math.sqrt(sum(value * value for value in vector))
    if not math.isfinite(norm) or norm <= 0:
        raise RetrievalError("Embedding has invalid norm")
    return [value / norm for value in vector]


def text_key(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class OllamaEmbeddingProvider:
    """No auto-pull, cloud provider, proxy or silent fallback. Explicit local model.

    Raw text is sent as documented by Ollama. Query/document methods are separate
    so another provider can implement its own task-specific formatting.
    """

    def __init__(
        self,
        model: str = "embeddinggemma:300m",
        host: str = "http://127.0.0.1:11434",
        timeout: float = 60.0,
    ) -> None:
        parsed = urlparse(host)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
            or parsed.username
            or parsed.password
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "Embedding host must be a local loopback HTTP Ollama service"
            )
        if "cloud" in model.lower():
            raise ValueError("Cloud embedding models are not allowed")
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.trust_env = False
        self.cache: dict[str, list[float]] = {}
        self.metadata: dict = {}
        self.live_calls = 0
        self.cache_hits = 0
        self.embedding_ms = 0.0

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        try:
            response = self.session.request(
                method,
                self.host + endpoint,
                timeout=self.timeout,
                allow_redirects=False,
                **kwargs,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise TypeError("not an object")
            return payload
        except (requests.RequestException, ValueError, TypeError) as exc:
            raise RetrievalError(
                "Local Ollama embedding service unavailable or invalid"
            ) from exc

    def _verify_model(self) -> None:
        if self.metadata:
            return
        tags = self._request("GET", "/api/tags").get("models", [])
        model = next((item for item in tags if item.get("name") == self.model), None)
        if model is None:
            raise RetrievalError(
                f"Local embedding model missing; run ollama pull {self.model}"
            )
        shown = self._request("POST", "/api/show", json={"model": self.model})
        if (
            "embedding" not in shown.get("capabilities", [])
            or shown.get("remote_model")
            or shown.get("remote_host")
        ):
            raise RetrievalError("Model is not a local embedding-capable model")
        self.metadata = {
            "provider": "ollama-local",
            "model": self.model,
            "digest": model.get("digest"),
            "size_bytes": model.get("size"),
            "details": model.get("details"),
            "ollama_version": self._request("GET", "/api/version").get("version"),
            "text_format": "raw-v1",
            "truncate": False,
        }

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        self._verify_model()
        missing = list(
            dict.fromkeys(text for text in texts if text_key(text) not in self.cache)
        )
        self.cache_hits += len(texts) - len(missing)
        for offset in range(0, len(missing), 16):
            batch = missing[offset : offset + 16]
            started = time.perf_counter()
            result = self._request(
                "POST",
                "/api/embed",
                json={
                    "model": self.model,
                    "input": batch,
                    "truncate": False,
                    "keep_alive": "5m",
                },
            )
            self.embedding_ms += (time.perf_counter() - started) * 1000
            self.live_calls += 1
            vectors = result.get("embeddings")
            if not isinstance(vectors, list) or len(vectors) != len(batch):
                raise RetrievalError("Embedding provider returned wrong vector count")
            for text, vector in zip(batch, vectors, strict=True):
                if not isinstance(vector, list):
                    raise RetrievalError("Embedding provider returned invalid vector")
                self.cache[text_key(text)] = normalized(vector)
        return [self.cache[text_key(text)] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def provenance(self) -> dict:
        return {
            **self.metadata,
            "live_calls": self.live_calls,
            "cache_hits": self.cache_hits,
            "cached_texts": len(self.cache),
            "embedding_ms": self.embedding_ms,
        }

    def save_cache(self, path: Path) -> None:
        payload = {
            "format": "local-embedding-cache-v1",
            "provider": self.provenance(),
            "vectors": self.cache,
        }
        payload["sha256"] = fingerprint(payload)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")


class CachedEmbeddingProvider:
    """Replay exact saved vectors; missing texts fail rather than calling a model."""

    def __init__(self, path: Path) -> None:
        try:
            payload = json.loads(path.read_bytes())
            digest = payload.pop("sha256")
            if (
                payload["format"] != "local-embedding-cache-v1"
                or fingerprint(payload) != digest
            ):
                raise ValueError("cache integrity")
            self.metadata = payload["provider"]
            self.cache = payload["vectors"]
            dimensions = None
            for vector in self.cache.values():
                normalized(vector, dimensions)
                dimensions = len(vector)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            raise RetrievalError("Embedding cache missing or corrupt") from exc

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        try:
            return [self.cache[text_key(text)] for text in texts]
        except KeyError as exc:
            raise RetrievalError(
                "Text not available in offline embedding cache"
            ) from exc

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def provenance(self) -> dict:
        return {**self.metadata, "execution": "offline-vector-replay"}
