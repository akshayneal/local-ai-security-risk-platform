# Sprint 10: model versus task diagnostic

**RELEASE CANDIDATE: NO-GO.** Task burden, decision wording and generation budget
are demonstrated contributors in these controls. Model fidelity remains a separate
blocker. These small authored observations cannot establish one universal primary
cause or justify a model-size verdict.

The lab used **16/16 raw requests**. All had final done=true: twelve complete JSON
answers, four known token-limit withholdings, **zero UNKNOWN/timeouts, retries or
SOC repairs**. Aster is **NOT RUN: 0/12 submitted**; its twelve reserved calls
remain unused and cannot become development allowance. Production source/defaults
remain unchanged. Narrow helpers remain experimental and inert.

## Diagnosis and counterevidence

Thinking-off produced complete answers where default/on exhausted the fixed
1280-token budget. This is operational evidence under a censored budget, not proof
that thinking intrinsically reduces fidelity. Full-task answers still failed
endpoint binding or used unsupported categories/checklist scope.

The one-path task reduced context, schema burden and answer length, but v1 called
the positive path no_finding while restating its unfiltered-input mechanism. One
generic explicit conditional-risk rule then produced the expected positive concern
and benign no-finding decisions on the same pair. This implicates task definition
as well as complexity. Counterevidence: the rule supplied substantial decision
logic, the positive answer echoed it, both final rationales ended mid-sentence at
the 400-character schema limit, and model text still omitted path IDs/full facts
and mixed validation with attack prerequisites. No failed result was repaired or
relabeled as a successful advisory.

The ledger added SOC process ID731, but did not fix unsupported Discovery mapping,
irrelevant PowerShell citations or approval-scope loss. Governance still omitted
reported implementation evidence and turned unknown retention into lack.
**Ledger remains OFF.** No general model accuracy or safety percentage is inferred.

## Source, checkpoints and preservation

Start: feature/controlled-inference-fidelity-sprint9, local/origin equal at
b6d84530b6eb9dccbb328a8dcffb0f9b532ef7ab. Continued the already created branch
feature/model-task-grounding-diagnostic-sprint10 and preserved interrupted work.
No Sprint 10 journal/reservation/artifact existed at resume; actual roots were
inspected rather than inferring zero from Git status.

| Commit | Purpose |
| --- | --- |
| 960f08a9e76503fac4f5b7cf1c073302b5d365b9 | Prospective cases/rubric/runtime, counted streaming/campaign transport, Aster isolation mocks, narrow v1, active scope guard. All 14 core calls used this source. |
| ad14f124f3511dbf7af109d50c8f3d05c6037b4a | Preserve core outcomes; optional explicit-v2 decision rule for two D4 calls. Recorded v1 prompts/schema remain byte-identical; cases/rubric/options unchanged. |
| Final audit commit | This report and final identities/reviews/inventory. Exact containing SHA, origin equality and exact-SHA CI are in the final handoff. |

Protected sets matched: **590 s4check, 13 Northstar, 36 Cedar7, 14 Maple8 and 18
Birch9 files**, installed AGENTS bytes, all historical tracked material and all
seven inherited Aster files. No s4check code ran or private database was queried.
The 405 inherited untracked files remain visible. No cleanup, stash, rewrite,
ignore-rule/launcher/port/shortcut change, local dependency/model installation or
service restart. Main and peeled v2.3.0 remain
fde00d0ca5d21eecbc6973cc784550ed453edb7a. No merge, PR, tag or release.

Only Sprint 9's current-tree scope assertion is replayed at immutable Sprint 9.
Its original body/assertions remain unchanged, with exact AST and actual archived
mutation rejection. A new active guard protects all other baseline blobs and exact
allowed paths. Old guards/gold/results/manifests were not weakened. Exact paths:
[change_inventory.json](model_task_diagnostic_v1/change_inventory.json) and
[sprint10_preservation.json](sprint10_preservation.json).

## Controlled results

Four distinct synthetic cases; technical graphs are correlated repeats. Every lab
arm used existing qwen3:8b Q4_K_M digest
500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41,
Ollama 0.40.13, temperature 0.1, context 8192, num_predict 1280, no seed, global system
instructions, strict streaming/no-truncate/no-shift. D1 changes only top-level
think; stored wire bodies were verified equal after removing that key per graph.

