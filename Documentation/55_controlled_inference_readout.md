# Sprint 9 controlled inference readout

**RELEASE CANDIDATE: NO-GO.** This unmerged experimental sprint changes who owns
coverage decisions and adds precise graph checks. Six journaled development
requests exposed continued semantic errors; the sixth timed out with provider
completion unknown. The stop rule prohibited further inference. Final acceptance
is **NOT RUN (0/12 submitted, zero raw attempts)**. No release, independent
validation, model safety or completed user workflow/visual review is claimed.

## Executive synopsis

Python now decides whether a declared AI graph has a model connected to a distinct
component by a directed flow. For reviewable graphs, Qwen proposes findings, gaps
and review steps rather than choosing insufficiency. The public API stays the
same. Zero findings remain valid and do not certify safety. After the lab exposed
unsupported categories, the compact contract was tightened to require real flow
references and necessary category-specific graph support. Those later checks have
software coverage only; they were not live evaluated.

The old contract returned false insufficiency on both development designs. The
compact/global pair returned both advisories but still failed semantic usefulness:
the risky response added unsupported categories and the benign response described
supplied components as absent. Narrow instructions worsened the risky output and
the benign request timed out. Global instructions are again the default. The
bounded SOC/governance evidence ledger is implemented but off by default because
its live comparison could not run. Further experiments need a separately authorized
run, not a retry of this stopped journal or a replacement acceptance suite.

## Engineering appendix: identity, checkpoints and preservation

Start branch `feature/reliability-fidelity-sprint8`, local and live origin equal:
`f85e67fbd224fa020d0d904b62b6f8d7fd0b5e24`. Work branch:
`feature/controlled-inference-fidelity-sprint9` (absent locally/remotely at Gate 0).
Main and peeled v2.3.0 remain
`fde00d0ca5d21eecbc6973cc784550ed453edb7a`; no merge, tag, release or PR.

| Checkpoint | Purpose |
| --- | --- |
| `1480892720bca305e48cbbc52908c80ff3cf9e3e` | Commit sealed acceptance inputs/rubric/runner/accounting contract and separate adaptive lab before application edits or generation. Literal staged and working hashes verified. |
| `1c421c08815060c746576b457e3d60351868a949` | Compact generation, structural reviewability, controlled instructions, ledger, counted transports and compatible historical replay. All six actual requests used this exact implementation and recorded source hashes. |
| `20945f2521d60253f3ea3207f7a4b8f47d11cd18` | Post-stop flow/category checks, complete attributed purpose summary, global default restored, ledger default off. No model call used this implementation. |
| Final audit commit | This report, exact inventory and screened machine readouts. Its exact final SHA, origin equality and exact-SHA Actions link/counts are supplied in the final handoff; a report cannot name its own containing commit. |

Gate 0 recorded branch/upstream/diffs, ignored/untracked inventory fingerprints,
journals/processes, Python identity and protected hashes before writes. No tracked
or staged changes and no inherited evaluation process were present. The known
405 untracked files remain visible. All 590 s4check files (405 historical plus 185
caches), 13 Northstar files, 36 Cedar7 artifacts, 14 Maple8 artifacts and installed
AGENTS bytes matched before work and remain protected. No s4check code was imported
or executed; Northstar database/WAL/SHM were hashed as bytes, never queried.

No existing launcher, shortcut, port, service, package, model, environment file,
secret, retrieval default, historical result/scorer or framework card changed.
Shared Ollama was neither stopped nor restarted after timeout. Exact paths and
base blobs are guarded in [sprint9_preservation.json](sprint9_preservation.json);
[change_inventory.json](controlled_inference_v1/change_inventory.json) lists actual
changes. [preflight.json](controlled_inference_v1/preflight.json) records Gate 0.

## What the code determines

- **Structural coverage:** a validated request needs a model and a non-self flow
  incident to it. Missing structure returns safe insufficiency/gaps with no model.
  This is a minimum review path, not complete architecture coverage.
- **Model proposals:** the internal three-field contract contains findings, gaps
  and human review. Python owns public case identity, coverage and summary, and
  assembles the envelope only after raw schema/reference checks. Invalid proposals
  are withheld; findings are never silently dropped or relabeled as verified.
