# Sprint 11: deterministic evidence and reasoning diagnostic

**RELEASE CANDIDATE: NO-GO.** The internal proof preserves required source values
independently of model recall. It does **not** make the model's interpretation
reliable. Both narrow and full answers still contain consequential reasoning,
polarity, scope and citation errors. No production route/default was enabled.

## What the evidence establishes

Eight experimental F3 submissions dispatched and report-bound **147/147 selected
required fields** exactly: 133 in six original controls, 14 in two identity-only
governance repeats. Actual stored provider requests and report panels were compared
with prospective source values, not just prompt-building tests. This measures a
bounded source projection, not all facts in arbitrary documents, authenticity,
model attention, interpretation correctness or operational authorization.

All **22 raw sends** have known final `done=true`, `done_reason=stop` and valid
model-facing JSON schemas. There were **zero censored, UNKNOWN, retry or actual SOC
repair attempts**. Four of six full F2 analyzers returned; both AI advisories were
correctly withheld by existing graph/reference boundaries. Eight F1 and eight F3
records returned. No live app HTTP endpoint or GUI was invoked.

The original F1 decisions matched authored labels in **3/6**, F3 in **4/6**.
These are label counts, not useful-report counts or accuracy estimates. F3's
approved-maintenance false positive and governance false negative remain failures
despite intact panels. All F3 `fact_ids` arrays were empty: availability of exact
facts does not establish claim-level semantic support.

## Design defect and limits

Original development identities included GAP/BOUNDED; frozen acceptance identities
also expose control types. Expected-decision/control/gold fields were never sent,
but these names can cue outcomes. **This is an implementation-author design
defect.** Original fixtures and outcomes were preserved, not silently renamed or
rescored. They support developmental debugging, not a clean or blind benchmark.

D3 prospectively repeated the governance pair with opaque LARCH-C31/LARCH-C74
identities. Both formats again missed the positive and returned no-finding on the
negative. Thus this observed failure does not depend solely on the suggestive
name; four correlated, stochastic repeats cannot establish that names never matter.
The originally proposed materiality-question ablation was abandoned **before any
send: NOT RUN 0**. D3 changed identity and derived hashes/fact IDs only, not the
original question/rule/substantive evidence. No heldout answer was used for tuning.

Other confounds: authored gold and reviews, shared within-pillar templates, fixed
order/cache/cold-load effects, no seed, different system scaffolds/context formats,
and F2's broader task plus extra guidance cards. F1/F3 use the same question/rule
and underlying inputs, but this is not a one-variable model-capacity experiment.
The generic SOC question mentions maintenance counterevidence even in the positive
case; the positive F3 explanation echoed it. That question defect remains recorded.

## Controlled observations

| Pillar | F1 plain reasoning, original pair | F3 evidence-bound, original pair | F2 original full contract |
| --- | --- | --- | --- |
| SOC | Positive false negative; approved failed-check negative core correct | Positive conditional investigation; negative invents a potential unauthorized-transfer pattern from one approved failed check | Both return. Both add unsupported C2 mappings and irrelevant PowerShell citations. Negative blurs known failed event with unknown outcome; positive suggests isolation on thin evidence |
| Governance | Positive denies gap while restating proposed/unimplemented gate; negative core correct | Same positive false negative despite two-of-six bypass preserved in panel; negative retains gate/sample/external-only scope | Both return. Positive reverses proposed/unimplemented review to reported implemented and unknown retention to lack. Negative broadens approval wording and conflates a review requirement with implementation scope |
| AI Security | Positive denies conditional risk because the example is simulated despite automatic ungated write; read-only negative core correct | Positive recognizes model-to-write tool and post-action oversight, but validation says to ensure the operator cannot intervene. Negative core correct but wrongly attributes read-only restriction to the model rather than tool | Both withheld. Positive tool finding omits ENGINE endpoint; negative adds generic unsupported concerns and omits required endpoints. Valid JSON did not satisfy the application boundary |

F1 positive failures: **3/3**, benign false positives **0/3**. F3 positive failures:
**1/3**, benign false positives **1/3**. Among the six original F3 answers, the
review identifies material unsupported claims in **two** (maintenance transfer
pattern and model/tool capability attribution), unsafe validation wording in
**one**, and question-contamination wording in **one**. Categories can overlap;
these are authored answer-level observations, not independent incidents. F2's four
returned records all have identified material claim/scope or mapping problems.
Both raw AI answers contain prerequisite/control polarity problems as well as the
binding failures that withheld them. No action actually ran or approval was granted.

