# Expansion sprint 1 closeout

Scope: isolated Windows released-demo lane plus shared enterprise retrieval
foundation. Work stays on `feature/enterprise-retrieval-expansion`. No merge,
release tag, version bump, new practitioner workflow or default retrieval migration.

## Starting state, checkpoints and release preservation

Started on clean, synchronized `main` at
`fde00d0ca5d21eecbc6973cc784550ed453edb7a` (2.3.0). `git fetch origin` confirmed
`origin/main` and annotated `v2.3.0` resolve to the same release. Initial tests:
**1,287 passed**, one existing Starlette/httpx deprecation warning.

| Checkpoint | Commit | Result |
| --- | --- | --- |
| Demo package | `bf7d9cb37c36b127c49266f13e0eaa19055cadf2` | Scripts, shortcuts, safety helpers, startup smoke |
| Demo PID correction | `2fbb0ee53260f43617ead766dfc900b6d7b1a1c7` | Windows PowerShell 5 JSON array regression fixed |
| Contracts/import/legacy | `59fab4bdb6cfa4e2ef561f648b5494297dd03f0e` | Metadata/ACL/workflow/currentness and preservation checks |
| Lexical/benchmark | `86e3d74d328b864b20b738af1af02c54262417f8` | Fixed corpus/cases, SQLite BM25 and raw comparison |
| Dense/hybrid implementation | `4e82c83a93e99811c36fac92059aac0b4e130657` | Local provider, cosine, RRF, offline tests; live experiment code identity |
| Attribute preservation correction | `d9ac67cd5b4fa5cd512949ca819b722ba6e40d0c` | Restored root attributes; scoped new LF rules locally |
| Dense/hybrid evidence | `ccab9d4768c59f8ce8875521805e3b707aa748f1` | Full raw comparison, vectors and deterministic replay |
| Dependency update isolation | `094ba0205a775f59441149188df5ec427cdc8e85` | Side-by-side environment updates, previous environment retained |
| Offline upgrade recovery | `07aefee3a7d0ed436dfe49c87c1cc452f3d1681f` | Restore last ready release after failed bootstrap; mock-tested |

The final documentation commit is identified by
`git log --oneline v2.3.0..HEAD` and the final handoff SHA. Every coherent checkpoint
was tested and pushed; no force push or branch deletion was used. The final handoff
includes the final hosted CI run and clean-worktree verification after the last push.

Final source gate: **1,440 passed** (153 added: 15 demo, 138 retrieval), Ruff and
`git diff --check HEAD`. Windows exercises every test; Ubuntu skips only the 11
PowerShell execution cases. The original warning is unchanged; no dependency was
added just to remove it. Targeted checks preceded commits. Final hosted CI is checked
after the closeout push, separately from the local gate.

Hosted CI caught seven frozen-identity assertions after the initial root attribute
addition. Rather than relax historical checks, root `.gitattributes` was restored
exactly and new rules moved under the two new directories. Historical expected
scores/scorers/manifests/tests were not edited. Corrected implementation checkpoints
passed hosted CI. The live experiment retained its original code/provenance.

Remote release verification: main and peeled tag remain at `fde00d0`; annotated tag
object remains `22e5e1704940c41284d6b29e393fd51958f3ba34`. Released application,
dashboard, reference packs, README, dependency manifests, registry implementation,
frozen evaluation artifacts and standalone scorers/runners have no final diff.
The root attribute file also has no final diff. A new preservation test checks the
release tree directly. Only new retrieval code appears under `app/`.

## Demo delivered and actually validated

Package: four scripts under `scripts/demo`; detailed [installation/use](isolated_demo.md).
Default root `%LOCALAPPDATA%\LocalAISecurityRiskPlatformDemo` contains `repo`, `venv`,
`logs`, `runtime`, `launcher` and an ownership marker. The installer creates start/
stop desktop shortcuts and copies bootstrap scripts outside development. It was
run on this computer and the copied scripts were refreshed after corrections.

Fresh startup synchronizes only the dedicated clone to remote `main`. Fixed path,
origin, marker and reparse/worktree checks guard destructive synchronization. Network
failure restores the last commit that reached readiness, including recovery after
an interrupted later bootstrap. No ready commit means an actionable failure.
The development checkout is never reset/cleaned/switched by the demo launcher.

CPython 3.13 is checked explicitly. A separate environment installs the released
Windows snapshot; both manifests contribute to the dependency key. Unchanged keys
skip installation. Changed keys build separately under `venv/environments/<key>`;
`pip check` must pass before publishing selection, preserving the previous environment.
The original smoke environment at `venv` is reused while its hashes match.

