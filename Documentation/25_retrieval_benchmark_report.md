# Retrieval benchmark (expansion sprint 1)

Independent retrieval evaluation v1, not a model-output or historical semantic
evaluation. Fixed corpus: 74 records = 26 existing curated cards plus 48 synthetic
records (36 versioned document chunks and 12 distractor notes). Fixed cases: 48,
all K=5: exact identifiers 8, semantic paraphrase 8, workflow 6, authority 6,
version/validity 6, access 6, poison/noise 4, positive controls 4.

All synthetic policies, vulnerabilities and requirements are fictional exercises.
The current/obsolete audit-retention pair shares document identity with distinct
content versions. Similar wrong CVEs/controls/tasks remain eligible distractors;
they are not artificially security-filtered to make ranking easy. Access, scope,
authority, date and workflow constraints use the common deterministic filter.

Judgments list required IDs, graded relevant/acceptable IDs and forbidden IDs.
Recall@5 uses all positive judgments, required recall is separate, MRR is first
positive reciprocal rank, NDCG@5 uses graded gain `2^grade-1`. Every case currently
has at least one positive; this suite does not measure unanswerable-query abstention.
Scores use authored keys, never an LLM. Narrow judgments can miss other useful
evidence; no enterprise generalization or statistical confidence is claimed.

Candidate filtering violations are counted separately: access, stale/failed/version,
workflow, authority/policy scope, applicability, validity, source type, and explicit
forbidden judgments. The control wraps the original keyword/tag ranking with the
same new eligibility layer as candidates. Thus security results establish the new
common layer, not retrospective ACL capability in the released application.

One poison case deliberately admits unverified material and expects that record;
retrieval does not detect arbitrary malicious instructions or establish truth.
Other policy-authority queries must exclude it. No benchmark-only production filter
or semantic-judgment oracle is implemented.

## Lexical checkpoint

The tracked `retrieval_evaluation/lexical_checkpoint.json` records full rankings,
scores, metadata, metrics, source/fixture hashes, runtime provenance and timings.
Both candidates use exactly the same cases. Lexical improves first-hit ranking
without improving aggregate recall; all eight violation counters are zero for both.
Final four-candidate results and architecture decision are added after the local
dense/hybrid experiment. Generation model calls and historical suite reruns: zero.

## Final measured comparison

[`comparison.json`](retrieval_evaluation/comparison.json) records all four candidates
on the **same unchanged 48 cases and 74 records**. Constructor/index-object setup
times were 0.0301 / 0.0193 / 4.4495 / 2.7643 ms for legacy/lexical/dense/hybrid.
The SQLite evidence snapshot took **22.6302 ms**, occupying **90,112 bytes**.
FTS projection build is charged per query; dense population is lazy, not included
in its constructor time. These are descriptive local measurements, not load tests.

| Candidate | Recall@5 | Required recall@5 | MRR | NDCG@5 | Query mean / median / p95 (ms) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Legacy control | 0.979167 | 0.979167 | 0.891319 | 0.913359 | 0.4919 / 0.6566 / 0.7577 |
| SQLite FTS5/BM25 | 0.979167 | 0.979167 | 0.944444 | 0.953372 | 2.5165 / 3.2270 / 3.6149 |
| Local dense | 1.000000 | 1.000000 | 0.963542 | 0.972761 | 1118.6791 / 72.2922 / 3240.0067 |
| Hybrid RRF | 1.000000 | 1.000000 | 0.979167 | 0.984622 | 5.1137 / 5.3717 / 10.3320 |

**All eight violation counters are zero for every candidate.** This includes
unauthorized access, stale/failed versions, wrong workflow, authority/policy scope,
applicability, validity, source type and explicit forbidden judgments. Invalid-output
fixtures separately prove the violation scorer detects actual violations; zero is
not produced by omitting those checks. The restricted record requires both scopes.

