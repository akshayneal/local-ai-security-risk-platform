# Sprint 15 continuation: analyst utility and request reliability

**Experimental, unmerged, default off. RELEASE NO-GO.** Independent human review:
**0 verified**. **USER VISUAL QA PENDING.** New local model and embedding sends:
**0**. No model quality, hardware offload or inference latency was measured.

Starting branch `feature/native-evidence-workflow-sprint15` at
`9be773070f2176d40e3e80beccf65feaefdc03c0` matched the live origin ref; exact
[baseline CI](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/42349043310)
was independently rechecked as successful. Work is on
`feature/sprint15-analyst-utility-and-request-lifecycle`, created from that tip.
No main/tag/release/PR or launcher changes are authorized by this continuation.
Git records full milestone identities: plan `c5e9e52`, A `d44b59d`, B/review
enablement `b9aa94e`, A review hardening `64aa314`.

## What the analyst can do

Select **Native Evidence Investigation** on the existing experimental native page,
load the fictional network sample, choose row 0 and an investigation question,
then explicitly build. The versioned API constructs a deterministic snapshot
without Ollama. The UI groups reported time/labels, device, process, account and
local/remote endpoints before expandable original/normalized/type/path details.
It separates observations, representation comparisons, insufficient evidence,
suggested evidence questions and the uncollected analyst-notes status.

The two sample rows reuse a PID but have different creation times. Their literal
differences remain visible without becoming a process join. An incomplete third
row cannot hide a known difference between valid rows; absent/invalid comparison
coverage remains explicit. Missing selected fields cannot be borrowed from another
row. Application access calls for application/server corroboration; blocking
calls for relevant protection disposition and association context; permission
calls for separately controlled reviewed current authority. No source was queried
and no action or authorization comparison occurred.

The client and page reconstruct every response against the exact current source,
selection and question, including both exports. Changing any input removes old
downloads until another explicit Build; refresh/download never submits again.
UTF-8 source text round-trips original BOM/CRLF bytes; CSV strings, leading zeros,
unknown fields and duplicate rows remain in the embedded original observation.
Markdown escapes source text and includes the original observation appendix.
See [sample exports](sprint15_continuation/examples/investigation.md) and the
[user-only walkthrough](sprint15_continuation/manual_qa.md).

| Capability / claim | Status and evidence boundary |
| --- | --- |
| Original native observation route and default view | Existing experimental v1 retained |
| Investigation companion API/UI/JSON/Markdown | Implemented experimental opt-in; deterministic, zero inference |
| Shape validation / normalized fields | Representation checks only; original values remain authoritative input |
| Cross-row comparison | Literal/type differences only; no causal join or conflict about a real event |
| Application access, transfer, control outcome, threat detection | Insufficient evidence; not implemented as native predicates |
| Policy authorization comparison | Not executed; uploaded approval cannot create authority |
| Independent review and visual QA | Materials prepared; actual review pending |

## Why native semantics remain unqualified