Ollama must already be installed. The launcher checks/starts its shared local service
and checks/pulls only released `qwen3:8b` when missing. Shared Ollama is deliberately
left running by stop. The experimental embedding model is not a demo prerequisite.
Loopback ports are API **8100**, UI **8510**, Ollama **11434**; Streamlit receives
the dedicated API URL. No unrelated port owner is terminated.

Launch serialization prevents concurrent bootstrap/stop races. PID, creation time,
exact command, demo Python path, expected module and port are verified before stop.
Windows venv child processes are recorded/checked. Partial startup cleans up only
verified owned API/UI services and keeps logs. Browser opens after bounded health
polls. This is process ownership, not authentication against the same OS user.

Actual smoke: one startup/stop sequence on Windows created the clone/environment,
passed `pip check`, reached API/UI readiness at 2.3.0 / `fde00d0`, reused healthy
services on the second click, verified four owned launcher/child PIDs and stopped
both listeners. Bootstrap Python quoting and PID deserialization defects discovered
during this smoke were corrected and regression-tested. No model inference ran.
`-NoBrowser` was used; automatic browser rendering was not visually inspected.
Offline/failure/update recovery is deterministically mock/helper-tested, not a live
network-disconnection or second service smoke. Final read-only checks verified the
ready commit, unchanged environment reuse and absence of demo port listeners.

## Retrieval delivered

See the [foundation design](24_enterprise_retrieval_foundation.md) and
[measured benchmark](25_retrieval_benchmark_report.md).

One typed search protocol serves all four intended workflows. Normalized evidence
preserves source/document/version/chunk identity, hashes, type/family, content,
workflow/tags, owner, authority/policy scope, access/sensitivity, applicability,
effective/expiration dates and status. Retrieval rank/score/component ranks are
diagnostics rather than user-facing response fields. Conflicting IDs fail closed.

Authority is independent of relevance. Existing cards retain external/local guidance
labels, not organizational policy. Policy requires an explicit trusted scope. The
caller must grant every required access scope. Workflow, status/currentness,
authority/scope, applicability, type and dates are filtered before ranking. ACL is
a real filter, not RBAC/authentication. Production identity must supply trusted grants.

The importer reuses the existing loader, identity, chunker and unchanged registry,
admitting current exact registered hashes with reviewed sidecar metadata. A read-only
live version gate excludes old snapshots after registry updates; unavailable registries
raise. Concurrent updates during a search are not a transactional snapshot guarantee.

Legacy uses the original scorer and preserves per-workflow order. SQLite FTS5/BM25
adds whole punctuated identifier tokens and per-query eligible projections, preventing
restricted records from affecting IDF statistics. Dense uses a provider abstraction,
local Ollama and exact in-memory cosine vectors. Hybrid uses RRF (constant 60),
retaining component ranks. No reranker, vector database, LangChain or LlamaIndex.
Evidence snapshots use a separate versioned SQLite file; vectors use a checksummed
JSON cache. Missing/corrupt indexes/provider failures raise predictably with no
scope-changing fallback. No eligible evidence returns an empty list.

Real embedding model: `embeddinggemma:300m`, local Ollama 0.40.12, BF16, 768 dimensions,
621,875,917 model bytes; exact digest and formatting are recorded in the benchmark.
The user-authorized download was separate from qwen. No cloud AI call, API key or
Python dependency change was introduced. Deterministic pytest needs no model/network.

## Benchmark result and decision

74 records: 26 curated + 48 clearly synthetic, with 36 versioned document chunks.
48 queries: exact 8, paraphrase 8, workflow 6, authority 6, version/validity 6,
access 6, poison/noise 4, positive 4. Every candidate used identical queries/metadata
and authored graded judgments. Historical semantic output suites were not used.

| Candidate | Recall@5 | MRR | NDCG@5 | All eight violation counters |
| --- | ---: | ---: | ---: | --- |
| Keyword/tag control | 0.979167 | 0.891319 | 0.913359 | 0 |
| Lexical BM25 | 0.979167 | 0.944444 | 0.953372 | 0 |
| Local dense | 1.000000 | 0.963542 | 0.972761 | 0 |
| Hybrid RRF | 1.000000 | 0.979167 | 0.984622 | 0 |

