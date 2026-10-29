# Shared retrieval at the application boundary

Default `RETRIEVAL_BACKEND=legacy` retains the exact released loader, limits (SOC 5,
AI risk 6), context formatting, prompts and source sanitation. Explicit `references=`
in evaluation/test calls bypasses orchestration and preserves historical replay.
No default migration, new dependency or model service was introduced.

Set `RETRIEVAL_SHADOW_BACKEND=lexical` separately to run lexical retrieval alongside
legacy. It never supplies generation context. The ignored local
`logs/retrieval_shadow.jsonl` records workflow, SHA-256 query fingerprint, ordered
legacy/lexical identities (array position is rank), overlap, elapsed milliseconds,
timestamp and fixed error code. No raw query, telemetry, content or exception message
is logged. A fingerprint is a correlation identifier, not anonymization. Retrieval
and logging faults are isolated from analysis. Shadow execution is synchronous and
adds bounded local CPU work; it is not a zero-latency background service.

Explicit `RETRIEVAL_BACKEND=lexical` enables the same curated-card importer,
eligibility and BM25 implementation for both SOC and AI System Risk Review.
Only public curated records are currently wired; no user-supplied access/policy
grants, registered document directory configuration or dense migration is implied.
The ranking query is capped at the retrieval contract's 20,000 characters; the
actual request/evidence sent to the analyzer is never truncated by this hook.
Lexical failures propagate through existing generic API errors. There is no silent
legacy fallback. Unknown active-backend values fail explicitly. Shadow configuration
errors are diagnostic only. Shadow is relevant when legacy is active; lexical mode
does not run a duplicate lexical shadow.

The new JSON evidence serializer separates `trusted_application_metadata` from
`untrusted_evidence_content`. It retains evidence/source identity, title, family,
type, authority, scoped policy authority, version/status/dates and applicability.
Ranking scores, ranks, ACL internals and file paths do not enter context. A narrow
application contract is prepended only on the opt-in path; the hardened semantic
prompt files are unchanged. Existing prompt-only instruction quarantine still runs.
Escaped JSON content cannot structurally create another metadata object, although
model obedience remains a semantic limitation.

Source IDs returned by the model are restricted to supplied envelope evidence IDs.
Chunks can be cited independently; parent document identity remains in application
metadata. Existing citation cleanup, observation checks, bounded repair and
fail-closed validation remain in force. Titles/families are restored from records.
For opt-in evidence, source-reference relevance is replaced with deterministic
application provenance, preventing model-authored relevance prose from upgrading
guidance into policy. Legacy source-reference behavior is unchanged. The existing
response schema stays intact; no stronger governance semantic guarantee is claimed.

Deterministic integration tests compare complete generation arguments and responses
between default and shadow, exercise failures, unknown configuration, oversized
ranking queries, metadata spoofing and fabricated citations for both analyzers.
Historical source-identity tests now resolve only four expressly authorized paths
at the foundation commit using `expansion_sprint_2_preservation.json`. Frozen suite,
scorer and official result bytes remain checked live with their original hashes.
