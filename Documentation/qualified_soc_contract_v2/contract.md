# Experimental qualified SOC report contract v2

`app/qualified_soc_v2.py` adds `qualified-soc-report/2`. It is an internal pure
function, off by default, using synthetic reviewed sources. It does not activate
an API/UI or infer real permission, source authenticity, compromise, completion
or executed action. No model or embedding request occurs.

V1 code and `qualified-soc-report/1` remain unchanged. The original Sprint 14
diagnostic stays 11/12 complete authored expectations, including N2A6. New v2
results are prospective development evidence, never a correction to old gold.

## Orthogonal processing and relationship dimensions

`processing_state` identifies the stage reached. `execution_state` and
`comparator_invocations` describe the actual single-comparator dispatch in this
derivation. `relationship` describes what supplied facts establish; uncertainty
does not imply that computation failed to execute.

| Condition | Processing state | Execution / calls | Relationship |
| --- | --- | --- | --- |
| Unique complete association, matching scope | comparison_returned | completed / 1 | declared_alignment |
| Unique complete association, different allowed operation/window | comparison_returned | completed / 1 | declared_mismatch |
| Unique complete association, unknown operation/status/window | comparison_returned | completed / 1 | underdetermined |
| Valid native Microsoft projected row | observations_projected | not_executed / 0 | unassessable |
| No rule or no associated rule | association_resolved | not_executed / 0 | underdetermined |
| Plausible incomplete identity | association_resolved | not_executed / 0 | underdetermined |
| Multiple plausible/full/equivalent records | association_resolved | not_executed / 0 | underdetermined |
| Opposed complete applicable supplied authorization statuses | association_resolved | not_executed / 0 | conflicting_claims |
| Malformed/ineligible/revoked/stale source | source_refused | not_executed / 0 | projection_unavailable |
| Comparator throws or returns a projection refusal | comparison_failed | failed / 1 | projection_unavailable |

Pydantic's `model_validator(mode="after")` checks cross-field invariants after
individual types: completed execution requires one call, a returned comparison,
unique association and the exact comparison outcome. Failed execution requires
one attempted call, a failure state and no completed artifact. Nonexecuted
association states cannot claim alignment. Wrapper and baseline case/question,
and completed comparison case/SOC pillar, must agree. A returned legacy
`projection_unavailable` is a failed projection, not a completed comparison.

`StrictBool` and `StrictInt` prevent `0` or `True` from posing as different types.
The export check additionally compares original serialized JSON before schema
validation; this prevents validation from normalizing away a tampered literal in
the embedded historical v1 model. Python's ordinary `True == 1` is never the
report integrity test.

## Reuse and provenance

`build_qualified_report(raw, review, scope, **options)` and JSON/Markdown exports
use the same argument layout as v1; exports take the report as their fourth
positional argument and repeat the same source/context options.

The synthetic path calls v1 with **no authorization candidates**, preserving its
exact event observation output as `baseline_provenance=event_only_v1`. This
baseline is not an aggregate v1 comparison result. The v2 path separately
qualifies candidate sources and resolves association, then invokes the unchanged
v1 comparator exactly once only in the unique supported branch. It never calls
v1's multi-candidate conflict function and guesses execution from an absent
artifact; that historical helper can internally invoke comparisons.

The native path reuses v1's native observation-only branch, including its existing
bounded JSON/CSV parser. It is labeled `native_v1`. Native ActionType/ResultType
are still uninterpreted assertions; LocalIP/RemoteIP are still local/remote.
No native source-to-permission, direction, transfer, completion, ATT&CK or threat
mapping is enabled. Exact original bytes, canonical bundle, row/field pointers
and coverage remain in the baseline and source snapshots.

All accepted sources carry exact original UTF-8 text/hash, stable application
source identity/revision, complete reviewed metadata and case/workflow/question
scope. Hashes correlate bytes; they do not authenticate the source or anonymize
it. The caller must supply fresh current metadata again at export; no external
registry/revocation discovery is added. Candidate metadata comes from separate
application review arguments, never source-body approval or authority claims.

## Association and conflict policy

Each candidate preserves its input ordinal, source identity/revision/hash and
checked original paths. Ordinals distinguish duplicate records without discarding
sources. There is no deduplication or first-match selection.

Association compares event ID, strict PID, process creation instant, event
instant, scoped question and event principal/asset/endpoint. Case/workflow/source
role/current revision and review effective/expiry windows were already qualified.
Aware time strings compare as instants, preserving their original spelling.
Names, shared IPs, ports, nearby time and reused PID alone cannot form a join.

- A known different identity/scope field means `unrelated`, even when another
  field is unknown.
- No known difference but a missing actor/resource/event instant means
  `plausible_incomplete`; it is not discarded as unrelated.
- All identity fields established means `complete` association. This does not
  establish operation/window applicability or a known authorization status.
- One plausible incomplete record means `incomplete`. A full record plus a
  plausible partial, or several plausible records, means `ambiguous` and blocks
  comparator dispatch. Multiple complete equivalent assertions are also ambiguous.
- An event source cannot qualify its own authorization. Inconsistent fresh
  metadata for one source ID is refused, including conflicting current reviews
  even when their raw bytes match. Exact repeated snapshots are retained as
  ambiguous duplicate records.

Conflict is intentionally narrower than v1. With multiple complete associations
and no plausible incomplete competitor, both opposite known statuses must concern
the **actual known event operation** and both explicit permission windows must
contain its instant. Only then is `opposed_complete_applicable_assertions`
reported. Unknown status/operation/window cannot prove conflict. Different allowed
operations or compatible/different windows alone are not mutually exclusive
permissions and remain ambiguity. No comparator is invoked to decide this source
assertion conflict. This is not proof that real institutional permissions conflict.

With one complete association, the old comparator still compares supplied allowed
operation/window against the actual operation/instant, preserving its documented
declared mismatch/alignment semantics. A failed/attempted event keeps that result;
scope mismatch never becomes proof of completed transfer, intent or compromise.

## Export, development and limits

JSON/escaped Markdown are rebuilt from original bytes, current review snapshots,
scope and all candidate records. Exports reject edited execution/outcome, source
values/revisions, lineage, approval/action fields and changed reviews. Markdown
renders raw annotations as escaped data and displays exact review/scope, candidate
paths and field lineage. Exceptions expose safe reason codes, not exception bodies
or unvalidated prose. Every export recomputes the derivation; its invocation count
describes that one derivation, not a global total across repeated exports.

`evals/qualified_soc_contract_v2/development.py` contains 14 new openly authored
development situations. Paired tests isolate null versus matching versus different
identity, partial versus complete denial scope, timezone-equivalent instants,
source permutations, duplicate records and unsuccessful attempts. Spy tests count
actual comparator dispatches. V1 compatibility checks generate/repeat original v1
reports and both exports on these **new** inputs; no historical experiment is run.

Reviewed synthetic eligibility does not prove source truth, source independence,
real permission, collection completeness, implementation, deployed security or
analyst usefulness. A broad real policy engine and missing structural identity
fields outside the strict synthetic schema remain unsupported. Independent human
semantic review and user visual QA remain PENDING; RELEASE NO-GO.
