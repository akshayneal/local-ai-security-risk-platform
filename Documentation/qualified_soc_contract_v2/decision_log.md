# Sprint 14B append-only engineering decisions

## 1 — Gate Zero and prospective architecture (2026-11-06)

Baseline local/origin130c954, tracked tree clean,990 raw/50 artifact/312 source
hashes intact, no active Python evaluation. Existing historical one-run diagnostic
remains11/12; N2A6 comparison exists and returns underdetermined. New v2 separates
actual execution from relationship without editing v1 or historical gold.

First potential association defects from source inspection: a full record can win
after an incomplete same-event principal is silently dropped; known statuses or
different operations can create a conflict despite unknown scope. Competing
explanation: these records might be unrelated or genuinely opposed. New fixtures
must isolate identity completeness and applicable operation/window before deciding.
Use event-only v1 projection, explicit bounded qualification/association, then one
comparator call only in the uniquely supported branch. Preserve all source records.

Next: commit plan; implement/test versioned contract and minimal adverse semantics.
