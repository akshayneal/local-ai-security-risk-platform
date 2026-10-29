# Expansion Sprint 3: Microsoft evidence reliability closeout

This feature branch delivers bounded Microsoft endpoint compatibility, explicit
complete-context failure behavior, safe local diagnostics and a frozen fresh
before/after experiment. It is not a release or a claim of semantic reliability.
Microsoft input remains **USER VISUAL QA PENDING**. Unsupported classifications,
source-scope mistakes and output omissions remain possible after successful validation.

## Recovery and repository provenance

Sprint start was `feature/microsoft-soc-retrieval-integration` at
`949d4cbdc3320a2bd409702d6e26fc6e98cff1fb`. Work continued only on
`feature/microsoft-evidence-reliability`. The first continuation recovered clean
local/origin `06a7c4d2dcf7102dc0a4ae429ec4d9a0c99a5de7`; the second recovered
`58304d0e81562156b2d9ae7db3bf1da1c613daaa` plus an uncommitted review ledger.
Those prior judgments were preserved. See the [recovery record](microsoft_reliability/recovery.md)
for inherited commits and exact process/journal observations.

The inherited original baseline was alive at first recovery with ten completed
records and later at least sixteen. At second recovery it had completed all 32.
No baseline attempt was restarted. The parent command's automatic context phase
failed its clean-tree precondition before any context call. After a checkpoint,
the pending six probes ran once. A separate five-call native API contract probe
was predeclared and committed before its results. No inherited evaluation was
terminated, suspended or restarted, and no duplicate evaluation was launched.

Important checkpoints:

| Commit | Purpose |
| --- | --- |
| f8159d2 | Bounded local diagnostic tracing and controlled reproduction |
| 3f33cca | Fresh suite, rubric, scorer and plan frozen; untreated launch |
| 08edf92 | Exact completed baseline and preserved review |
| 61e02d5 | Separately declared native context-contract experiment |
| 4ad2f63 | Structured Microsoft endpoint compatibility |
| 92e8ee3 | Complete-context boundary and bounded grounding instructions; treatment launch |
| 79fc027 | Offline query-term diagnosis, without production retrieval changes |

Production implementation is `92e8ee3038715071389b8ff95c4b6f65f7ce7da8`.
Later commits add tests, review and documentation, with no executing application,
dashboard, frozen evaluator or reference changes during treatment. Final commit
identity is reported in the delivery message and Git history; a report cannot embed
its own eventual commit hash. Hosted CI must be checked against that exact pushed
commit. No merge, tag, release, force push or history rewrite was performed.

## What changed and why

`app/local_diagnostics.py` records bounded predefined machine codes, stages, safe
field names, hashed identity, repair status and timing only when explicitly supplied
by local evaluation. It drops raw responses, prompts, telemetry and arbitrary error
messages. `app/model_metrics.py` separately captures allowlisted numeric usage and
byte overhead. Neither adds ordinary API, UI, export or Activity diagnostic output.
Existing production trace behavior is preserved. Governance diagnostics are narrower
than SOC policy tracing; returned/schema outcomes do not prove semantic validation.

`app/microsoft_evidence.py` derives additional valid IP/port relationships from
validated individual Microsoft network rows. Bounded role labels and JSON projections
must preserve original row relationships. Tests cover malformed ports, role reversal,
cross-row joins, unrelated addresses, exact values, positive controls and repair.
The legacy generic textual grammar remains intact. Missing protocol stays unknown;
443 does not prove HTTPS. Finite prose recognition and original textual authority
remain limitations; this is not universal relationship or protocol entailment.

The historical port-443 trial cannot be retrospectively diagnosed. One controlled
reproduction withheld after an initial `IP_SHAPE` rejection and an `ENDPOINT_PAIR`
repair rejection (245.185 s). Rejected values were deliberately not retained, so
valid-pair false rejection versus invention is inconclusive for that trial.
Independent deterministic probes prove a format compatibility defect and its
bounded correction. See [diagnostics](32_microsoft_output_diagnostics.md).

