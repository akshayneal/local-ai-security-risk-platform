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
