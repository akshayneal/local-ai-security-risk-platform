# Sprint 14B prospective contract hardening plan

2026-11-06. Experimental internal, off by default. RELEASE NO-GO.
Starting branch: `feature/evidence-qualified-ingestion-sprint14`, local/upstream
and live origin `130c95454378394ca197d8851a7bae99adf8439a`.
Target: `feature/qualified-soc-contract-hardening-sprint14b`.

## Preservation gate

Tracked staged/unstaged diffs empty, divergence 0/0, requested branch absent
locally/remotely. Expected 405 visible untracked s4check files remain user-owned;
185 ignored private cache files, environment, logs and workspaces are preserved.
No Python evaluation is active; only existing Ollama app/server processes were
observed. No service/model/environment change or inference is authorized.

Existing guard verifies 707 original blobs, 990 inherited raw files, 50 Sprint 14
artifact hashes, 312 frozen Python Git blobs and 13 candidate runtime hashes.
Sprint 14 journal has 12 starts, 12 results, one completion: exactly one run,
12 completed, 11 complete authored expectations matched, zero model sends.
Historical UNKNOWN remains unchanged. No private s4check source was opened.
Baseline CI 42320925797 completed/success at the exact starting SHA. Existing
Windows venv is CPython 3.13.1; pip check passes. Main and v2.3.0 stay at
`fde00d0ca5d21eecbc6973cc784550ed453edb7a`.

All 758 starting tracked blobs are preserved except a narrowly proved migration
of the immediately preceding exact-scope test. New guard will protect 757 other
blobs and replay unchanged original assertions at the immutable starting SHA,
with AST equivalence and an actual source-byte mutation rejection. Old scopes,
baselines, raw artifacts, source contracts, examples and frozen scores stay exact.

## Known historical observation, not new qualification

Read-only N2A6 inspection: expected status assessed, actual unassessable; both
relationships underdetermined; comparison artifact exists. Preserve 11/12 and all
original fixtures/key/scorer/journal bytes. Never rerun or rescore that diagnostic.
New identities and versioned results cannot retroactively correct its score.

## Prospective v2 design and alternatives

Add `app/qualified_soc_v2.py`; preserve `app/qualified_soc.py` and its serialization.
Separate processing stage, comparator execution and relationship outcome. A valid
returned comparison, including underdetermined, means execution completed. Native
observation, missing/ambiguous/conflicting association and failed qualification do
not mean that one comparator completed. Count actual calls per derivation; errors
must not acquire completed status. Source integrity is distinct from semantic truth.

Reuse unchanged v1 parsers, strict source reviews, event-only observation path,
source/lineage models and comparator. Do not invoke v1's multi-authorization path
and infer execution from its missing artifact: its conflict helper can internally
call comparisons. Instead qualify/parse candidates, resolve association, then
explicitly call the existing comparator once only for one complete association
without a plausible incomplete competitor. No full pipeline copy or global patch.

Alternatives rejected: rename v1 assessed in place (changes frozen history); infer
execution from a favorable label (wrong dimension); copy the entire v1 pipeline
(unnecessary maintenance/compatibility risk); use a model to resolve joins (no
authority or inference budget). Native mappings remain deliberately unsupported.

Association has complete, plausible-incomplete and unrelated candidate states.
Known different event/process/creation instant/event time/question/actor/asset/
resource means unrelated. Missing keys do not match, but a plausible partial must
not disappear when another full candidate exists. Multiple plausible/full records
abstain; preserve duplicates without first-hit deduplication. Qualification errors
fail visibly rather than falling back. Exact type and timezone checks stay in force.

Opposite known authorization statuses count as conflict only for complete claims
about the same actual operation and relevant event-time window. Unknown scope or
status is insufficient. Different allowed operations/windows can be compatible
rules, so difference alone is not contradiction. This is a narrow comparison of
supplied assertions, not authenticated permission, real conflict or action grant.

## Truth table and new development case matrix

| Situation | Processing / execution | Relationship |
| --- | --- | --- |
| Eligible unique complete matching rule | comparison returned / completed | declared_alignment |
| Eligible unique differing allowed operation | comparison returned / completed | declared_mismatch |
| New unknown-operation case with unique complete association | comparison returned / completed | underdetermined |
| Native DeviceNetworkEvents row | observations projected / not executed | unsupported native/unassessable |
| No authorization | association missing / not executed | underdetermined |
| Different event/process or reused PID creation instant | no association / not executed | underdetermined |
| One plausible incomplete record | insufficient association / not executed | underdetermined |
| Full plus plausible incomplete; duplicate/equivalent records | ambiguous / not executed | underdetermined |
| Complete, applicable opposed supplied permission/denial | conflicting association / not executed | conflicting_claims |
| Unknown status/operation/window plus other record | ambiguous/insufficient / not executed | underdetermined |
| Stale/revoked/wrong case/question/workflow or malformed source | refused / not executed | projection_unavailable |
| Comparator error | projection error / failed invocation | projection_unavailable |

New paired counterfactuals also cover equivalent aware timezone instants, exact
source revisions and snapshots, self-authorization, unsuccessful attempts, absent
actor/resource, source permutations, irrelevant annotations/rows/CSV-like strings,
body authority injection, True versus 1, export-time changed metadata and mutations
of execution/relationship/source/lineage/no-action fields. A metamorphic invariant
states exactly which semantic fields should stay equal, not byte-order identity.

Before fixing each observed bug: record minimal fixture, first broken boundary,
competing explanation, discriminator, minimal fix, positive/negative checks and
remaining limit. V1 behavior remains historical; v2 deliberately supersedes only
the documented execution/association/conflict semantics. No production route,
retrieval, repair, Inspector, correction, launcher or timeout change.

## Native feasibility, bounded research only

Inspect one value, DeviceNetworkEvents.ActionType=ConnectionSuccess, using existing
docs and read-only official public Microsoft references. Record what they actually
support, portal-only gaps, secondary identity/protocol/collection prerequisites and
negative examples. Deliver a short MORE_EVIDENCE_REQUIRED/DEFER/APPROVE_FUTURE_NARROW_STUDY
memo. No activation of native completion, permission, transfer, ATT&CK or risk
semantics. No login, GUI, tenant access, network scanning or installed packages.

## Evaluation and stopping rules

New development fixtures/tests may iterate prospectively. Metrics stay separate:
qualification, source integrity, association, actual comparator invocation,
relationship, provenance/export integrity and no-grant fields. Test the original
v1 path on new development inputs and hash preserved historical artifacts.

Optional new mini-diagnostic: only after candidate maturity, freeze 8-12 disjoint
opaque cases, separate scorer-only key/rubric, evaluator and source identity before
one offline execution. Exclusive durable reservation, per-case journal and retained
failure required. No post-exposure tuning or historical rerun. If a proper freeze
is not feasible, record NOT RUN; robust P0 code/checkpoint takes priority.

Model/embedding calls: ZERO. Historical experiment/diagnostic runs: ZERO. No
independent human semantic review is performed by Codex or other agents; count
remains 0 completed. USER VISUAL QA PENDING. No population accuracy or model-safety
claim. Existing timeout/retry risk remains documented and unchanged for Sprint 15.

Run focused software/negative mutation tests, then full deterministic pytest at
final source, Ruff on tracked Python, pip check, whole-feature diff check and new
preservation checks. Persist stable milestones/checkpoints. Normal feature push is
authorized; verify exact origin HEAD and final-SHA CI test/Ruff conclusions. No
merge, PR, tag, main push, release or automatic background continuation.