| Block | Source commit | Sends / complete | Output tokens in execution order | Provider seconds |
| --- | --- | ---: | --- | --- |
| D0, six cases x F1/F3 | c0a9a2eabd9fa28a8ec148c4d7cde8a0b70beba0 | 12 / 12 | 128,209,109,142,167,311,163,238,175,237,189,196 | Per-attempt machine readout |
| D1, same six x F2 | c0a9a2eabd9fa28a8ec148c4d7cde8a0b70beba0 | 6 / 6 | 684,613,818,622,533,1318 | Per-attempt machine readout |
| D2, second installed model | NOT RUN | 0 | No compatible second completion model | N/A |
| D3, opaque governance pair x F1/F3 | 0f313ef1ff177b0bf47d71e3af6e2651773dca27 | 4 / 4 | See per-attempt readout | Per-attempt machine readout |

Total measured provider wall time: **1390.852560 seconds**. The largest full
answer used 1318 tokens; all stopped normally, with room under the 4096 ceiling.
Runtime was existing Ollama **0.40.13**, qwen3:8b **Q4_K_M**, digest
`500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
Every arm used think=false, temperature 0.1, context 32768, num_predict 4096,
stream=true, truncate=false, shift=false; installed top_p 0.95/top_k 20/repeat_penalty 1,
no seed. Requested context is within installed model 40960 capability. A conservative
UTF8-byte upper bound for messages/schema plus 512 template overhead and 4096 output
tokens must fit 32768 before dispatch. This does not prove attention or understanding.

Per-request wall/connect/idle bounds are 720/10/120 seconds; campaign 6 hours, wire
response 1 MB, retained data 24 MB. The larger request-local context avoids relying
on an optimistic tokenizer estimate; no shared Ollama setting changed. Measured
latencies reflect this machine/configuration and order, not a model ranking.
Hardware: Ryzen 9 5900HS, 8 cores/16 threads, 25131372544 bytes RAM. Read-only installed
metadata showed only Qwen completion and embeddinggemma:300m embedding capability.
No second-model inference, model download, installation, restart or production switch.
Thinking content was discarded; only sizes/hashes/usage survive.

## What the code owns

`app/deterministic_evidence.py` is an **internal, opt-in synthetic proof** with no
endpoint/UI import. `select` copies/revalidates the request, reuses the existing
SOC/governance EvidenceLedger or bounded typed graph leaves, then binds required
paths to immutable values, original roles, source revision and case scope.
Missing/oversized required fields or unsafe classification cause visible
unavailability; optional omissions are counted. Whole bounded prose fields remain
literal assertions, not machine-extracted absent/implemented/approved states.

`run` delivers those selected values through an explicitly supplied counted client.
`project` permits a small model decision domain, checks available/unique fact IDs
and rejects structured action/approval/canonical-field overrides. It constructs the
fact panel from the validated selection; model restatements cannot replace it.
`export_json` revalidates binding and rejects altered reports; `export_markdown`
escapes source and proposal text. False prose may still appear under **unverified
model interpretation**. Software cannot certify arbitrary natural-language entailment.

After core outputs, a failing offline test exposed a missing declared-tool
prerequisite check. The proof now reuses existing category/path traversal, binds
AI category/flow metadata and rejects a structured consequential-tool concern when
no reachable consequential capability is declared. This is a necessary condition
within the declared graph, not tested operational capability or model safety.
All six original F3 messages/schema and 133 source-panel values replay unchanged;
no original result was reclassified as successful. This extra check is **software
validated**, not a separate live AI improvement claim.

`DiagnosticBudget` and `CampaignLedger` reuse the earlier audited design in a new
namespace with new roots/options/caps. Durable local and aggregate reservations
precede each raw send; replies require a final frame; UNKNOWN blocks further work.
No proxy, redirect, SDK fallback or transport retry. The original SOC one-repair
path is preserved and tested with two counted fake sends; actual repairs were zero.
Raw new artifacts: **72 files, 497600 bytes**, all synthetic, with exact hashes in
the [machine readout](deterministic_evidence_v1/lab_readout.json).

Reviewed organizational retrieval/exact reviewed-source spans, production display,
Inspector/correction integration and private/sensitive data projection are **not
implemented in this proof**. Existing eligibility/version/source restoration and
correction-first exports remain unchanged and regression-tested. The synthetic
classification label is an internal caller responsibility, not authentication or
anonymization. No source text or model output can grant authority.

## Acceptance, preservation and software verification

Allowance: 24 development +12 reserved acceptance =36 global. Actual:**22/24 dev,
0/12 acceptance**,14 unused globally, no transfer. D0=12, D1=6, D2=0, D3=4.
**New Juniper acceptance NOT RUN:**12 scheduled,0 submitted/raw/completed, 12 NOT RUN,
four per pillar. SOC-negative/governance-positive viability failed, and its frozen
identities also expose control types. Frozen acceptance inputs/method/rubric/scorer
remain byte-identical to preregistration. No acceptance directory exists. Old Aster
and all unused old allocations were untouched. Independent adjudication is pending.

Start local/origin: feature/model-task-grounding-diagnostic-sprint10 at
564499f0537688b6422f48c51fc5995467f000c6. Work branch:
feature/deterministic-evidence-benchmark-sprint11. Checkpoints: preregistration
2cde4804fd56b49e621f4cea7d5e5f9a3781176e; initial implementation c0a9a2e...;
core preservation/opaque treatment 0f313ef...; replay cache isolation
10571eb9d45c7adf2edffc0e5509c43c4aa12663; final audit containing commit and
exact pushed-SHA CI are recorded in the final handoff.

Protected bytes: 590 s4check (405 visible/185 cache), 13 Northstar, 36 Cedar7, 14 Maple8,
18 Birch9 =671, plus 71 Elm Sprint10 files and seven Aster files, all historical
tracked material and installed AGENTS. No private database was queried or code
under s4check executed. All 405 inherited untracked files remain. Main/peeled v2.3.0
remain fde00d0ca5d21eecbc6973cc784550ed453edb7a. No launchers, registry, environment,
requirements, service/port config, PR, release, tag, merge or main push changed.
Historical Birch UNKNOWN remains unchanged; its journal was not replayed.

Only the immediately preceding current-tree scope guard receives one import and
one historical-at-SHA decorator. Its original assertions remain unchanged, proved
by AST equality and actual archived mutation rejection. The active Sprint11 guard
protects all other baseline blobs, exact allowed paths, Elm bytes and AGENTS.
See [audit](deterministic_evidence_v1/data_path_audit.md) for nine source chains and
[inventory](deterministic_evidence_v1/change_inventory.json) for every changed path.

Existing Windows Python 3.13.1; pre-core focused 148 passed/one existing warning,
66.57s; final focused 38 passed,12.33s. Final full Windows suite: **2266 passed, zero failed/skipped, one existing
warning, 273.83s**. Exact-SHA CI is supplied in the final handoff. Commands use Python -B,
PYTHONDONTWRITEBYTECODE=1, pytest -q -p no:cacheprovider, Ruff check --no-cache .,
pip check and git diff --check. No installation or environment modification.

Failure history is retained: initial collection failed before the proof existed;
the repair mock exposed the old metrics helper's 4K/8K limit (fixed in evaluation
dispatch only); a typed read-only negative test failed before the prerequisite
gate. The first full run had 2261 passes and four replay-cache FileExistsError
failures (253.11s). An independent cache now wraps the identical original archive
body; all 17 affected/preservation tests passed in 34.29s. Original helpers and
assertions remain unchanged. The final full rerun is recorded separately. Passing
tests demonstrate these software contracts, not semantic usefulness.

## Ranked decision and remaining review

1. Keep application-owned source/report projection as the experimental integrity
   foundation; extend it only with reviewed requirements and compatible tests.
   Do not promote the narrow model decision route by default.
2. Obtain independent review of expected judgments, unsafe wording and source
   applicability, then design a distinct, clean evaluation with opaque identities
   before any new outcomes. Original freezes/results remain historical evidence.
3. Clarify materiality/conditional-risk questions and typed, reviewed control
   assertions without weakening forbidden-inference checks or inventing prose parsing.
4. Compare another model only after separate installation/hardware authorization;
   no installed alternative was available, so no model superiority verdict follows.

**USER WORKFLOW / FINAL VISUAL QA and independent semantic review PENDING.** In a
later authorized session, manually use existing Development Start/Stop, the three
current workflows, benign/uncertain cases, exact source/field/version anchors,
safe withholding and correction-first exports. This proof has no new UI control.
Model-only recall, pipeline integrity and full report usefulness remain separate.
