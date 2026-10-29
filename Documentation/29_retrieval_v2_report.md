# Retrieval V2: held-out queries and no-answer failure

The independently authored V2 corpus, judgments, metrics and plan were committed
before results at `cae8dd9fd6369b6ea39609abb63b81c3ce6e740d`. The comparison ran
on that clean commit with local Ollama `embeddinggemma:300m`. No post-result
threshold, filter or judgment tuning was performed. V1 remains unchanged.

Files: `evals/retrieval_v2/{corpus,cases,plan}.json`, runner/authoring code and
`Documentation/retrieval_evaluation_v2/comparison.json`; exact dense and hybrid
vectors are saved separately for offline replay. The artifact records byte and
semantic hashes, runtime, source hashes, raw rankings, category metrics and times.

96 new synthetic records cover 12 topics across SOC and AI risk: 24 adjacent
requirement/procedure chunks, 12 alternate summaries and 60 metadata decoys.
40 fresh queries include 12 exact controls, 12 compound paraphrases requiring
multiple useful chunks, 6 authority/access/currentness/applicability questions and
10 no-answer questions with related but insufficient evidence. They were held out
from V1 architecture selection, but are authored lab tests, not an independent
enterprise dataset or statistical generalization claim. No-answer facts include
missing deadlines, reputation, approvals, retention, thresholds and vendor storage.

Graded relevance accepts alternative evidence. Required-group recall accepts either
requirement text or its alternate, while requiring the procedure separately.
Positive Recall/MRR/NDCG exclude no-answer cases and report their denominators;
required Recall covers 18 cases and required-group recall covers 12. All candidates
use K=5 and identical eligibility. No threshold/abstention candidate was added:
no-answer success means an empty result and **all four candidates fail all 10**.
This is a false-retrieval metric, not evidence that a generated answer necessarily
hallucinates. There is no answer generation in this retrieval comparison.

| Candidate | Recall@5 (30) | Required recall (18) | Group recall (12) | MRR (30) | NDCG@5 (30) | No-answer false retrieval |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Keyword/tag | .8222 | .8333 | .6250 | .7972 | .7523 | 10/10 |
| Lexical BM25 | .9111 | .9444 | .8333 | .9500 | .8818 | 10/10 |
| Local dense | 1.0000 | 1.0000 | 1.0000 | .9444 | .9235 | 10/10 |
| Hybrid RRF | .9667 | 1.0000 | .9583 | .9778 | .9509 | 10/10 |

Every candidate has zero in all eight declared policy/filter violation counters.
These are metadata eligibility checks, not proof that evidence supports every claim.
Lexical misses custody procedure and some authentication/network/SharePoint/hiring
alternatives. Dense recovers every positive judgment but sometimes ranks an
alternate ahead of the strongest chunk. Hybrid misses the SharePoint requirement
group and one hiring alternate, despite higher MRR/NDCG than dense. A single overall
winner hides the tradeoff between complete evidence coverage and ranking order.

## Controlled timing

Milliseconds, median / p95 over 40 queries. Each dense/hybrid candidate has an
independent provider and query cache. Eligible-union documents are prepared first;
each unique query then runs once fresh and once cached. Fresh includes query
embedding and retrieval; warm includes cache lookup and retrieval. Lexical includes
FTS eligible-projection construction on every call. Timing is hardware/runtime
specific, with no parallel generation load deliberately added.

| Candidate | Fresh query | Warm query |
| --- | ---: | ---: |
| Keyword/tag | .212 / .363 | .203 / .233 |
| Lexical | 1.542 / 1.680 | 1.531 / 1.611 |
| Dense | 28.339 / 51.012 | 1.322 / 2.035 |
| Hybrid | 25.859 / 38.390 | 2.776 / 3.225 |

First embedding plus client/model readiness: dense **3,451.188 ms**, hybrid
**82.938 ms**. Remaining document embedding/cache preparation: dense **817.640 ms**,
hybrid **709.358 ms** (48 eligible-union texts each). The hybrid provider starts
independently, but the shared Ollama service/model and OS caches can already be
resident from dense. A true unloaded-model cold-start experiment was **not** run;
the shared local service was not forcibly unloaded. These initialization columns
must not be compared as equivalent cold starts. Preparation is excluded from
per-query timings and reported explicitly, unlike V1's ambiguous warm fusion path.

Reproduction (local model already installed; no download by this runner):

```powershell
.\.venv\Scripts\python.exe -m evals.retrieval_v2.runner --live --output evals/results/retrieval_v2.json --vectors-dir evals/results/vectors_v2
.\.venv\Scripts\python.exe -m evals.retrieval_v2.runner --vectors-dir Documentation/retrieval_evaluation_v2/vectors --output evals/results/retrieval_v2_replay.json
```

Offline replay checks every rank, score, component rank, metric and violation;
latencies naturally differ. Live runs are experiments, not deterministic CI tests.

Recommendation: retain legacy default, allow bounded lexical opt-in/shadow, and
investigate abstention/answer-support assessment under a new predeclared experiment.
Do not add a threshold chosen against these now-observed negative cases to production.
Dense/hybrid are useful ranking candidates but add model readiness cost and still
return unsupported related material. **Default-migration ready: No.**
