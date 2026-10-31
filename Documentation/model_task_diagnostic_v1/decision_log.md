# Sprint 10 development decisions

Implementation-author record, not independent adjudication. Append new outcomes;
never replace failed requests or frozen facts.

- Recovered original Sprint10 branch at exact b6d8453 baseline; no Sprint10 commit,
  remote branch, journal, reservation or result existed. Prior preflight preserved.
- Before interruption 74 baseline tests passed; recovered scaffolding passed 67.
  During managed sandbox resumption, 22 passed/45 setup errors resulted from denied
  pytest temp-directory access. Identical tests passed outside sandbox (67/67);
  no implementation change manufactured those passes. Full access was restored.
- Original 590/13/36/14 plus18 Sprint9 artifacts and AGENTS match. Frozen Aster
  remains byte-identical. Current empty api/ps + no runner/eval/client process
  establishes present quiescence, not the old request's completion/cancellation.
- Streaming/D1 controls confirmed by installed show metadata and versioned provider
  ChatRequest/handler documentation. No generating capability probe/warm-up.
- Review found absent per-phase accounting: a new mock expected a fifth D3 send
  denied but observed count5. Added durable D1/D2/D3/D4 6/4/4/2 gates; both cap and
  replay now deny before wire. Existing mock snapshot expectations updated for the
  added phase_counts field (3 failed/39 passed before that own-test correction).
- Fixed lab token cap1280 for all arms before any results, to leave typical NDJSON
  frame overhead under256KB; token-limit done=true is known withholding and remains
  in denominators. No cap increase or schema/context fallback after results.
- Actual analyzer dispatch is test-covered using counted fake streams, including
  one SOC repair spending two requests and refusal of automatic SDK/HTTP retries.
  Focused current tests82 passed; default app source files remain unchanged.
- D1 has default/off/on order; load/cache/order and stochasticity remain confounds.
  D2/D3 mode selection follows the prospective plan; no invented accuracy rate.

## D1 completed at960f08a9e76503fac4f5b7cf1c073302b5d365b9

Six raw sends, six final done markers: default2 and on2 hit the fixed1280-token cap; off2 completed JSON, positive withheld by endpoint binding, benign returned zero findings but generic/contradictory gaps. No UNKNOWN, retries or repair sends. Off selected for D2/D3 under the prospective operational fallback, not semantic winner. Source/prompt/schema fixed across modes; first default positive includes cold model load. Full raw/model facts remain separate from copied app purpose/inventory; source membership did not prevent irrelevant guideline use. No default change or acceptance gate pass.

## D2/D3 complete, before D4 outcomes

All14 core raw sends have known final completion; zero retries/repairs/UNKNOWN.
Full/off repeated the missing REPHRASER endpoint and unsupported unsafe-output
category. Narrow/off returned both internal records in25.31/29.04s, but positive
said no_finding while recounting unchanged untrusted input through the wrapper.
Benign described fixed12/24 and escaped preview more faithfully, but omitted
literal flow IDs and overstated prevention. Raw-model versus app-projected facts
remain separate. Narrow v1 does not satisfy positive/benign viability.

Ledger-on added SOC PID731 but retained unsupported Network Discovery and a
PowerShell citation despite no PowerShell. Both SOC arms omitted approval EL-271's
four-attempt/09:00-09:10 limit. Both governance arms omitted EL-T37/7of7 and described
unknown retention implementation as lack; on improved external-sharing scope but
not the state fidelity gate. Ledger stays OFF; no product change.

D4's specific ambiguity: does v1 confuse conditional concern with verified attack
proof? Keep v1/cases/rubric/schema/runtime unchanged, append one generic explicit
conditional-decision rule for a new v2 treatment on the same pair, think=false.
This is the only adaptation; positive/benign decisions remain model-owned. New
TDD tests first failed2/2 because the rule option did not exist, then passed.
The new rule contains no case ID, gold label, numeric answer or case-specific
finding. Original recorded v1 prompts/schema were checked byte-identical after
adding optional v2. All D4 outcomes, including failure, will be retained; no more
than2 calls and no Aster tuning. No improvement is claimed before these outcomes.

## Final development close

D4 explicit-v2 returned conditional_concern for free text and no_finding for fixed
numeric input in30.90/36.17s. Both raw rationales end mid-sentence at400 characters;
no app truncation/fill/repair occurred. This corrects one v1 false-negative decision
but does not establish complete explanation quality or full-model fact retention.
The explicit predicate supplies substantial logic and the positive echoes it;
small correlated cases cannot establish general ability or one primary cause.

All16 raw sends are finalized:12 complete JSON/shape-valid answers,4 known length
withholdings,0UNKNOWN,0retry,0SOC repair. Public analyzers returned6/12 submissions;
experimental narrow records returned4/4. No more lab calls. Aster0/12 NOT RUN:
ledger fidelity failed, latest full path not viable, narrow/off incompatible with
its locked method. Defaults unchanged; no production source was changed.

Final Windows full suite2227passed, one pre-existing warning,260.68s. Full Ruff,
pip check and diff check pass. Final raw/protected identities and feature-only
push/CI remain the handoff gate. All original judgments/raw artifacts retained.