- **Graph scope:** compact findings require a real directed flow and both cited
  endpoints. Necessary category support comes from declared model input/output
  paths, connected retrieval stores/tools and explicit nonpublic flow labels.
  Multihop paths are supported. Tool/invoker paths bound authorization coverage;
  a general authorization matrix remains unassessed. These checks can rule out
  missing declared prerequisites, not establish semantic truth or actual risk.
- **Known context:** the app summary retains the complete attributed purpose
  field and typed inventory counts within the existing 1,200-character contract.
  It does not parse prose, dump the request or silently truncate evidence.
- **Experimental ledger:** immutable field/row pointers, exact bounded values,
  roles, request hashes and case scope; 64 entries, 1,024 characters per value,
  24 KB summed entries and explicit omitted counts/first 16 omitted paths. The
  original input remains unchanged. It distinguishes supplied/default-field
  unknown, but does not classify prose as absent/implemented/approved. Internal
  `evidence_ledger_mode(True)` is required; default legacy prompts stay unchanged.

Supplied input, retrieved text and model prose remain untrusted. No body text can
grant authority/access. Fixed `candidate`, `not_verified` and `no_actions_executed`
labels and identity checks do not verify arbitrary prose about controls, actions
or citation support. The app has no action tools. Source membership is not
entailment; hashes correlate artifacts and are not authentication/anonymization.
Public shapes, original endpoints, SOC case routing and one-repair limit,
retrieval eligibility, Inspector/correction lineage and exports remain compatible.
AI Security retains six versioned local guidance sources and read-only provenance;
it gains no organizational workspace access or correction editing.

## Hypotheses and actual development evidence

All six requests used the same committed code, Qwen digest, temperature 0.1,
num_ctx 8192, provider-default thinking and two authored Birch graphs. Lab inputs
were deliberately distinct from Aster acceptance and older Cedar/Maple. Review
caught draft overlap before any generation; only mutable lab examples were replaced.

| Hypothesis | Baseline / intervention; actual calls | Supported observation and decision | Limits |
| --- | --- | --- | --- |
| H1 | Coverage union/global: 2; compact/global: 2 | False insufficiency 2/2 baseline versus 0/2 compact returns; compact positive had a plausible retrieval core, but two unsupported categories. Benign had zero findings but false component-absence wording. Retain app-owned coverage, no usefulness pass. | Two repeated authored graphs, not independent samples or a reliability estimate. |
| H2 | Ledger off/on SOC/governance comparison: 0/0 | NOT RUN after timeout stop. Keep ledger internal and off by default. | Deterministic preservation tests only; no live polarity/scope improvement shown. |
| H3 | Compact/global: 2; same compact/narrow: 2 | Narrow risky response invented confidential data and downstream consumption; narrow benign timed out. Abandon automatic narrow selection. | Narrow pair has one response and one unknown timeout. Optional explicit think comparison NOT RUN. |
| H4 | Post-stop flow/category intervention: 0 live calls | New synthetic failures reproduced missing-flow, disconnected/borrowed-path and public/unknown disclosure issues; graph/decoder checks now reject them. | Software proof of necessary structural scope only, no live validation or general prose entailment. |

The original lab cap remains 24, final cap 12, global cap 36. Six raw requests
were reserved and fsynced before sending; five provider responses and five valid
HTTP 200 advisories returned. Request 6 raised ReadTimeout; API safely withheld
HTTP 422. An application retry was attempted in code but denied before a second
raw send. Its two metrics entries are not two provider requests. No warm-up,
parallel generation, SDK-hidden request, selective rerun or acceptance request.

| Authored development denominator | Positive graph | Benign graph | Total |
| --- | --- | --- | --- |
| Submissions / raw attempts | 3 / 3 | 3 / 3 | 6 / 6 |
| Provider returned / unknown timeout | 3 / 0 | 2 / 1 | 5 / 1 |
| API returned / withheld | 3 / 0 | 2 / 1 | 5 / 1 |
| False insufficiency among returned | 1 | 1 | 2 |
| Strict useful advisory | 0 | 0 | 0 |