Microsoft requests now use native loopback Ollama requests with context 8192,
`truncate=false` and `shift=false`, on the inspected runtime contract. Unsupported
runtime/host, rejected prompt and length-limited/incomplete generation fail closed.
There is no fallback into truncating behavior. A safe 422 error reaches the UI
without raw errors or a result. The installed SDK lacks the required native flags,
so the bridge uses the existing requests dependency with proxies and redirects off.
Generic SOC and governance retain their ordinary SDK generation configuration.
No new dependencies, external model calls, reference changes or registry changes.

Every Microsoft row contributes a source-field inventory entry. Full original
canonical evidence remains in the request and exports; there is no context selection
or omitted-row claim of completeness. Existing hostile-instruction quarantine is
still a separate prompt security treatment. Short Microsoft instructions distinguish
process launch from successful deletion, quoted mention from execution, and device
from account identity. A short governance paragraph distinguishes supplied scope,
known terms and binding authority from checklist suggestions. The generic SOC prompt
is byte-identical to the untreated checkpoint. No semantic regex engine was added.

## Context evidence and limits

Six original probes compared one, twelve and forty-five rows at 4096 and 8192.
The network case withheld after repair at both settings. Four longer-case responses
returned but contained semantic/identity defects. With default truncation, the
45-row prompt processed 2050/4098 tokens at the two settings; those counts alone
do not identify the retained rows. Tagged provider source supports middle-prompt
truncation as the mechanism, without proving per-row retention in those outputs.

Five separate native contract calls established successful short requests, rejected
large requests and output stopping exactly at the 4096 total-token boundary with
shifting disabled. Large HTTP 400 probes remain `other_server_error` in their raw
artifact because the fixed error allowlist did not match; no discarded error text
is reconstructed. Production handles 400/413 as generic rejected complete-context
requests, not a proven specific error-body classification.

Reported residency rose from 5,986,561,554 to 6,599,978,515 bytes (about 0.61 GB);
VRAM snapshots were about 4.21/4.19 GB. These are observed residency, not peak memory.
Latency is confounded by generation length, loading and repairs. One trial per
context cell gives no statistical confidence or isolated speed benefit.

In treatment, twelve rows used 4805 prompt plus 1362 generation tokens and retained
the deletion command and correct alert ID, but miscounted events and selected an
unsupported login incident label. Forty-five rows were rejected in 4.687 s, with
no result, no policy repair and no processed-token count. Actual user prompt bytes
include analyzer inventory overhead; input bytes are never relabeled as token counts.
No exact pre-inference tokenizer, fixed supported row count, semantic completeness
guarantee or governance large-input context protection is claimed. See the
[capacity report](33_context_and_evidence_budget.md).

## Frozen experiment and results

The fresh experiment has 24 synthetic cases (14 SOC, ten governance), 32 attempts
per phase, including three repetitions of four cases. Temperature 0.1, qwen3:8b
identifier `500a1f067a9f`, seed unset, legacy retrieval and no shadow are preserved.
Microsoft context 8192 and no eviction are intentional treatment variables;
governance retains default context. The bundled intervention and unseeded sampling
do not isolate causal contributions of individual changes.

Semantic suite hash:
`a8a1963d52360de8eca77be28c3513450f0d3e53586e8b17ef7976be09241d1c`.
Exact source byte hashes, request hashes, schedule, scorer, rubric and truth conditions
remain unchanged. Both original journals and reports remain at their ignored local
paths. Official reports are byte-exact copies, with provenance/hash checks and
offline replay. No failures were selectively rerun. Withheld outputs are
unassessable, never semantic passes. Narrow machine checks are not truth judgments.

The original baseline completed all 32 attempts, and all six original context
probes completed. The treatment also completed all 32 attempts. Final treatment
report SHA-256 is `b8fc3a27a5784b177dce4a932b64f42478cefe49ad63dac6ad6537aede12e3cd`.

