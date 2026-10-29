# Enterprise retrieval foundation (unreleased expansion branch)

The released 2.3.0 analyzers continue to call
`app.reference_loader.get_relevant_references`: token overlap plus tag bonus over
curated JSON cards. This is the control, not modern RAG. Source sanitization,
prompt quarantine, SOC validation/repair and governance processing are unchanged.

## Shared contracts and eligibility

`app/retrieval` owns `RetrievalQuery`, `EvidenceRecord`, `RetrievedEvidence` and the
`Retriever.search(query)` protocol. All four intended workflows have explicit enum
values; only the two released workflows exist in the application. Search fields
have executable semantics: top K, source types, authority categories, required
applicability tags, granted access scopes, policy scopes, as-of effective/expiration
dates and version restrictions. Empty filter sets mean unrestricted except access
and policy scope, which default to no grants. Expiration dates are exclusive.
`include_inactive` explicitly admits inactive snapshot records, never failed ones.
As-of dates are validity filters, not historical registry reconstruction.

Evidence preserves source/document/version/chunk identities, document content hash,
chunk hash, source path, title, content, type, family, tags, workflow scope, authority,
policy scope, owner, sensitivity, access requirements, applicability and validity
dates. Results add backend score/rank and component ranks. Identical evidence IDs
collapse; conflicting payloads fail rather than choosing ambiguous provenance.

Authority is categorical, not a relevance boost. Existing cards are external
framework guidance or local reference guidance, never binding policy. A policy
requires explicit trusted `policy_scope`, and retrieval must grant that scope.
Unspecified imported material is unverified. None of these labels establishes
truth or neutralizes instructions inside content; downstream trust controls remain
necessary. Synthetic fixtures are not real policies, legal or federal requirements.

`filter_records` runs before ranking. All required record access scopes must be
granted; workflow membership, authority, applicability, dates and version status are
checked independently of backend. Access context is supplied by the caller: this is
a tested eligibility mechanism, not authentication/RBAC. A future authenticated
server must derive grants from trusted identity, not accept end-user self-assertion.

## Existing ingestion and legacy adapter

`load_registered_records` reuses TXT/Markdown/PDF loading, document identity, existing
chunking and the unchanged SQLite registry. It requires reviewed sidecar metadata
by document ID; content cannot self-assign authority/access. The registry stores
identities, not payloads, so the importer reloads files and only admits their exact
current registered hash. `registry_version_gate` reads the registry in read-only
mode and rechecks current identity/hash/chunked status at query time, excluding an
old index snapshot after a registry update. Missing/corrupt registries raise
`RetrievalError`. It does not create or migrate a registry. When using registered
records, supply this gate to the retriever; snapshot-only synthetic/card benchmarks
use explicit status metadata. No historical-version reconstruction is promised.

`LegacyRetriever` uses the original tokenizer and scoring function unchanged.
`load_curated_records(mode)` preserves workflow-specific card order including tie
order. Deterministic tests compare the complete ordered legacy cards with today's
function. Shared checklists carry both existing workflow scopes without duplication;
future workflows need explicit metadata review before consuming them.

## Checkpoints and operations

Checkpoint 1 implements the [isolated demo](isolated_demo.md). Checkpoint 2 adds
contracts, conservative metadata import, current-version gate and legacy adapter.
Later sections and the benchmark report record candidate and migration decisions.
No new dependency or registry schema change is needed for these foundations.

## Lexical candidate and rebuildable snapshot

`LexicalRetriever` uses standard-library SQLite FTS5/BM25. A general tokenizer
indexes ordinary words and hashed whole punctuated tokens, preserving exact CVE,
IP, control and command identifiers alongside split terms. Identity/title/tag/
content/family field weights are fixed at 5/3/2/1/1 before evaluation. Queries use
quoted OR terms (at most 256), never user-supplied FTS syntax. Ties preserve corpus
order. Only eligible records enter a per-query in-memory FTS projection. This also
prevents forbidden content from changing IDF statistics or consuming top-K slots.
Projection rebuild cost is included in query latency; it is a small-corpus design,
not an enterprise-throughput claim. Larger backends should implement authorized
prefiltering with equivalent semantics behind the protocol.

`storage.py` persists a versioned, ordered SQLite evidence snapshot with a semantic
SHA-256 manifest. Corrupt/missing/incompatible snapshots fail predictably and must
be rebuilt; no implicit backend fallback or relaxed access scope. This is separate
from the unchanged document registry. Connections close explicitly on Windows.

```powershell
.\.venv\Scripts\python.exe -m app.retrieval.index build
.\.venv\Scripts\python.exe -m app.retrieval.index status
.\.venv\Scripts\python.exe -m app.retrieval.index build --raw-docs knowledge_base/raw_docs --registry knowledge_base/registry/document_registry.db --metadata path/to/reviewed-metadata.json
.\.venv\Scripts\python.exe -m evals.retrieval.runner --output evals/results/retrieval.json
```

The registered-document options must be supplied together. The metadata JSON maps
document IDs to explicit workflows, source_type, source_family and optional trusted
metadata. A rebuilt snapshot does not override query-time registry currentness.

The independent retrieval benchmark reads committed JSON fixtures. The authoring
module can regenerate them deliberately but the runner never rewrites judgments.
See the [benchmark report](25_retrieval_benchmark_report.md) for limitations and results.
