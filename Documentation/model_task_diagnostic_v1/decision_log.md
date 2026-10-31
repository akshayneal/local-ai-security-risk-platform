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
