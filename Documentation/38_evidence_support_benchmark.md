# Evidence support v1: frozen held-out experiment

Sprint 4 starts from the fully closed Mini-Sprint 3.5 at
`47f038602b03b38854dfe82024941f2d4204ca76`, whose
[exact-SHA CI](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40975409627)
passed. Mini-sprint results remain 8/8 returns per phase, 16 total model calls, zero
repairs, with residual C2, Initial Access, logging-authority and compliance defects.
That branch is preserved; new work uses `feature/evidence-support-workbench`.

This distinct benchmark freezes **43 cases, 55 synthetic source records, 14
categories**, plan, generator, runner, judgments and methodology before candidate
results. There are 18 full-support, 14 related-but-insufficient, five no-eligible,
three partial and three conflicting cases. Three additional no-answer cases are
included among the related-but-insufficient gold cases, with empty relevant sets.
No-answer gold therefore covers 19 cases; full-support false-support denominator
includes all 25 non-full-support cases, including partial/conflict.

The [methodology](../evals/evidence_support_v1/methodology.md) defines distinct
relevance, sufficiency, required-group, abstention, eligibility, authority, scope,
version and latency metrics. Gold judgments never enter the application assessor.
The existing legacy, lexical, dense and hybrid rankers use identical K=5, existing
pre-ranking eligibility and default RRF=60. No fourth/new backend, score-support
threshold, post-outcome tuning or production migration. Local embeddinggemma:300m
is already installed; no model download or cloud embedding is introduced.

The scope is deliberately bounded. Exact structured record assertions can establish
what an eligible record says, within its trusted metadata scope; they do not prove
external reality. Guidance cannot create a case event or a binding requirement.
An observation source type is separate from operational guidance. A scoped policy
requirement cannot establish implementation. The natural-prose policy positive
exposes the lost-answer cost if a conservative candidate cannot interpret it.

Synthetic access grants and current-version maps are fixture-owned trusted test
context. No query/source text grants access or policy scope. No application registry
is modified. Wrong-team, access-restricted, wrong-workflow, inactive, future, expired
and registry-superseded evidence exercise eligibility before ranking/embedding.

Rankers only return candidates; they do not themselves assert factual support.
The explicitly named any-hit-means-support comparator is a diagnostic heuristic,
not measured current production behavior or a generated-hallucination count.
No composite score or universal retriever superiority is claimed.

Frozen source/data identities are recorded in
[freeze.json](../evals/evidence_support_v1/freeze.json). Results will be appended
after the once-only ranking run and the separately committed support candidate.

## Completed result

Ranking launch `abd9ab214e24bccd9f052bfd75dffe87afbdca16` completed all 172
case/backend rows once, with a byte-exact journal/report comparison. Installed local
embeddinggemma digest is
`85462619ee721b466c5927d109d4cb765861907d5417b9109caebc4e614679f1`.
Fifty-eight embedding requests populated an exact replay cache. There were **zero
qwen generations** for this primary experiment. Corpus and judgments stayed frozen.
Candidate `1d123a7db13c12089fb13a9ca55dc164ca8b767b` was committed before its
offline assessment pass. [Provenance and artifacts](evidence_support_v1/assessment_provenance.json)
bind both candidate modules, the exact ranking/assessment reports and vector cache.

| Metric | Legacy | Lexical | Dense | Hybrid |
| --- | ---: | ---: | ---: | ---: |
| Mean eligible relevant Recall@5 (35 nonempty gold sets) | 1.0 | 1.0 | 1.0 | 1.0 |
| Full-support evidence sufficiency@5 (18 positives) | 18/18 | 18/18 | 18/18 | 18/18 |
| Required-group recall (24 cases with nonempty groups) | 1.0 | 1.0 | 1.0 | 1.0 |
| False full-support decisions (25 non-full cases) | 0/25 | 0/25 | 0/25 | 0/25 |
| False abstention / positive loss | 1/18 | 1/18 | 1/18 | 1/18 |
| Correct no-answer | 19/19 | 19/19 | 19/19 | 19/19 |
| Correct partial / conflict handling | 3/3; 3/3 | 3/3; 3/3 | 3/3; 3/3 | 3/3; 3/3 |
| Eligible-source / wrong-authority support violations | 0; 0 | 0; 0 | 0; 0 | 0; 0 |
| Diagnostic any-hit false support | 18/25 | 18/25 | 20/25 | 20/25 |
| Median ranking milliseconds | 0.290 | 1.291 | 24.666 | 2.264 |
| Median support-assessment milliseconds | 0.098 | 0.097 | 0.101 | 0.101 |

All rankers reach a ceiling on this small, explicit synthetic corpus. This is weak
evidence for choosing among them; no default migration is justified. Vector caching
and backend order affect latency: hybrid reuses dense vectors/query embeddings, so
the observed medians do not establish a causal hybrid speed advantage. Eligibility
includes workflow, access, policy scope, dates, status and fixture registry currentness.
Tests also verify never-eligible restricted/wrong-team/old/future/expired sources did
not enter the embedding cache, rather than merely hiding them after ranking.

The one lost positive is the valid natural-prose Juniper policy. It is retrieved but
the bounded structured matcher cannot interpret it. This loss is preserved; no parser
or answer-key tuning follows it. Structured requirements match only reviewed scoped
policy metadata; policy wording cannot prove implementation. Source assertion
matching is a useful software primitive, not general semantic intelligence or proof
that future production analyses will avoid unsupported claims.

The any-hit heuristic is explicitly diagnostic. Its 18/25 or 20/25 false-support
counts are **not** generated hallucinations and are not labeled current production
decisions. Raw retrievers provide candidates; they make no support assignment.
The assessment layer, ranking quality and human/model analysis must remain separate.

No errata or original judgment revisions were needed. Two artifact tests replay all
four rankings from cached vectors, every assessment, group metrics, source eligibility
and the false-abstention cost without Ollama/network. Live semantic validation is
separately bounded and must not be inferred from this deterministic result.

Judgments were authored by the implementation assistant before candidate outcomes.
Independence here means the gold data is separate from the candidate's inputs;
it is not independent human/expert adjudication. The explicit synthetic subjects
and structured assertion format make ranking relatively easy and do not represent
the full difficulty or prevalence of real organizational documents.