All six are AI Security development submissions; SOC and AI System Risk have
zero submitted/returned live lab cases. Repeated graphs are not fresh independent
cases. The 18 prewritten complete expected facts yield 15 assessable: 0 fully
retained, 14 omitted, 1 contradicted; 3 unassessable after timeout. Conditional
retrieval fragments survive in compact outputs, but complete path facts including
literal flow references do not. Fragments and plausible candidate cores are
reported separately, not counted as full facts. There were seven returned finding
citations with allowed identity/category membership; four entire candidate-category
occurrences lacked applicable case support. Membership did not establish relevance.
These are implementation-author judgments, with auxiliary agent review, not
independent human adjudication. No population accuracy/safety percentage is inferred.

The complete attempt ledger, prompt/schema/input/source/config fingerprints,
provider usage/timing, bounded excerpts, review reasons and artifact identities
are in [lab_readout.json](controlled_inference_v1/lab_readout.json).
[decision_log.md](controlled_inference_v1/decision_log.md) retains failed approaches
and competing explanations. Full synthetic responses remain only under the fresh
ignored `knowledge_base/workspaces/cedar-sprint9-lab/` root; hidden thinking text
was removed before storage, retaining only presence/size and raw-response hashes.

Ollama read-only preflight verified 0.40.13, existing qwen3:8b Q4_K_M digest
`500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
Actual `/api/show` reports thinking capability; no explicit mode probe occurred.
Loopback only, proxy/redirect/cloud fallback denied, complete-context request flags
truncate=false/shift=false. Exact bounded byte counts are not token counts or
proof full context was retained. The lab explicitly selects the existing strict
HTTP route for every workflow; ordinary SDK sends missing strict flags are refused.
Normal generic legacy SDK behavior stays unchanged outside this experimental seam.

Reservations and completions share a durable, locked journal across both intercepted
stacks. A timeout or incomplete reservation blocks future calls across invocations.
The 180-second network timeout is per blocking operation, not a hard end-to-end
deadline or proof cancellation. A persisted four-hour deadline prevents new
requests with less than 180 seconds left. Replies are bounded to 256 KB, total
retention to 12 MB; final raw/review retention was 85,890 bytes across 18 files.
No further generation was used to diagnose or recover the uncertain provider call.

## Sealed acceptance

The separate 12-case Aster suite, rubric, plan and small acceptance runner were
committed at 1480892720bca305e48cbbc52908c80ff3cf9e3e before all lab calls. Five
literal frozen files are verified against working and committed Git bytes, with
suite-local LF attributes and a committed-versus-working regression. No case,
expected fact, rubric, source identity or final runner changed after freeze.
Shared mutable engineering transport remains governed by its frozen accounting
contract. The suite is authored prospectively by the implementer, not blind or
independent.

**NOT RUN:** 12 scheduled, 0 submitted, 0 raw attempts, 0 provider/API returns,
12 NOT RUN. Four per pillar; technical controls 2 positive/1 negative/1 ambiguous,
SOC 1 positive/2 negative/1 ambiguous, AI-risk 1 positive/2 negative/1 ambiguous.
All final usefulness/fidelity/source metrics are unassessable, never passes.
No acceptance output root exists. Eighteen unused lab requests and twelve reserved
final requests remain unused and cannot be borrowed or retried after the stop.
See [acceptance_readout.json](controlled_inference_v1/acceptance_readout.json).

## Deterministic verification and failure history

Existing Windows CPython 3.13.1 AMD64 `.venv` used throughout, Python `-B`,
PYTHONDONTWRITEBYTECODE=1, pytest cache disabled, Ruff --no-cache. No packages
were installed/upgraded. The pre-existing Starlette/httpx deprecation warning
remains; no warning suppression or dependency change was made.

| Check | Actual result |
| --- | --- |
| Starting focused baseline | 56 passed, 1 warning, 8.56 s |
| H1 initial TDD | 8 failed / 26 passed before implementation |
| H2 initial TDD | Missing helper collection error; then current field/compatibility checks pass |
| Initial current + historical focused | 127 passed, 1 warning, 93.00 s |
| Expanded transport/accounting | 30 passed, no provider calls; fake SDK/HTTP exhaustion, actual app retry/SOC repair, timeout/incomplete journal, redaction, model/URL/options and LF checks |
| First full diagnostic | 2101 passed / 1 failed, 1 warning, 233.75 s; historical client-byte guard, migrated without changing its assertion |
| Additional historical/negative checks | 6 passed, 17.91 s; actual archived client mutation rejected by both original guards |
| Post-lab H4 TDD | 16 failed / 41 passed before graph/summary intervention |
| Latest AI Security contracts/hardening/current API/UI | 117 passed, 1 warning, 5.93 s |
| Latest ledger/semantic/retrieval/UI/Microsoft compatibility | 239 passed, 1 warning; ledger isolation 17 passed after lint cleanup |
| Final full Windows suite | 2139 passed, 0 failed/skipped, 1 existing warning, 234.48 s |
| Final current scope / frozen suite / accounting | 35 passed, 13.50 s; protected inherited bytes and committed literal freeze verified |
| Final Ruff / pip check / git diff --check | PASS; no broken requirements; PASS |
| Final pushed-SHA Actions | Exact SHA/link, actual hosted counts/skips and conclusion in final handoff |

Earlier mistakes remain recorded: new negative test initially mutated an old
authorized source and therefore did not fail the old guard; corrected only the
new test target. Initial evaluation tests exposed duplicate draft lab input and
an incorrect mock redirect assumption; fixed before generation. The separate
transport audit caught malformed thinking-marker, journal/deadline, unbounded
metadata-read and returned-model checks before first live use. Own UI tests had
over-specific display assertions, corrected to actual metadata. None changed old
gold, raw outcomes, judgments or official denominators to manufacture success.

Historical tests whose pinned source/protocol legitimately changed run their
unchanged original assertions at the immutable Sprint 8 endpoint using a bounded
tracked-only Git archive and scratch index. AST comparisons retain all original
bodies/assertions; actual archive mutation negatives still fail. A new active
Sprint 9 guard checks exact allowed paths and every other baseline blob. Frozen
V1–V3.2/retrieval/Microsoft/SOC/corrections/Sprint5–8 artifacts remain unchanged.
No new historical live run, official comparison or historical model replay occurred;
offline replay assertions in test suites are software checks, not fresh model data.

Reproduction of software checks only:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B -m ruff check --no-cache .
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
```