| Measurement | Baseline | Treatment |
| --- | ---: | ---: |
| Returned / requested | 29/32 (90.6%) | 31/32 (96.9%) |
| Withheld | 3 | 1 |
| First-pass valid / requested | 29/32 | 30/32 |
| Policy repairs attempted / returned after repair | 3 / 0 | 1 / 1 |
| Completed model responses / rejected model requests | 35 / 0 | 32 / 1 |
| Transport/JSON retries | 0 | 0 |
| Narrow returned-response machine check failures | 0 | 0 |
| Lexical coverage groups matched / returned groups | 29/31 | 34/34 |
| Median latency, all attempts | 90.583 s | 103.234 s |
| Total analyzer latency | 3289.066 s | 3421.702 s |

Three network attempts gained availability; the largest SOC case lost it. Among
28 common returns, median latency rose from 85.995 to 102.055 seconds. The single
fast rejection does not establish improved latency. One network attempt repaired
an initial IP-shape defect successfully with full final validation.

| Manual dimension | Baseline present / ambiguous / absent (29 returns) | Treatment present / ambiguous / absent (31 returns) |
| --- | ---: | ---: |
| Material omission | 1 / 1 / 27 | 0 / 0 / 31 |
| Unsupported factual claim/inference | 8 / 8 / 13 | 10 / 8 / 13 |
| Unsupported authority/policy claim | 3 / 4 / 22 | 7 / 4 / 20 |
| Overclaiming/proportionality | 8 / 6 / 15 | 4 / 15 / 12 |
| Source applicability concern | 4 / 9 / 16 | 3 / 16 / 12 |

Each dimension excludes three baseline and one treatment unassessable withheld
outputs. In the 28 common returns, factual concerns labelled present remain 7/28
in both phases; authority concerns increase from 3/28 to 7/28. No broad unsupported
semantic-claim reduction is established. Present overclaiming falls, but ambiguity
increases substantially, and withholding a flawed large response changes denominators.
See the [full comparison and case findings](34_microsoft_reliability_evaluation.md)
and its linked exact artifacts for paired transitions.

The parent-child relation and explicit vendor-term coverage improve; maintenance
no longer confuses a device with an account; hiring no longer restricts recruiter
override; public catalog no longer invents sensitive data. Commands and LSASS
positive evidence remain represented. Important residuals/regressions include the
training-note execution label, unsupported network tactic mappings, an additional
Persistence hypothesis in the LSASS control, process-only account-disablement advice,
the medium case's borrowed login label and incorrect event count, and expanded
charter/checklist authority claims. Scoped monthly access review, fictional-law
uncertainty and approval-versus-veto distinctions remain visible. These are bounded
case observations, not universal preservation or accuracy guarantees.

The assistant manually reviewed every scheduled attempt using the original rubric,
with exact quotes and record hashes. Review is unblinded, implementation-assistant
review, not independent human certification. Present/ambiguous/absent judgments
overlap across dimensions, include moderate-confidence interpretations and must not
be added into an overall score. Historical baseline and committed early treatment
judgments are preserved; any revision would require an explicit explanation.

The [entity/identifier supplement](microsoft_reliability/entity_identifier_review.json)
records the device-to-account error no longer reproduced, executable punctuation
corruption persisting, corrected medium-case identity, and unassessable large-case
identity after withholding. It does not count withholding as an identity fix.

## Retrieval and next work

The conditional held-out retrieval support/abstention experiment was **not completed**.
No threshold, false-support/abstention rate or lost-answer tradeoff is claimed, and
no document 35 purports to report that experiment. No retrieval default changed.

A separate reproducible offline query diagnostic found adapter-generated MFA and
Conditional Access warning terms promote the authentication checklist into top-five
results for three non-authentication inputs. Removing that field lowers its score
from six to one and removes it from those top-five lists; a fresh authentication
positive control retains the card. This is a ranking effect, not proof that it
caused a particular hallucination. The medium treatment's borrowed login label is
a concrete residual concern, not authorization to retune this frozen evaluator.

