# Sprint 9 engineering decisions

This is an authored development record. Lab repeats are diagnostic observations,
not acceptance evidence or independent samples. Entries are appended, retaining
failed interventions and alternative explanations.

## Before generation

- Gate 0: exact local/remote Sprint 8 SHA confirmed; no tracked/staged change or
  active evaluation. All protected sets matched (590/13/36/14 and AGENTS). The
  405 inherited untracked files remain visible. Existing shared Ollama unchanged.
- Focused baseline: 56 passed, one existing warning, 8.56 seconds. No provider.
- H1 TDD: 8 failed / 26 passed before implementation (2.93 seconds, existing
  warning). Failures cover compact positive/benign responses, non-reviewable
  graph paths, hostile declaration behavior and missing controlled contexts.
- H2 TDD: collection fails because app.evidence_ledger does not yet exist. No
  model request and no old evidence alteration. Tests explicitly reject body
  authority and preserve exact quantitative/scoped fields without NLP inference.
- Read-only provider preflight: Ollama 0.40.13, exact installed qwen3:8b digest;
  show capabilities include thinking. No thinking behavior has yet been tested.
- Architecture decision: preserve public envelopes and audit/Inspector identities;
  use an internal candidate-only generation contract and an exact supplied-field
  ledger. A ledger assertion remains supplied and externally unverified.
- Competing explanation: broad instructions/decoder workload may cause semantic
  failures independently of reviewability. The lab will distinguish the complete
  architecture contrast from isolated system-instruction/thinking contrasts.
- Preserve existing SOC endpoint identity normalization; do not add an analyzer
  rejection that would break vendor-versus-case ID compatibility.

## Pre-live implementation and audit

- Before any generation, source review caught two initial lab graphs sharing
  acceptance graph text. Replaced only mutable lab inputs: unreviewed Markdown
  retrieval and fixed-label display, with distinct components/functions. The
  sealed acceptance bytes remain unchanged. This correction used no outcomes.
- H1 current contract/hardening batch: 91 passed. Current compact API/UI cases:
  4 passed. H2 compatibility/semantic/Microsoft batch: 236 passed. Focused current
  and historical migration batch: 127 passed. Existing Starlette warning retained.
- Accounting first passed 19 checks, then a separate audit found malformed
  thinking-marker, journal-header/deadline, metadata-read and response-model
  validation gaps. Fixed these before live use; expanded accounting tests: 30
  passed. No actual provider request occurred in these tests. Fake provider retry
  plus SOC repair jointly reserved exactly four synthetic test attempts.
- First full diagnostic run: 2101 passed / 1 failed, one existing warning,
  233.75 seconds. The old grounding source-byte guard pins ollama_client, now
  legitimately changed to select trusted workflow instructions. Add only its
  immutable-Sprint8 replay decorator, preserve all original assertions via AST,
  and test actual archived-client mutation rejection. No old allowlist or historic
  evidence/scorer is broadened. Final full verification will follow lab work.
- Initial scope-negative test mistakenly mutated an old-authorized analyzer and
  correctly did not fail its old guard (13 passed / 1 failed). Corrected the new
  test to mutate the old-protected client; no guard assertion was changed.
- The proposed ledger is an exact input projection and prompt intervention.
  No general control-polarity or citation-entailment validator is claimed.

## Adaptive lab: six actual raw requests

All calls used implementation 1c421c08815060c746576b457e3d60351868a949,
the frozen model/digest/options, identical paired Birch inputs, no ledger and
provider-default thinking. The shared journal records actual wire/source hashes.

| Attempts | Contrast | Observations | Decision |
| --- | --- | --- | --- |
| 1–2 | Existing coverage union + global instructions | Both graphs returned false insufficiency, zero findings; supplied classification and tested-control state were misstated. | Replace model-owned coverage, retain failures. |
| 3–4 | Compact contract + same global instructions | Both returned advisory; risky case had one plausible retrieval core and two unsupported categories; benign zero findings but false component-absence wording. | Retain structural coverage architecture, reject semantic viability. |
| 5–6 | Same compact contract + narrow instructions | Risky output added public-to-confidential and downstream-consumer inventions; benign request timed out at about 181 seconds. | Abandon automatic narrow instructions; unknown timeout stops all further inference. |

Attempt 6 reserved before send. A requests ReadTimeout left provider completion
unknown. The application's retry entered generation code but the shared budget
refused transport before another raw request: six reservations total, five provider
responses, five HTTP 200 advisories, one withheld HTTP 422, zero final attempts.
Timeout is not proof cancellation; shared Ollama was not stopped/restarted/queried
to force recovery. The journal remains blocked; no new trials or warm-ups occurred.

These repeated two-case observations are development evidence only. No authored
output met the predeclared strict usefulness criterion. No acceptance case was
submitted. H2's SOC/governance comparison and optional thinking ablation are NOT
RUN. Source membership passed for returned citations but did not establish their
applicability. Complete expected facts are judged separately from retained semantic
fragments; empty flow references fail the complete graph-path requirement.

## Post-stop software intervention; no live validation

- TDD: 16 failed / 41 passed for flow/category gates and attributed complete
  purpose retention. Internal findings now require a real flow; schema and runtime
  restrict categories using directed model paths, declared tools and explicit
  nonpublic flow labels. Public TechnicalFinding and response shapes stay intact.
  Multihop positive, disconnected/borrowed-path, public/unknown disclosure and
  zero-finding tests remain. Necessary graph support is not semantic entailment.
- Broken-authorization coverage is explicitly limited to declared tool/invoker
  paths. General permission-matrix authorization remains unassessed.
- Replace generic app summary with the complete attributed purpose and bounded
  typed inventory counts. No description parser, truncation or authority promotion.
- Revert only our automatic narrow-system selection to original global prompting;
  keep explicit workflow context for future separately authorized experiments.
- H2 ledger remains available through internal evidence_ledger_mode(True), but off
  by default. No live evidence supports adding its extra context to legacy prompts.
  Default-on and disabled prompt arms are tested against original prompt framing.
- Latest AI Security compatibility batch: 117 passed. H2 compatibility batch:
  239 passed. These are software checks, not further model observations.
- Final acceptance: NOT RUN; strict lab viability unmet and timeout stop active.
  Remaining lab allowance 18 and final allowance 12 remain unused, not transferable.