The [field-to-meaning matrix](sprint15_continuation/native_semantics.md) records
official source URLs, displayed revisions, layers, counterexamples and needed
corroboration. Two hypotheses were considered: mapping ConnectionSuccess to
completion, and using network-protection disposition records. Microsoft's
[network-protection guidance](https://learn.microsoft.com/en-us/defender-endpoint/network-protection#network-protection-and-the-tcp-three-way-handshake)
explicitly allows ConnectionSuccess before later blocking. Detailed ActionType
definitions remain delegated to the portal; ResultType is not defined in the
public network-table columns. DeviceEvents disposition records are outside the
accepted upload profile and have no association contract here.

Decision: **MORE_EVIDENCE_REQUIRED**. No new native completion, access, protection
or authorization predicate was justified. `native_semantics_unverified`, comparator
`not_executed`/0, association `not_assessed` and relationship `unassessable` remain.
This is a useful observation/investigation aid, not a qualified threat detector.

## Inference lifecycle safety subset

The separate `app.lifecycle_api:app` composition adds versioned SOC/governance
routes only with `ENABLE_INFERENCE_LIFECYCLE=1`. It calls the unchanged original
analyzers, Inspector and audit functions inside a request-local execution context.
A small Ollama hook selects the bounded transport only inside that context;
historical runners and ordinary SDK/HTTP behavior remain unchanged. The UI opt-in
applies to generic SOC and AI System Risk; Microsoft upload and AI Security UI
remain explicitly legacy.

The default cooperative analysis budget is **900 seconds**, provider connect
limit **5 seconds**, read inactivity limit at most remaining budget, and UI margin
**30 seconds** (930-second read wait). Configuration is local-process-owned,
validated and never granted by an input request. Monotonic checks cover preflight,
dispatch, any repair, response reads/decoding and final validation/serialization.
Requests timeouts cannot enforce a hard elapsed stop or cancel provider work.

The active path makes no automatic retry after an uncertain dispatch. It permits
at most **2 SOC generation POST attempts** (initial plus the existing completed-
output repair), or **1 governance attempt**. A preflight GET is not inference.
Legacy maxima remain SOC **4**, governance/AI Security **2** because transport
retry and SOC repair are separate loops. The SDK default still has no explicit
timeout; the lifecycle generic mode deliberately uses bounded HTTP instead.
All new and historical actual live-send counts for this sprint are **0**.

Client-generated UUIDs identify attempts; the 64-entry single-process registry
stores only status metadata and suppresses duplicate retained IDs. It retains
running/unknown entries and fails closed if they fill capacity. Completed results
are not stored/recoverable. Eviction, another worker or restart loses suppression;
missing status is never proof of no dispatch. The UI shows an ID before waiting
and retains an uncertain-attempt guard through script reruns in the same active
session. Full reload/new session can lose it. Status lookup never resubmits;
explicit acknowledgment permits a fresh request but cancels nothing.
See [causal review and exact contracts](sprint15_continuation/inference_lifecycle.md).

## Validation, preservation and review

The [prospective plan](70_sprint15_continuation_plan.md) defines the acceptance
properties before checks. Ordinary deterministic software and mocked lifecycle
tests suffice; **no new scored diagnostic was necessary**. These tests and agent
reviews are implementation-authored checks, not independent semantic validation.
Original Sprint 14 N2A6 **11/12**, Sprint 14B **10/10**, the 60-output Sprint 13
masked packet/key and all earlier outcomes stay unchanged. Historical diagnostics
and live evaluations were not rerun.

The immediate historical live-scope assertion receives only one import/decorator
and executes its unchanged body at immutable `9be7730`. New negative tests mutate
real protected source in isolated temporary archives and verify rejection. A new
exact-path guard protects prior tracked blobs beyond the named continuation edits;
it cannot exempt old files through the new-file list. The original raw-artifact
guard remains unchanged. This is a narrowly explained scope migration required by
the requested continuation, not relaxed evaluation expectations.

All 405 inherited untracked files remain outside Git. The starting temporary
hash inventory also covers 452 ignored non-venv/non-bytecode files (a broader
cache/private scope than the earlier 185-file subset). No unrelated process,
workspace, registry, environment, service, package or launcher was changed.
The [reviewer guide](sprint15_continuation/reviewer_guide.md) and separate
[blank form](sprint15_continuation/reviewer_form.md) bind authentic future findings
to exact artifacts while leaving every identity, judgment and signoff blank.

## Concepts and residual limits

A deterministic rule gives the same output for the same input; it does not make
an unsupported vendor meaning true. Strict types prevent Python's `True == 1`
from merging distinct source representations. Field paths explain where a value
comes from; a hash detects changed bytes but authenticates neither source nor
reviewer. Suggested evidence is a question for a person, never a checked source
or permission to act.

Ranked next work: (1) genuine analyst usefulness/semantic review and user visual
QA of this integrated slice, preserving disagreements; (2) a separately controlled
source/currentness and proven association contract before any real authorization
comparison; (3) evaluate whether persistent lifecycle result recovery is needed,
with explicit privacy/retention bounds; (4) only then consider a small prospective
vendor predicate with applicable schema evidence and counterexamples. Model change,
release, broad joins and new integrations are outside this sprint.

| Remaining risk | Practical limit / follow-up |
| --- | --- |
| Native meaning and authenticity | No completion/threat/permission inference; obtain applicable schema and independent corroboration |
| Collection and association | Bounded supplied bundle only; no causal joins or absence-of-event conclusion |
| Long provider waits | Cooperative checks withhold late output; no cancellation or strict wall-clock interruption |
| Lost replies / duplicate requests | Metadata lookup and local guard only; no persistent result recovery or cross-session guarantee |
| Registry saturation | Unresolved running/unknown entries are never silently evicted; investigate actual work before user process management |
| Human usefulness / presentation | Authored tests and agent review are insufficient; authentic review and visual QA remain pending |

Final validation counts and exact source identity are recorded below and in the
adjacent [validation record](sprint15_continuation/validation.json). The final
handoff reports the exact pushed feature SHA, origin equality and its CI URL.

## Final local validation

CPython **3.13.1**, existing Windows virtual environment. Final implementation
source: `fb111d7bb9b8f3245c236eecdcd29134db720bb8`; subsequent handoff changes
contain documentation/logs only. **3,210 passed, 1 inherited warning, 385.22s**
with `python -B -m pytest -q`. All **346 tracked Python files** pass Ruff;
`python -B -m pip check` reports no broken requirements; full-feature
`git diff --check 9be773070f2176d40e3e80beccf65feaefdc03c0` passes.
The remaining warning is Starlette's inherited TestClient/httpx deprecation;
no package was installed or upgraded to suppress it.

Focused gates: 181 combined native tests before review polish; 45 native tests
after the final export fix; 14 preservation tests; 279 early and 282 final
backend/required legacy seam tests (58 final new backend cases); 92 dashboard/native
regressions before final UI polish and 30 final lifecycle dashboard cases.
New authored cases total 140;
the reported early baseline was 3,070. These are software checks, not accuracy.

The initial full run at `3efc852` also passed 3,207 tests in 364.89s. Its log is
preserved separately. The full-feature whitespace check then exposed an extra
blank line at the end of the new generated Markdown example; `610ff40` normalizes
the exporter ending and updates that example. Focused checks and the full suite
were repeated against the corrected source (3,207 passed in 356.85s).
All three complete local logs are retained, including the final interruption fix.
Earlier focused harness issues were also corrected: Windows pytest auto-generated
an oversized fixture filename (explicit test IDs fixed it), and AppTest exposed
a stale widget after a release rerun (a guarded pre-render callback fixed it).
No frozen expectation, case denominator or historical result was changed.

The first pushed head `7c62379` failed hosted CI
[42413016721](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/42413016721):
2 failed, 3167 passed, 38 skipped. Hosted Python 3.13.18 / Streamlit 1.67.0 differs
from local Python 3.13.1 / Streamlit 1.58.0. Both failures were the new test helper
accessing removed `AppTest.session_state.filtered_state`; public mapping membership
keeps the stronger guard-key-absence assertion. No package or product behavior
changed for this compatibility fix. The failure metadata remains committed;
hosted missing-artifact skips do not establish local raw-file preservation.

Final causal review also exposed a real interruption retry defect: Tenacity catches
BaseException, and two synthetic interruption tests each observed two mocked POSTs
before the fix. `fb111d7` gates every retry off within an active lifecycle context
while preserving the exact legacy predicate outside it. Three new tests verify
one dispatch plus original interruption propagation and legacy compatibility.
The pre-fix regression outcome (2 failed) and the after-fix focused outcome
(282 passed) are retained in the validation record. No OS signal or model send
was used. The complete 3,210-case final run validates both corrections.

All 990 local historical raw files were verified, with no absent groups. Hash-only
starting inventories confirm all 405 inherited untracked and 452 ignored files
unchanged. The final guard protects **823/829** baseline tracked blobs; the only
existing changed paths are native API, native client/page, the context-only Ollama
hook, generic SOC/governance workspace hook and immediate scope-test migration.
The original API client, main, analyzers, launchers, main branch and v2.3.0 tag
remain unchanged. Main/tag still resolve to `fde00d0ca5d21eecbc6973cc784550ed453edb7a`.

Read the validation record for the exact changed-file inventory and commands.
Final exact-push CI is checked after the handoff commit rather than claimed from
an earlier code SHA. No new scored diagnostic or live runtime smoke was run;
independent human review remains zero verified and visual QA remains pending.