| Arm | Raw | Complete JSON / known capped | Contract returns | Seconds in case order | Authored finding |
| --- | ---: | --- | --- | --- | --- |
| D1 full/default | 2 | 0 / 2 | 0 analyzer | 177.57 /170.37 | Budget-censored; facts unassessable. |
| D1 full/off | 2 | 2 / 0 | 1 analyzer | 80.90 /65.80 | Positive missing endpoint plus unsupported output concern; benign generic/contradictory gaps. |
| D1 full/on | 2 | 0 / 2 | 0 analyzer | 170.49 /171.75 | Budget-censored; facts unassessable. |
| D2 full/off | 2 | 2 / 0 | 1 analyzer | 81.98 /42.35 | Positive binding/category failure repeats; benign checklist scope poor. |
| D2 narrow-v1/off | 2 | 2 / 0 | 2 experimental | 25.31 /29.04 | Positive false negative; benign scoped decision appropriate, prevention wording overconfident. |
| D3 ledger OFF/off | 2 | 2 / 0 | 2 analyzer | 100.25 /125.85 | SOC mapping/citation and governance state/scope failures. |
| D3 ledger ON/off | 2 | 2 / 0 | 2 analyzer | 96.18 /123.17 | PID 731/external-sharing wording improve; material failures persist. |
| D4 narrow-v2/off | 2 | 2 / 0 | 2 experimental | 30.90 /36.17 | Expected core decisions; incomplete rationales and full-fact retention. |

Technical order is positive/benign; D3 order is SOC/governance. Six public analyzer
records returned from twelve full submissions; four experimental records returned
from four narrow submissions. No live HTTP app endpoint was invoked: actual
analyzers/internal contracts ran directly, with separate API/UI/export mock tests.
Do not call these HTTP 200s. Twelve complete raw answers passed model-facing
Pydantic shape checks; that is not twelve useful/supported advisories.

Of 96 scheduled compound full facts: **24 unassessable, 5 retained, 38 partial,
19 omitted, 10 contradicted** under the prospective rubric. Facts include IDs/roles,
quantities, attribution and scope. Some share an error, such as retention polarity;
these are not independent failure incidents or an accuracy denominator. Partial
semantic fragments remain visible. App-copied purpose, IDs and selected paths do
not earn model-retention credit. Narrowing loses coverage; all six facts and the
four selected-path facts per graph remain separately inspectable.

Concrete failures and gains:

- Full positive cited WRAPPED-CONTEXT but omitted its REPHRASER endpoint from
  component_ids; Python correctly withheld the whole advisory. The extra unsafe
  output concern assumed missing enforcement despite the escaped read-only
  trainer preview and no unsafe executable consumer.
- Narrow v1 denied a prompt-injection path while describing unchanged visitor
  content reaching a model through a wrapper that does not reject instructions.
  Correct projected metadata did not establish a correct model conclusion.
- Both SOC outputs mapped Network Discovery without supplied discovery behavior
  and cited PowerShell guidance for packetcheck.exe. Ledger-on acknowledged that
  no PowerShell command was observed. Membership was not relevance.
- Both governance outputs described unknown retention implementation as lack and
  omitted EL-T37/P2/7-of-7 evidence. Off broadened external-sharing review into all
  sharing; on improved that wording but still lost one-rehearsal/7-draft approval.
- D4 changed only a generic conditional-decision rule, not gold/model decisions.
  Both rationales are exactly 400 characters and end mid-sentence in the raw JSON;
  no app truncation/repair occurred. A schema-bound generation effect is plausible,
  not proven as sole cause. Structural completion was not explanation quality.

Thinking-off selection followed the prospective operational fallback; no mode
gave a jointly faithful full-task pair. First default-positive includes cold load
8.84s. Output length, load/cache/order, stochasticity and tiny samples confound
performance claims. Thinking text was discarded; only sizes/hashes and aggregate
usage survive. A trustworthy per-channel token split is unavailable. Every attempt,
source/config/hash, latency/usage, full-fact judgment and counterexample is in
[lab_readout.json](model_task_diagnostic_v1/lab_readout.json).

## Experimental responsibilities and limits

DiagnosticBudget fsyncs reservations before the fixed-loopback send, parses bounded
NDJSON, requires final done, removes thinking and permits no retry. Socket connect/
idle/wall bounds are 10/90/360 seconds, campaign 3 hours, reply 256 KB, retention 12 MB. Actual retained
lab/campaign artifacts: **71 files, 486540 bytes**. Sixteen known finishes demonstrate
this campaign's accounting, not general provider stability. Historical Sprint 9
UNKNOWN remains unchanged. Current quiescence before new work used empty api/ps
plus no runner/eval/client, not health or elapsed time alone. Ollama was not stopped,
restarted or unloaded.