Highest-value next sprint: separately freeze a held-out evidence-based query/support
experiment, preserving authentication positive controls and recording actual retrieved
authorization, then assess release readiness with independent review and user visual
QA. Do not combine this with new workflows or default retrieval migration. Additional
generic prompt wording is not established as the best next treatment. Recommend
GPT-6.1 Sol with high reasoning effort for that bounded implementation/experiment;
this is engineering judgment consistent with OpenAI's
[model selection](https://developers.openai.com/api/docs/guides/model-selection) and
[deployment guidance](https://developers.openai.com/api/docs/guides/deployment-checklist),
not a measured model comparison or an application model change.

## Validation, preservation and maturity

Final local Windows validation: **1,637 passed**, one existing Starlette/httpx
deprecation warning, in 70.63 seconds. Ruff passed, `pip check` reported no broken
requirements, and `git diff --check HEAD` passed. The six official-artifact replay
tests also passed separately. All Python commands used the repository virtual
environment; ordinary pytest required no model or internet access. No new dependency
or warning-driven environment change was introduced.

Production-launch exact-SHA hosted CI passed at
[run 40926037735](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40926037735)
for `92e8ee3038715071389b8ff95c4b6f65f7ce7da8`. The delivery message reports the
final documentation/artifact commit's exact-SHA hosted CI separately. A second
fresh Windows checkout was not created; local Windows validation and hosted fresh
Linux checkout checks are separate evidence.

AppTest and API tests exercise Microsoft failure messaging, original input retention,
stale-result/export clearing, generic compatibility and diagnostic non-exposure.
No visual browser/theme inspection was completed. No desktop/browser control,
screenshots or equivalent automation was invoked during either continuation. The
initial pre-restriction session attempted browser setup, blocked by the tool's
Windows URL policy; claiming zero attempted UI use across the entire sprint would
be inaccurate. **USER VISUAL QA PENDING**.

Frozen V1/V2/V3/V3.1/V3.2, Retrieval V1/V2, Microsoft stress, prior manifests and the
new suite/scorer are preserved. Only enumerated authorized production paths receive
new preservation exceptions; original historical blobs remain available. Stable
`main`, `origin/main` and peeled `v2.3.0` remain
`fde00d0ca5d21eecbc6973cc784550ed453edb7a`; annotated tag object remains
`22e5e1704940c41284d6b29e393fd51958f3ba34`. Isolated demo configuration is unchanged.
No vector RAG, cloud connector, credentials, new practitioner workflow, deployment
or automatic containment was added.

| Maturity question | Disposition |
| --- | --- |
| Baseline complete? | Yes, exact original 32 attempts preserved. |
| Context probes complete / behavior measurable? | Yes, six declared probes plus five separate native contract calls; byte/token/resource limits documented. |
| Diagnostic coverage complete? | Bounded requested diagnostic paths tested; no universal semantic diagnosis or complete governance policy trace. |
| Port failure diagnosed? | Rejection stages known for the controlled reproduction; exact rejected relationship and historical root cause inconclusive. |
| Microsoft endpoint compatibility corrected/validated? | Yes for tested structured forms, row relationships and negative controls; finite grammar limits remain. |
| Context overflow behavior safe? | Measured Microsoft complete-context rejection and unfinished-generation withholding verified; provider contract, not a fixed row budget or comprehension guarantee. |
| Material omissions better controlled? | Improvement in this sample: one present and one ambiguous baseline concern become absent; no completeness guarantee and medium-case count error remains. |
| Unsupported semantic claims reduced? | Broad reduction not established; factual concerns persist and authority concerns regress. |
| Unchanged-suite treatment comparison complete? | Yes, 32 vs 32, with machine replay and separate manual comparison. |
| Microsoft input release-ready? | No: user visual QA, independent review, semantic/query defects and capacity availability limits remain. |
| Default retrieval migration-ready? | No: held-out support/abstention tradeoffs are unmeasured; default unchanged. |