Do not rerun the live runner: its unknown-timeout journal intentionally refuses
further generation. Keep the failed output and unused acceptance suite intact.

## User-only QA and next scope

**USER WORKFLOW / FINAL VISUAL QA PENDING.** No agent GUI/browser/shortcut or
manual workflow acceptance occurred. In a separately authorized manual session:

1. Use existing Development Stop then Start shortcuts; verify feature branch/SHA
   and all three workflow entries. Repeated Start should reuse owned services;
   Stop must preserve shared Ollama. Use the development launcher, not release demo.
2. Compare synthetic suspicious, legitimate and context-poor SOC records. Check
   exact identities/endpoints, completed versus attempted operations, uncertainty
   and conditional proposed actions.
3. Compare unknown, explicitly absent and reported-implemented AI controls,
   quantitative evidence and narrow human-review/approval scope.
4. Compare risky, benign and incomplete AI graphs, real flow-bound candidates,
   appropriate zero findings and no-model insufficiency; all remain unverified.
5. Inspect original SOC/risk source versions/field anchors, record judgments and
   corrections, then compare correction-first JSON/Markdown and revision history.
   AI Security stays read-only and does not gain correction or workspace access.
6. Check safe withholding, export escaping/binding and sharing notices. The summary
   may contain the complete caller-supplied purpose; exports are not redacted.

The next useful scope is a newly preregistered bounded evaluation of the post-stop
graph gates and a separately isolated evidence-ledger comparison, with runtime
timeout behavior addressed prospectively. Preserve this blocked journal and sealed
suite; do not recover the result with extra prompting or relabel software checks
as semantic acceptance. Broader independent review and user QA remain blockers.
