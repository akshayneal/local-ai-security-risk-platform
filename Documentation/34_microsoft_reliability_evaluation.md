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

## Residual retrieval-query diagnosis

A separate deterministic [query diagnostic](microsoft_reliability/query_diagnostic.json)
is reproducible through `evals/microsoft_diagnostics/query_terms.py`, with no model
calls or production changes. It compares the full canonical request, the same request
without adapter-generated observed_behavior, and raw canonical evidence alone.
Three existing synthetic non-authentication inputs and one new synthetic
authentication control are inspected; this is diagnosis, not a scored benchmark or
the conditional support/abstention experiment.

The adapter adds MFA/Conditional Access and unfamiliar-IP warning text to every
Microsoft request, including process-only inputs. The analyzer includes it in the
retrieval query. The authentication checklist scores 6 and appears in the top five
for all three non-authentication inputs. Removing that behavior field lowers its
score to 1 and removes it from their top five; raw evidence scores 0. A true
authentication control keeps the card under every representation (scores 9/4/3).
This proves a query-term effect on this lexical ranking, not that it caused any
particular generated claim or that raw-only queries preserve all useful context.

No query change is applied during or after the frozen treatment. The finding is a
specific next-step hypothesis for a separately declared query/support experiment.
Changing query construction would also require carefully recording actual retrieved
source authorization; the current frozen scorer reconstructs the original query.
Do not retune its checks or silently reinterpret this comparison. Default retrieval
and all historical retrieval metrics remain unchanged.

## Completed unchanged-suite treatment

The treatment ran once from clean implementation
`92e8ee3038715071389b8ff95c4b6f65f7ce7da8`, October 29, 2026,
17:56:12–18:54:20 UTC. All 32 records equal the journal, preserve the recovery
prefix and match baseline schedule/request hashes, source byte hashes and semantic
identity. Model identifier, temperature, seed state and retrieval settings match.
Microsoft complete-context 8192 is the intentional configuration change. Later
commits changed only tests, review and documentation, not executing source.

The byte-exact [treatment report](microsoft_reliability/treatment.json) SHA-256 is
`b8fc3a27a5784b177dce4a932b64f42478cefe49ad63dac6ad6537aede12e3cd`.
The [comparison](microsoft_reliability/comparison.json) replays the unchanged frozen
comparison function; [provenance](microsoft_reliability/treatment_provenance.json)
binds official artifacts and original journal bytes. No attempt was selectively rerun.

| Measurement | Baseline | Treatment |
| --- | ---: | ---: |
| Returned / requested | 29/32 (90.6%) | 31/32 (96.9%) |
| Withheld | 3/32 | 1/32 |
| First-pass valid / requested | 29/32 | 30/32 |
| Policy repairs attempted | 3/32 | 1/32 |
| Returned after repair / repairs | 0/3 | 1/1 |
| Completed model calls | 35 | 32 |
| Rejected model requests | 0 | 1 |
| Transport/JSON retries | 0 | 0 |
| Narrow returned-response machine check failures | 0 | 0 |
| Lexical coverage groups matched / returned groups | 29/31 | 34/34 |
| Median latency, all attempts | 90.583 s | 103.234 s |
| Total analyzer latency | 3289.066 s | 3421.702 s |

Three network responses gained availability; the largest case lost availability
through safe request rejection. There are 28 common returned attempts. Their median
latency increased from 85.995 to 102.055 seconds, so the fast rejected large request
must not be marketed as a speed improvement. Thirty-three treatment model requests
include 32 completed responses and one rejected request, separate from policy repair.

The [complete treatment review](microsoft_reliability/treatment_manual_review.json)
preserves early committed judgments. The [manual comparison](microsoft_reliability/manual_comparison.json)
records every paired transition, with separate returned and unassessable denominators.

| Manual dimension | Baseline present / ambiguous / absent (29 returned) | Treatment present / ambiguous / absent (31 returned) |
| --- | ---: | ---: |
| Material omission | 1 / 1 / 27 | 0 / 0 / 31 |
| Unsupported factual claim/inference | 8 / 8 / 13 | 10 / 8 / 13 |
| Unsupported authority/policy claim | 3 / 4 / 22 | 7 / 4 / 20 |
| Overclaiming/proportionality | 8 / 6 / 15 | 4 / 15 / 12 |
| Source applicability concern | 4 / 9 / 16 | 3 / 16 / 12 |

Three baseline and one treatment withheld outputs are unassessable for each
dimension, excluded above. These are subjective overlapping review judgments, not
machine-proven semantic rates. In the 28 common returns, factual concerns labelled
present remain 7/28 in both phases: three present-to-absent improvements, three
absent-to-present regressions, and other ambiguous transitions. Authority concerns
increase from 3/28 to 7/28. Present omission and ambiguous vendor-term coverage each
become absent. Overclaiming often shifts into ambiguity rather than a clear absence.
The experiment therefore does **not** establish broad semantic-claim reduction.

Notable improvements: supplied parent-child relation now represented; connection-only
trial two no longer invents a brute-force/login sequence; maintenance no longer maps
to Credential Access or labels a device as an account; public catalog no longer
invents sensitive data; hiring no longer restricts recruiter override; missing vendor
terms are explicitly checked. Deletion-command and LSASS-dump evidence remain present.

Residuals/regressions: training-note command still becomes an execution label;
network rows receive unsupported Initial Access/Discovery classifications; the LSASS
positive control adds a weakly supported Persistence hypothesis; process-only hash
case proposes account disablement without account evidence. The medium case fits
measured capacity yet borrows a brute-force/login label and miscounts rows. The
scoped LC-12 case extends charter authority and adds an unsupported high-impact
classification. More governance relevance prose calls checklist advice mandatory;
the conflicting-description case calls a design a containment-policy violation.
Public museum cases still preserve nonsensitive scope, but missing-documentation
versus absent-control ambiguity remains. Withholding the large defective baseline
output is an availability tradeoff, not a semantic correction among returns.

No new scorer, changed truth condition, overall pass score or statistical confidence
claim is introduced. Manual review remains unblinded implementation-assistant review;
independent adjudication is a release-readiness follow-up. The query diagnosis and
these results motivate a separately authorized held-out query/support experiment,
not additional treatment within this frozen comparison.