CampaignLedger enforces disjoint 16/12 and 28 aggregate; local phase caps 6/4/4/2 count
repairs too. Pending/UNKNOWN blocks further sends. Trials/artifacts are exclusive.
Evaluation disables retry/SDK fallback only process-locally; production paths stay
unchanged. Some original metrics show context-required=false for narrow/generic
tasks; actual wire flags/context are separately recorded and strict dispatch was
forced. Byte/token counts do not prove semantic context retention.

Narrow selection is bounded shortest-path traversal from a declared ingestion
surface to a model, stable tie order and <=4 edges, same rule for both graphs.
Python fixes category/path/endpoints/source; it does not choose the answer or read
gold. Both versions pass the complete original design. V2 appends a generic
decision rule and preserves v1. Validation labels prose unassessed; wrong text is
never converted to verified facts/actions.

One call covers one category/path question. An illustrative catalog capped at 24
flows x 6 categories could cost 144 calls, up to 14.4 hours at 360 seconds each; even that is not
exhaustive multihop coverage. No enumerator, ranking policy or multi-call production
pipeline was added. Replacing the broad workflow with one question would lose
coverage and is not justified here. Source membership, IDs and hashes are not
entailment, control verification, authority, authentication or anonymization.

## Acceptance and actual defaults

Aster files/order/rubric/imported run/runtime/accounting remain unchanged. Root
redirects and conservative one-send/umbrella hooks were mock tested with synthetic
rows; old Sprint 9 roots were not reused. Its frozen compact/ledgerON/default system
and thinking/context 8192/temp0.1/180s methodology cannot inherit lab settings.

**NOT RUN:** scheduled 12, submitted 0, raw 0, completed 0, NOT RUN 12, four per pillar.
No new acceptance root exists. Ledger fidelity failed, the latest full pair was
not viable, and narrow/off is methodologically incompatible. Forced ledger-on/
default-thinking would not validate the selected behavior. No competing acceptance
suite was created. See [acceptance_status.json](model_task_diagnostic_v1/acceptance_status.json).

Defaults remain Sprint 9: minimum model+distinct-flow reviewability, compact
candidate contract/graph gates, global instructions/provider-default thinking,
ledgerOFF and original retrieval/API/export/Inspector/correction/launcher behavior.
Streaming, token cap and explicit rules remain experimental, not product changes.

## Verification, handoff and next scope

Existing Windows CPython 3.13.1 environment. Final full pytest with -B and disabled
cache: **2227 passed, zero failed/skipped, one existing Starlette/httpx warning,
260.68s**. Focused committed checks: 83 passed; explicit-rule source/counter mocks: 78
passed; final original/narrow/runner selection: 36 passed; final preservation/case
checks: 10 passed in 10.48s. Ruff/pip/diff/protected
checks and exact pushed-SHA hosted CI are recorded in the final handoff/metadata.

Failure history: managed-sandbox temp access caused 22 passes/45 setup errors;
identical tests then passed 67/67 with access and no source fix. A mock phase-cap
test first observed a fifth D3 reservation, then passed after durable guards.
Three own snapshot expectations needed the new phase_counts field. Two rule tests
failed before the option existed and then passed. Scoped type/import/mock/Ruff
fixes changed no historical assertion, gold or observed outcome. Passing software
tests does not adjudicate semantic usefulness.

Reproduce software only: existing venv Python -B, PYTHONDONTWRITEBYTECODE=1,
pytest -q -p no:cacheprovider, Ruff --no-cache, pip check and git diff --check.
**Do not run more Sprint 10 lab inference: 16/16 is exhausted.** Failed acceptance
gates do not authorize an Aster invocation.

**USER WORKFLOW / FINAL VISUAL QA and independent semantic review remain PENDING.**
In a later authorized session use existing Development Start/Stop, all three
workflows, uncertain/benign inputs, exact source/version/field anchors,
correction-first exports and safe withholding. No GUI/manual acceptance occurred.
Exports remain unredacted. Next useful scope is independent review of these
preserved judgments, then a separately authorized held-out comparison of explicit
questions, complete explanations and compatible acceptance. An alternative-model
benchmark may clarify remaining capacity limits; no model was installed here.