The 97.9% -> 100% recall change is **one additional query**, not broad enterprise
validation. Category-specific metrics and every rank remain in the raw artifact.
Baseline/lexical both miss RET-010's hiring-bias paraphrase in top five; common query
words can rank distractor notes ahead of the intended record. Dense recovers it.
Dense ranks the intended forensic custody record fourth for RET-013, behind a
PowerShell reference, backup guidance and discovery guidance. Hybrid ranks it first.
RET-028 and RET-041 place a different eligible isolation policy above the single
required policy in all candidates. Both discuss approval: the narrow authored key
does not fully represent every useful answer. No post-result judgment/rank tuning
was performed to remove this ambiguity. Poison can appear in unrestricted queries
(for example the legacy RET-034 ranking); provenance does not make it trusted.

## Model, storage and timing qualifications

Live local model: `embeddinggemma:300m`, BF16, 307.58M parameters, **768 dimensions**,
model bytes **621,875,917**, digest
`85462619ee721b466c5927d109d4cb765861907d5417b9109caebc4e614679f1`.
Ollama **0.40.12**, Windows CPython **3.13.1**, SQLite **3.45.3**. The original
generation model/configuration/snapshot was unchanged. No new Python dependencies.

There were **51 local embedding endpoint requests**, **53,491.9744 ms** cumulatively
inside those requests, and 114 cached texts (72 eligible document representations
plus 42 unique query strings). The first dense query cost **22,264.1578 ms** including
model load/lazy document embeddings. Dense ran first with an empty provider cache;
hybrid reused the same populated dense index and query cache, producing no additional
embedding request. **Hybrid's warm timing cannot be compared as a cold speed win.**
Cache hits grow from 6 after dense to 54 after hybrid. Real deployment latency must
measure fresh queries, index preparation, cache misses and resource contention.

The tracked [`vectors.json`](retrieval_evaluation/vectors.json) is 1,856,813 bytes;
exact list-based vector search is sufficient for this corpus. Actual Python heap,
GPU utilization and enterprise throughput were not measured. Offline replay produced
identical full rankings, scores, component ranks, metrics and violations. Its latency
is vector replay timing and is not a new live embedding performance result.

## Provenance and reproduction

Corpus semantic SHA-256:
`2c94deba053750c3c40f4d683b2ecc7e6835c962d832064c0be9373a13f218f8`.
Cases semantic SHA-256:
`450b791179075fd71afaf832f7b98150d9cf0efeaebddde429a0442dcc6b1272`.
Current LF fixture byte hashes: corpus
`9d8cb979d1b7f35b378b14be43facad3b474391e59cf7008d7a7b28eaa4046f7`, cases
`7986e3913afeae9fabc7bdd823bb08ce9efc6f0dd3825ec248d3781813c8c53b`.

Live comparison code is commit `4e82c83a93e99811c36fac92059aac0b4e130657`, with
per-source normalized-LF SHA-256 hashes verified against that tree in tests. The
reported dirty state records fixture LF normalization before that normalization was
committed. Fixture meanings and semantic hashes stayed unchanged. The earlier
lexical checkpoint retains its original Windows CRLF fixture byte hashes; its
semantic corpus/case hashes and ranking metrics match the final comparison.
New directory-local attributes now preserve LF bytes without modifying the frozen
root `.gitattributes`. Reports are retained separately, never overwritten by replay.

```powershell
.\.venv\Scripts\python.exe -m evals.retrieval.runner --backends legacy lexical dense hybrid --embedding-cache Documentation/retrieval_evaluation/vectors.json --output evals/results/retrieval_replay.json
.\.venv\Scripts\python.exe -m pytest tests/test_retrieval_artifacts.py
```

## Architecture recommendation

Keep the shared evidence/eligibility contracts. **Use lexical first for a separately
scoped shadow transition**, because it improves ordering and adds exact-identifier
support with no model or package requirement. Keep dense/hybrid as viable local
semantic candidates; hybrid is the best ranking result on this small suite, but its
incremental gain and warm timings do not justify making it the default now.

Before migration, test held-out multi-chunk organizational documents, no-answer
queries, alternate valid judgments, concurrent registry changes, cache invalidation,
trust-preserving prompt serialization, and uncached live query latency. No reranker,
enterprise vector service, RBAC or new workflow was added. This is an enterprise-
portable foundation, not evidence of enterprise scale or production readiness.
