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

## Completed untreated baseline

The original process completed at clean launch implementation
`3f33cca014ff7865981afcedacdc69107bb5f6d2`, October 29, 2026, 06:24:30–07:20:25 UTC.
The exact report is [baseline.json](microsoft_reliability/baseline.json), SHA-256
`4296d7e5a341fdbb5e918efa2d24ac94a36bd6220c1cce88486df65360789b68`.
Report records equal the append-only journal, all 32 scheduled request hashes/order
match, and the recovery snapshot prefix is preserved. Source changes during the run
were confined to tests/documentation; executing application and evaluator source
remained identical. See [recovery](microsoft_reliability/recovery.md).

| Measurement | Baseline |
| --- | ---: |
| Returned / requested | 29/32 (90.6%) |
| Withheld | 3/32 |
| First-pass valid / requested | 29/32 |
| Policy repairs attempted | 3/32 |
| Returned after repair / repairs | 0/3 |
| Raw completed model calls | 35 |
| Transport/JSON retries | 0 |
| Source/canary/critical-token/recognized-pair check failures among returns | 0 |
| Lexical coverage groups matched / returned groups | 29/31 |
| Median latency, all attempts | 90.583 s |
| Total analyzer latency | 3,289.066 s |

SOC-006/3, SOC-007/1 and SOC-008/1 were withheld after endpoint-pair rejection on
both generations. Safe codes cannot establish whether their discarded values were
valid or mutated. The independent deterministic probes establish the compatibility
defect; these failures establish availability cost, not proven false rejections.

The [complete manual ledger](microsoft_reliability/baseline_manual_review.json)
retains prior judgments and all 32 identities with exact quotes and record hashes.
Counts overlap; they are not an overall score. Among 29 returned responses:

| Manual dimension | Present | Ambiguous | Absent |
| --- | ---: | ---: | ---: |
| Material omission | 1 | 1 | 27 |
| Unsupported factual claim/inference | 8 | 8 | 13 |
| Unsupported authority/policy claim | 3 | 4 | 22 |
| Overclaiming/proportionality | 8 | 6 | 15 |
| Source applicability concern | 4 | 9 | 16 |

Three withheld responses are unassessable for each semantic dimension and excluded
from these returned-response denominators. Mixed confidence and ordinary ambiguity
remain in the ledger; no false certainty is inferred from three unseeded repetitions.

Specific findings: a quoted training command becomes an execution-attempt label;
the supplied parent-child process relation is omitted; a connection-only inference
borrows brute-force/login events from related guidance; maintenance gets an
unsupported Credential Access mapping and a device ID becomes an account. The two
long SOC inputs retain their deletion-command text but invent alert IDs and other
claims. Those identifier defects are outside the frozen critical-token check.
Credential-access evidence is correctly retained in the positive control.

The public museum assistant does not reproduce invented HR/employment sensitivity
in any of its three trials. The public catalog case does invent sensitive-data risk.
Known 14-day retention is retained in logging_requirements despite a lexical coverage
flag; that flag is a documented proxy limitation. Vendor terms are identified as
missing without invented training use. The fictional monthly mandate and unverified
legal allegation remain distinct. Some checklist relevance prose upgrades guidance
to binding obligations, and the hiring case proposes an unsupported restriction on
human override authority. No category-only Low/Approved answer key was imposed.

Treatment should address the objective endpoint compatibility and context-loss
risks, with bounded support-scope instructions and an observation inventory where
justified. The baseline does not justify a broad governance prompt rewrite or a
regex semantic truth engine. Cases, judgment rubric and scorer remain frozen.

## Pre-live treatment declaration

The treatment combines structured endpoint compatibility, a source-field inventory,
native no-eviction context behavior for Microsoft at measured 8192, a short
Microsoft evidence-interpretation paragraph, and a short governance support-scope
paragraph. Governance schema validation remains the existing contract; no semantic
validator or governance repair is claimed. Generic SOC prompt bytes and SDK options
are preserved by regression tests. No retrieval backend or reference pack changes.

Before treatment results, expectations are: valid structured endpoint forms should
be accepted while mutated relationships still reject; the long case should withhold
rather than return an incomplete-context result; the medium case should fit 8192;
unsupported scenario borrowing and entity-type confusion should decrease among
returned analyses; credential/hiring/scoped-mandate positive facts should remain.
Availability and latency can regress and must be reported separately. Unseeded
sampling and the bundled intervention prevent causal attribution to individual
components. The same rubric applies to all returned outputs, including regressions.

The exact 32-attempt treatment schedule, cases and frozen scorer are unchanged.
The implementation must be committed cleanly before `--phase treatment`; every
trial, rejection and repair is retained. No selective reruns, scorer tuning or
replacement overall score is permitted.
