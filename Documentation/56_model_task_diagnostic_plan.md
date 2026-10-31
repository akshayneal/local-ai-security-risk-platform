# Sprint 10: model versus task diagnostic

Prospective development experiment, not a feature or release. Start from local/
origin Sprint 9 b6d84530b6eb9dccbb328a8dcffb0f9b532ef7ab on the existing new branch
`feature/model-task-grounding-diagnostic-sprint10`. Pre-interruption work is retained;
no Sprint 10 journal/reservation/result existed at resume. The earlier preflight
and new timestamped resume preflight are separate records.

## Question, controls and inference limits

Can installed Qwen carry out small grounded judgments more faithfully than the
current full compact task? Distinguish task burden, model fidelity, configuration,
runtime stability and inconclusive evidence; record counterevidence. Four new
synthetic Elm cases, facts and forbidden inferences are in the versioned case
catalog and rubric. No Aster input is used for development. This is authored,
correlated development evidence, neither blind nor independently adjudicated.

| Phase | Prospective comparison | Raw cap |
| --- | --- | ---: |
| D1 | Same positive/benign technical graphs, current compact task, provider-default/off/on thinking in that order | 6 |
| D2 | Same two graphs, full compact versus Python-preselected one-path/category question | 4 |
| D3 | Same fresh SOC and governance cases, ledger off/on only | 4 |
| D4 | One explicitly documented ambiguity/counterexample per invocation | 2 |
| A | Untouched, conditional Aster acceptance | 12 |

D totals at most 16, A at most 12, aggregate at most 28. No borrowing, warm-ups,
unrecorded probes, automatic transport/SDK retries or background generation.
SOC's original single repair remains; it consumes the same phase and global caps
and may leave later submissions NOT RUN. Every send is reserved/fsynced in local
and umbrella journals before provider work. Unknown/partial completion blocks all
new inference; health or elapsed time is not completion proof.

## Fixed lab runtime and controlled seams

Existing qwen3:8b Q4_K_M digest
500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41,
Ollama 0.40.13, temperature 0.1, num_ctx 8192, num_predict 1280 for every arm;
other installed sampling parameters unchanged, no seed. Only top-level `think`
changes in D1. Default omits the key; off/true send explicit false/true.

The lab alone uses schema-constrained NDJSON streaming, truncate=false/shift=false,
360-second wall deadline applied at socket send/read, 10-second connect and
90-second idle bounds, persisted three-hour campaign deadline. Provider output
must include done=true and stop/length. Length is known completion but withheld,
not semantic success; incomplete/timeout/invalid framing is UNKNOWN and stops.
Thinking and answer tokens share the finite generation budget, which can mask
capability. The 1280-token cap leaves typical streaming-frame overhead under the
independent 256 KB wire ceiling; that ceiling remains enforced without fallback.
Retained D artifacts <=12 MB, synthetic only, screened before exclusive writes.
Thinking text is discarded; only presence/size/hash and aggregate usage survive.

Read-only local show/version/tags confirmed the fixed runtime and thinking
capability. Official versioned [ChatRequest fields](https://github.com/ollama/ollama/blob/v0.40.13/api/types.go)
and [chat handler](https://github.com/ollama/ollama/blob/v0.40.13/server/routes.go)
document concurrent stream/format/think and num_predict. Actual stream completion
is tested with mocks before D1; the first planned call is not a hidden probe.

The actual app analyzer/internal contracts run in-process. The evaluation patches
only its provider dispatch to the counted stream and calls the existing generation
function without its retry decorator. SDK fallback is refused. Strict dispatch is
explicit for generic SOC/governance too. Public API/default provider behavior is
unchanged; live analyzer returns are not claimed to be exercised HTTP responses.

## Selection, judgment and promotion

D1 mode selection for D2/D3: prefer a mode completing both graphs; then fewer
disqualifying inventions/material contradictions under the unchanged authored
rubric; then more complete facts; then lower answer/generation latency. If no mode
completes both, use explicit off for a bounded task diagnostic and report that
selection as operational, not a semantic winner. Repeated full-task D2 controls
remain fresh lab attempts, not independent samples. Load/cache/order are latency
confounds; report provider load/prefill/eval durations separately when available.

Each full fact is RETAINED/PARTIAL/OMITTED/CONTRADICTED/UNASSESSABLE with reason.
Separate raw model retention from app-projected identity, purpose or selected
path. D2 reports all six facts plus the four selected-path facts per graph; omissions
outside one path remain visible. Python selection is graph traversal, not a risk
verdict: both controls get the same prompt-injection category rule, <=4 real edges
and one applicable guidance card. One call covers one question only. Exhaustive
coverage would need bounded additional calls and a separate design/cost decision;
no automatic multi-call production workflow is introduced.

Only the latest positive+benign comparison can support promotion: justified
path-bound positive, no invented path/category, benign no fabricated risk/material
contradiction, no authority/action grant, compatible contract and deterministic
regressions. Ledger activation additionally needs faithful paired SOC/governance
states/numbers/scope. Otherwise defaults stay as Sprint 9 and Aster NOT RUN.

## Isolation and acceptance

Fresh D: knowledge_base/workspaces/elm-sprint10-lab/accounting/.
Umbrella: elm-sprint10-campaign/. Conditional A: elm-sprint10-acceptance/.
Existing Cedar/Maple/Birch/Northstar roots are never resumed, queried or written.
Every trial directory and artifact is exclusive; journals append only. Protected
sets and exact current source scope are in sprint10_preservation.json.

Aster's frozen files, imported run function, original model path, order, compact
protocol, ledger ON, default system instructions/provider thinking, temperature
0.1, context8192 and 180-second timeout remain untouched. Process-local root
redirects and conservative one-send-per-case/umbrella guards are mock tested.
Lab streaming/token/mode choices cannot leak into Aster. If product defaults or
selected narrow method are incompatible, record 0/12 NOT RUN. Commit the selected
implementation before any acceptance; no tuning after viewing its outcomes.

Current quiescence is established from empty api/ps, no connected generation
client, and no runner/evaluation process; historical Sprint 9 completion remains
UNKNOWN. Recheck before first live call. A new uncertain request stops the sprint;
never restart/kill the service to recover it.

## Handoff and defaults

Initial defaults remain compact app-owned coverage/graph gates, global instructions,
provider-default thinking, ledger OFF. All new helpers are inert/evaluation-only
unless an evidence-supported change is separately committed within this sprint.
Preserve every result, checkpoint/source hash and unused quota. Finish focused/full
Windows tests, Ruff/pip/diff/protection checks and exact-final-SHA feature CI. No
main/tag/PR/release/launcher/dependency change. Release remains NO-GO pending broader
independent review and USER WORKFLOW / FINAL VISUAL QA.
