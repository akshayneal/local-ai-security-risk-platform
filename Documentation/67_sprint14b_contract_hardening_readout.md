# Sprint 14B contract hardening

Experimental internal, off by default. RELEASE NO-GO. No model/embedding sends.
INDEPENDENT HUMAN REVIEW PENDING (0 verified). USER VISUAL QA PENDING.

## Recovery and version boundary

Started from `feature/evidence-qualified-ingestion-sprint14` at
`130c95454378394ca197d8851a7bae99adf8439a`, with exact CI success at
https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/42320925797.
Work is on `feature/qualified-soc-contract-hardening-sprint14b`. The original
prospective plan and new diagnostic literals were committed at `f95d4d4` and
`0801266`. On November 7, recovery retained these commits and the newer expected
source/tests/preservation edits; no partial work was regenerated or discarded.
The coherent source milestone is `46ce403`; Git records full identities.

Sprint 14's N2A6 result stays exactly 11/12 full authored expectations. Its
relationship was underdetermined and a comparison artifact existed, but its v1
status was unassessable. No old case, key, scorer, score, journal or example was
changed, replayed or rescored. V2 is a new contract, not a correction to that score.

## P0-A: execution and relationship are separate

`app/qualified_soc_v2.py` adds `qualified-soc-report/2`, preserving v1 source.
Its execution state says whether the single comparator actually returned, failed,
or was never invoked. The relationship says what the supplied assertions establish.

| Fresh situation | Execution | Relationship |
| --- | --- | --- |
| Unknown operation, unique complete association | completed, one invocation | underdetermined |
| Native DeviceNetworkEvents observation | not executed, zero invocations | unassessable |
| Missing, unrelated, incomplete or ambiguous context | not executed | underdetermined |
| Complete applicable opposed assertions | not executed | conflicting_claims |
| Refused source | not executed | projection_unavailable |
| Comparator throws or returns a projection refusal | failed, one invocation | projection_unavailable |

Pydantic `model_validator(mode="after")` checks relationships among fields after
individual types are checked: a completed comparison needs one invocation, a
returned artifact, unique association and the exact returned outcome. Strict
integers/booleans and serialization before normalization prevent True/1 and 0/False
type confusion. Wrapper, baseline and comparison identities must agree.

The new path reuses an explicitly labeled event-only v1 observation baseline,
qualifies authorization sources separately, and dispatches the unchanged comparator
only in the unique supported branch. It avoids v1's multi-candidate conflict helper,
which could invoke comparisons while returning no comparison artifact. Call-spy
tests and the new evaluator observe actual dispatches; exports are separate pure
recomputations. No invocation is inferred merely from a favorable label.

## P0-B: association and conflict hardening

Two new paired reproducers establish v1 limitations without changing its history:

1. Add a same-event rule with unknown principal to a complete matching rule. V1
   drops the partial candidate and selects the complete record. V2 retains it as
   plausible-incomplete and abstains; changing only that actor to a known different
   actor makes it unrelated, while an exact actor gives two ambiguous matches.
2. Combine a complete authorized record with a denied assertion of unknown
   operation/window. V1 can report conflict from statuses alone. V2 requires
   complete, opposed assertions concerning the actual known operation and both
   permission windows covering its instant. Unknown scope/status or different
   allowed operations/windows alone remain ambiguity.

Identity matching uses event, strict PID, process creation instant, event instant,
question, principal, asset and resource. Explicit equivalent timezone instants
match while original strings stay exact. Known mismatches reject joins; missing
identity is not a match and cannot silently disappear. Reused PID, shared IP/name,
port or nearby timestamp alone is insufficient. There is no first-hit selection or
deduplication. Duplicate records retain ordinals; inconsistent review snapshots for
one source identity are refused, not described as conflicting live permissions.

