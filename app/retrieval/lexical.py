"""SQLite FTS5/BM25 over an eligible projection; no global ACL-sensitive IDF."""

import hashlib
import re
import sqlite3
from collections.abc import Iterable
from contextlib import closing

from app.retrieval.contracts import (
    EvidenceRecord,
    RetrievalError,
    RetrievalQuery,
    RetrievedEvidence,
)
from app.retrieval.filtering import VersionGate, filter_records, unique_records


def lexical_tokens(text: str) -> list[str]:
    """Normal words plus whole security identifiers encoded as FTS-safe tokens.

    The extra token preserves CVE/IP/control/command punctuation exactly; split
    terms still support partial lexical matches. This is a general tokenizer,
    independent of benchmark identifiers and judgments.
    """
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    for token in re.findall(r"[a-z0-9]+(?:[._:\-][a-z0-9]+)+", text.lower()):
        tokens.append("exact" + hashlib.sha256(token.encode()).hexdigest())
    return tokens


class LexicalRetriever:
    def __init__(
        self, records: Iterable[EvidenceRecord], version_gate: VersionGate | None = None
    ) -> None:
        self.records = unique_records(records)
        self.version_gate = version_gate

    def search(self, request: RetrievalQuery) -> list[RetrievedEvidence]:
        records = filter_records(self.records, request, self.version_gate)
        tokens = sorted(set(lexical_tokens(request.text)))[:256]
        if not records or not tokens:
            return []
        try:
            # Build only the eligible projection, BEFORE scoring. Forbidden content
            # cannot alter document frequencies or consume candidate slots.
            with closing(sqlite3.connect(":memory:")) as connection:
                connection.execute(
                    "CREATE VIRTUAL TABLE candidates USING fts5(identity, title, tags, content, family)"
                )
                connection.executemany(
                    "INSERT INTO candidates(rowid, identity, title, tags, content, family) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        (
                            ordinal,
                            *(
                                " ".join(lexical_tokens(text))
                                for text in (
                                    f"{record.source_id} {record.chunk_id or ''}",
                                    record.title,
                                    " ".join(record.tags),
                                    record.content,
                                    record.source_family,
                                )
                            ),
                        )
                        for ordinal, record in enumerate(records, 1)
                    ),
                )
                rows = connection.execute(
                    "SELECT rowid, bm25(candidates, 5.0, 3.0, 2.0, 1.0, 1.0) AS relevance "
                    "FROM candidates WHERE candidates MATCH ? ORDER BY relevance, rowid LIMIT ?",
                    (" OR ".join(f'"{token}"' for token in tokens), request.top_k),
                ).fetchall()
        except sqlite3.Error as exc:
            raise RetrievalError("SQLite FTS5 retrieval unavailable") from exc
        return [
            RetrievedEvidence(
                record=records[rowid - 1], score=-score, retriever="lexical", rank=rank
            )
            for rank, (rowid, score) in enumerate(rows, 1)
        ]