Snapshot build: 22.6302 ms / 90,112 bytes. Query median/p95 milliseconds:
legacy 0.6566/0.7577; lexical 3.2270/3.6149; dense 72.2922/3240.0067;
hybrid 5.3717/10.3320. Dense includes lazy index/model work (51 endpoint calls,
53,491.9744 ms); hybrid reuses warmed vectors and queries. Those live timing columns
are not controlled cold/warm comparisons. Constructor times, full latency statistics,
hashes, category results, metadata and raw rankings are in `comparison.json`.

Saved vectors cover 114 texts and occupy 1,856,813 bytes. Offline replay reproduces
every rank, score, component rank, metric and violation exactly. RET-010 is the single
baseline/lexical recall miss; dense recovers the hiring-bias paraphrase. Dense ranks
forensic custody only fourth on RET-013; hybrid improves it. Two isolation-policy
first-rank disagreements retain plausible alternate relevant evidence. The benchmark
does not establish truth, instruction safety, negative-query abstention or scale.

Recommend preserving shared eligibility/provenance and taking **lexical into a bounded
shadow transition first**. Hybrid is the measured ranking winner and a viable semantic
candidate, but its small one-query recall gain and warmed timing do not justify new
default operational requirements. No post-result benchmark-specific filter or score
tuning was introduced. Preserve this comparison as separate evidence for the next step.

## Integration and exact migration gate

| Gate | Assessment |
| --- | --- |
| 1. Candidate architecture implemented | Yes, as an isolated package/benchmark |
| 2. Meaningful improvement/capability | Bounded evidence: improved ordering and one semantic recall recovery |
| 3. Zero access violations | Yes on this suite and deterministic tests |
| 4. Zero stale/version violations | Yes under declared snapshot/live-gate semantics |
| 5. Zero workflow violations | Yes |
| 6. Source/provenance guarantees intact | Released paths unchanged; new prompt metadata serialization not integrated/validated |
| 7. All existing tests pass | Yes in final local gate; hosted gate checked after push |
| 8. New preservation/regression tests pass | Yes, including exact offline replay |
| 9. Demo remains operationally simple | Lexical needs no new service; hybrid needs embeddings, not adopted by demo |
| 10. Reversible application migration | Shared interface exists; route/config transition remains unimplemented |

**No default, opt-in analyzer or shadow prompt integration.** Stable analyzers still
retrieve as released. The optional integration condition was not considered satisfied:
the old prompt serializer omits new authority/version metadata, and operational/held-out
evidence is limited. No SOC/AI Risk live generation smoke was needed or performed.
All existing sanitization, quarantine, repair, fail-closed, API/UI and source tests
pass against unchanged implementation. This is stronger preservation evidence than
claiming an untested end-to-end new retrieval path.

## Files, limitations and next authorized step

Files added: `scripts/demo/*.ps1`, `app/retrieval/*.py`, `evals/retrieval/` fixtures/
runner/metrics/local attributes, five new test modules, local artifact attributes,
lexical/four-way/vector artifacts, this report, design/benchmark reports and
`Documentation/isolated_demo.md`. The stable README/version/dependencies are untouched.

Limitations: small authored corpus with mostly one-chunk positive judgments; no
enterprise-load or held-out/no-answer evaluation; no authenticated access service;
no concurrent transaction-level eligibility guarantee; raw embedding format not
optimized by model-specific prompting; exact linear vectors and rebuilt FTS projections;
no automatic live model pin enforcement beyond recorded digest; browser not visually
smoked; offline/update recovery helper-tested. Existing SOC/governance semantic,
availability, formatting and identifier limitations remain visible in prior reports.
No unrelated roadmap work was implemented. No PR merge or release action was taken.

Next suggested scope, requiring a new instruction: trust-preserving prompt evidence
serialization and a curated-card lexical shadow path for the two existing workflows,
with source/authority regression tests, explicit outage behavior and fresh-query
latency measurement. Add held-out multi-chunk/alternate/no-answer judgments in a
distinct experiment before deciding on dense/default migration. These recommendations
are not implementation authorization.

Recommended next implementation model: **GPT-6.1 Sol, high reasoning effort** for the
bounded trust-boundary/configuration work. This is engineering judgment, consistent
with [official model selection](https://developers.openai.com/api/docs/guides/model-selection)
and [reasoning-effort guidance](https://developers.openai.com/api/docs/guides/deployment-checklist),
not a claim that cloud inference belongs in this local application.

| Success level | Final assessment |
| --- | --- |
| Foundation complete | Yes |
| Semantic benchmark complete | Yes, real local embeddings |
| Hybrid complete | Yes, implemented/benchmarked/replayed |
| Shadow-integrated | No, consciously deferred |
| Production-migration ready | No |