All accepted original bytes, scalar types, source reviews/hashes/revisions, paths,
candidate checks and selected field lineage remain visible. Exports reconstruct
from originals and current reviews, rejecting edited execution, outcomes, source
values, revisions, lineage or action flags. Markdown escapes source text. A reviewed
synthetic source is eligible within this demonstration, never authenticated
institutional permission. Failed/attempted events remain noncompleted.

The [contract](qualified_soc_contract_v2/contract.md) defines the full truth table
and limitations. Source validation, a successful computation and a source hash are
different guarantees; none independently verifies an event or grants authority.

## P0-C: native feasibility

Recommendation: **MORE_EVIDENCE_REQUIRED**. Public Microsoft guidance describes a
ConnectionSuccess record before TCP handshake completion and alongside subsequent
blocking. The public ActionType definition delegates supported values to the
portal schema, which was not accessed. No completion, data-transfer, permission,
ATT&CK or security-risk mapping was activated. Native comparison remains unexecuted.
The [decision memo](qualified_soc_contract_v2/native_mapping_feasibility.md) links
the official sources, exact narrow candidate predicate, prerequisites and negative
examples. More useful observation-only product work can proceed without guessing
vendor action semantics.

## Evaluation and preservation

Fourteen fresh development situations and 101 v2 software tests cover the truth
table, paired adversarial joins, source-order invariance, strict types, failure
states, mutation rejection and new-input v1 export compatibility. Root study
accounting tests additionally check original observation inventories, lineage,
actual call counts, freeze portability and exclusive reservation behavior.

The new mini-diagnostic ran exactly once at ec6289c5ce1dedacaaa68dbe476773f5ad4e41ed. All10
complete authored expectations matched: qualification,association,actual call
counts,execution/processing,relationship,exports and no-grant fields each10/10.
Source/lineage checks passed9/9; one refused source is honestly not evaluated.
Each class contains one authored case; these are not accuracy estimates or
independent human judgments. Original14N2A6 remains11/12,unchanged.

Final local checks:2924passed,1existingwarning,350.74seconds on CPython3.13.1;
Ruff322trackedPython files,pipcheck and full-feature diffcheck pass. Focused
finalv2/study/newpreservation:117passed13.41seconds. Existing ten-case
inputs/key/rubric/generator remain byte-exact. An additive portable freeze binds
their same hashes to relative repository paths while preserving the original
Windows-path freeze; no diagnostic outcome was inspected to make that change.

The new guard protects 757 of 758 baseline Git blobs and 990 inherited raw files.
The only original-file migration adds one import/decorator to Sprint 14's immediate
scope assertion; its body replays at immutable `130c954` with AST equivalence.
An actual app/main.py mutation proves the original guard's protection; a separate
actual qualified_soc.py mutation proves the new guard protects v1. This distinction
avoids falsely claiming an older baseline protected files introduced later.

Of Sprint 14's 50 artifact hashes, 49 remain exact; the sole deliberate exception
is that AST-checked scope-test migration. V1 application source, frozen diagnostic
materials, reports/examples and raw data remain unchanged. The expected 405 visible
untracked s4check files and 185 ignored private caches remain untouched; private
source was never opened or executed. Historical UNKNOWN remains UNKNOWN.

## Product scope and next milestone

P0-A and P0-B add an internal contract; this sprint does not activate public UI/API.
P0-C is a completed decision memo, not a native detector. Existing 300s timeouts and
uncertain inference retry behavior remain unchanged. No model performance or
reasoning accuracy was measured. Human semantic/visual review remains pending.

After the stable tested14B commit, the authorized earlySprint15 branch should add
a useful typed native observation and a default-off development API/UI flow. An
ordinary upload must receive application-derived unverified provenance rather
than caller-supplied approved review metadata. Missing vendor evidence must remain
explicit; do not force native data into the synthetic authorization comparator.

User-only QA: inspect the new unknown-operation and native JSON/Markdown examples,
compare execution counts, relationships and original source pointers, and record
your observations separately. No automated check is a completed visual review.
