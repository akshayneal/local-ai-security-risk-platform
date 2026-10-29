# Microsoft reliability v1: predeclared fresh experiment

24 synthetic cases: 14 SOC, ten AI System Risk Review. Truth conditions and review
rubric live in `evals/microsoft_reliability/`; this is separate from frozen Microsoft
stress, semantic and retrieval evaluations. Four high-value cases repeat three
times; all others run once: **32 planned attempts per phase**. Sampling is unseeded,
qwen3:8b, temperature 0.1, legacy retrieval, no shadow. Baseline has no application
context override. One-trial cases remain diagnostic, not reliability estimates.

SOC covers destructive presence/absence/quoted commands, related/unrelated processes,
unknown/explicit protocol, multiple endpoint rows, credential-negative/positive,
conflicting severity with maintenance approval, hash/injection and medium/large
context. AI risk covers public read-only, sensitive HR, hiring impact, affirmative
approval versus default execution, missing/known vendor/retention terms, scoped
organizational mandate, unverified legal allegation and contradictory descriptions.
Every case declares supported/unsupported facts, unknowns, admissible alternatives
and contracts. Relevant guidance is retrieved normally; source applicability remains
manual review rather than a claimed semantic score.

No overall score. Availability, first-pass validity, repair and post-repair validity,
source/identifier/recognized-pair membership, lexical material-evidence review flags,
latency and manual semantic findings retain distinct denominators. Coverage flags
are deliberately imperfect; positive/negative tests expose negation/paraphrase
limits. Unsupported factual/authority claims and omissions require quoted review.
Withheld responses have no assessable semantic output and never count as passes.

Suite source bytes are pinned to LF by local attributes; identity includes source
byte hashes and expanded semantic case hash. `freeze.json` is committed with cases,
plan, rubric and evaluator before baseline. Exact trial schedule and canonical
request identities must match for treatment comparison. Runtime provenance records
application commit, model identifier/settings and dirty state. Per-trial journals
persist all attempts to ignored `evals/results/`; completed synthetic reports may
be copied to official new documentation artifacts after review.

```powershell
.\.venv\Scripts\python.exe -m evals.microsoft_reliability.runner --phase preflight
.\.venv\Scripts\python.exe -m evals.microsoft_reliability.runner --phase baseline
.\.venv\Scripts\python.exe -m evals.microsoft_reliability.runner --phase context
```

Live runner requires a clean commit, refuses existing report/journal names and never
selectively reruns failures. No ordinary pytest invokes Ollama or internet access.
Production treatment is conditional on baseline evidence; scorer and truth conditions
stay frozen. Semantic review is implementation-assistant review, not independent
human adjudication.
