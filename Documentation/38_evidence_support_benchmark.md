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
