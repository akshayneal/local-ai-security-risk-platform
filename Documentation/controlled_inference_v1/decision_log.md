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
