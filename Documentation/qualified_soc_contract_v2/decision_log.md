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

## 2 — Minimal association and conflict counterexamples before v2 implementation (2026-11-06)

Source inspection isolates two boundaries. Reproducer A: a complete matching rule
plus a separately qualified same-event/process/time/question rule with principal
null. V1 drops the partial candidate and chooses the complete rule. Competing
explanation: unknown actor might mean an unrelated rule. Discriminator: change
only that null to the exact actor versus an explicitly different actor; partial
must remain plausible, exact must remain an ambiguous second match, different
must be unrelated. V2 adds three-state association rather than changing v1.

Reproducer B: a complete authorized rule plus a same-identity denied assertion
whose operation or permission window is unknown. V1's status-set shortcut calls
it conflicting. Competing explanation: the denial could concern this event, but
its applicability is missing. Discriminator: fill all operation/window scope so
both opposed statements explicitly apply, versus leave one prerequisite unknown.
V2 reports conflict only in the complete applicable case; unknowns and different
allowed operations remain ambiguity. No extra comparator is called to decide
source conflict. Positive/negative paired tests and source-order invariants will
bound the change. V1 bytes and historical 11/12 diagnostic stay untouched.

## Preservation proof distinction (2026-11-06)

Source inspection identified that the original Sprint 14 scope guard predates
`app/qualified_soc.py`: v1 was an authorized-new path, so mutating it cannot
prove that original guard rejects changes to v1. Competing explanation was that
all current source belonged to that guard's protected baseline; its explicit
BASE285 and authorized-new list disprove that explanation. This distinction was
reported before implementing the separate proofs; this written entry follows
the initial code edit, not a claimed pre-edit log. The prospective plan was
already committed; no diagnostic or inference was executed.

Keep the original assertion unchanged and prove its rejection with an actual
`app/main.py` mutation in an immutable130c954 tracked-only archive. Separately,
the new Sprint 14B guard freezes all758 starting blobs except the immediate scope
migration; its actual `verify_scope` calls `verify_protected_blobs`. Test that
same helper against the archive:757 original blobs pass, then an actual v1
`app/qualified_soc.py` byte mutation fails. No frozen hashes, data, old guard
body or source authority is changed to manufacture a passing proof.

## Portable prospective freeze addendum (before execution)

The authoring script recorded absolute Windows paths in its original input-freeze
metadata. Competing explanations: literal hash drift versus path-only portability.
All four original hashes match; cases/key/rubric/generator bytes remain unchanged.
An additive portable manifest maps the same exact bytes to repository-relative
names and hashes the untouched original freeze. No diagnostic was run or tuned.
The evaluator will reject path/hash inconsistencies rather than read host paths.

## 3 — Execution and final schema invariants (2026-11-07)

Continued existing source/tests after allowance interruption; no fixture or
historical artifact was regenerated. Review identified a returned legacy
projection_unavailable artifact (for example from bounded Unicode expanding past
the derived ASCII byte budget): returning a model object is not proof the typed
comparison completed. V2 records one failed attempt and preserves safe legacy
reason codes, while a valid unknown-operation comparison remains completed and
underdetermined. Positive/negative controls pass without model sends.

Final model checks now reject impossible not-executed alignment, cross-case or
non-SOC comparison artifacts, a native provenance label on completed comparison,
and altered candidate ordinals/source identity/revision/hash. Candidate counts
and tri-state inventory must agree with the aggregate association state. Exact
source/current-review rederivation remains the export integrity boundary.

Validation:101 new v2 tests; combined new v2 plus existing v1/qualification focused
checks259 passed in3.27s. Scoped Ruff passes. No new diagnostic was read or run by
this implementation agent; root owns its prospective freeze and once-only run.

## Recovery and broadened continuation (2026-11-07)

Observed actualHEAD0801266 with two local milestone commits and expected newer
implementation/preservation/test edits beyond the earlier nine-file snapshot.
No Python evaluation or new diagnostic reservation exists. Original case/key and
portable hashes verify;757 original blobs and990 raw files remain exact. Preserve
and finish these files. The continuation explicitly authorizes earlySprint15
after a tested14B checkpoint, using observation-only application-owned upload
provenance rather than accepting end-user review/approval metadata.

## Recovered source ready for final14B verification (2026-11-07)

Focused recovery run passed111 tests before the last7 v2 invariant cases were
added; final owned v2+v1+qualification checks then passed259 tests. Root study
accounting controls passed9 tests. ScopedRuff is clean after correcting only the
new study import layout. No diagnostic inputs/key were regenerated; no reservation
exists. Next: commit coherent source, focusedfinal/full deterministic gate, then
freeze candidate and execute the existing ten-case mini-diagnostic once.
