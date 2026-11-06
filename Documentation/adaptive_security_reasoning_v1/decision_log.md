# Sprint 13 decision log

2026-11-01 (America/Indianapolis), recovery: local/origin Sprint 12 match
95fdfbe1d5f5cacf0d814e7c3a67bb56ce18f57a; main/tag unchanged. Tracked/staged
diff empty. Exactly 405 inherited visible s4check files preserved, with 185
ignored files. Known historical artifact counts reconcile. No active evaluation
process observed; existing Ollama app/server and editor processes untouched.
Existing venv Python 3.13.1; ordinary python resolves Windows Store alias, so use
.venv/Scripts/python.exe. Created only authorized Sprint 13 branch. Development
and diagnostic sends consumed: 0/0. Historical UNKNOWN remains UNKNOWN.

Prospective H1/H2/H3 cards saved in plan before new application implementation.
Next: forensic table, active preservation guard, strict schema and fresh locked
holdout; no generation before prospective commit.

2026-11-01, adaptive deterministic cycle S1 (before repair; zero model sends).
Observation: review probe with governance status explicitly_absent, actual_timing
before, and positive sample returned declared_mismatch, whereas analogous AI gate
contradiction returns conflicting_claims. Blanket governance/AI disconfirming IDs
also marked mismatch-supporting values as counterevidence. Rival explanation:
actual timing describes a different control; the schema fixes same action/scope,
so this implementation must surface conflicting reported implementation state.
Hypothesis: explicit state/timing conflict checks plus value-specific pointer
roles prevent this polarity failure without suppressing genuine absence or late
review. Prospective tests: absent+known timing => conflicting_claims;
absent+unknown timing => declared_mismatch; present-after remains mismatch and
its after/write/model values are not disconfirming; present-before is alignment.
Failure condition: any known positive premise silently relabeled counterevidence,
or conflict incorrectly converted to deployed violation. Adopt only after tests.

Cycle S2 prospective: a null counterclaim is missing knowledge, not an assertion
of the opposite fact. Current asymmetric handling marks null primary + known
alternative conflicting while known primary + null alternative is unavailable.
Hypothesis: preserve primary values/results, accept typed null alternatives as
unknown, and surface unresolved alternatives without making them contradictions.
Rival: treating every alternate as conflicting is conservative but semantically
incorrect. Prospective controls include both null directions, typed enum unknown
vs before, and before vs after as genuine conflict. Never fill a primary unknown
from an alternate claim. Counterclaims cannot change source-reference metadata.

Cycle S3 prospective (before repair; zero model sends): review probe supplied an
AI timing counterclaim value violet; scalar-type-only checking accepted it as a
meaningful conflict. Hypothesis: validate an alternate against the same strict
pillar schema and comparison preconditions without mutating canonical input.
Positive control before/after remains a conflict; enum violet, negative counts,
invalid time, unknown graph endpoint and attempts to change source-reference
metadata must be projection_unavailable. Rival: scalar class checks suffice;
the observed accepted impossible enum falsifies that rival. Null is accepted
only where the declared field is nullable; typed enum unknown remains explicit.

S1/S2/S3 falsification before repair: focused pytest retained 9 failures and
112 passes (3.20s). Failing assertions concretely reproduced absent-vs-actual
state conflict, mismatch support mislabeled counterevidence, both nullable
unknown directions, both typed enum unknown directions, impossible violet
counterclaim, negative count and invalid time counterclaims. These failures
precede the following implementation correction; they are not model outcomes.

S1/S2/S3 repair result: 121 focused tests pass (2.77s). Original scalar status
counterfactual explicitly_absent retained its before timing and therefore now
expects conflicting_claims; the separately added absence+unknown-time control
still expects declared_mismatch. This development rubric clarification is
recorded before any generation/holdout execution; no frozen old test was edited.

Cycle S4 prospective: read-only review mutated a withheld commentary hash to a
different valid 64-hex value and export accepted it. Canonical assessment stayed
intact, but generated-artifact provenance was not bound. Hypothesis: require the
original optional commentary when exporting and reconstruct the complete report;
then a digest/status change or omitted/changed original commentary must fail.
Rival: regex verification is adequate; observed mutation disproves that claim.
This changes only internal new API's optional argument; deterministic callers
remain compatible. No model sends are required for this integrity falsification.

S4 result: 122 focused tests pass (2.65s); Ruff on the four new application/test
files passes. Export now reconstructs original report including optional
commentary and rejects forged hash/status or omitted/changed original commentary.
All model commentary stays withheld. The deterministic cycles are development
falsification only, not independent review or diagnostic holdout scores. No raw
model sends have been made by this implementation agent.

Final adversarial development audit, prospective cycles S5-S8 (before repair;
no model calls or holdout inputs). S5 observed wrong-snapshot source text is
retained and exported even though source_snapshot_mismatch is returned.
Hypothesis: retain eligible source only after fingerprint validation; preserve
raw hash and diagnostic while withholding the unreviewed bytes. Falsifier: any
source text from a mismatched snapshot appears in JSON/Markdown export.

S6 observed Python fromisoformat accepts and normalizes +00:60 and +00:99.
Hypothesis: explicit timezone component bounds reject these malformed offsets
before comparison. Valid Z, +00:00, and equivalent -05:00 controls must keep
prior results; malformed offset must be projection_unavailable, never a new
scope mismatch caused by normalization.

S7 observed every AI graph field marked decisive, including disconnected nodes.
Hypothesis: when a selected path exists, bind graph evidence only to nodes/edges
on model-to-selected-tool directed paths. Counterclaim on disconnected node kind
must leave the scoped relationship unchanged; model-kind change on selected path
must preserve both assertions as conflicting. No-path graph conservatism remains
explicitly unassessed instead of claiming minimal decisive evidence.

S8 observed canonical amount integer1 changed to booleanTrue passes export:
Python/Pydantic equality equates 1 and True. Hypothesis: compare canonical JSON
serialization of the reconstructed report, including types. Falsifiers: int-to-
bool and bool-to-int premise mutations accepted at export. This repairs exact
literal-type identity; it does not prove semantic truth or authenticity.

S5-S8 prerepair falsification: focused tests produced 7 failures and 124 passes
(3.18s): three normalized malformed offsets, disconnected-node false conflict,
wrong-snapshot raw export, and both integer/boolean literal mutation controls.
Valid +24:00 rejection and selected-path conflict control already passed. These
are new development findings; no diagnostic input/outcome was consulted.

S5-S8 repair: 131 focused tests pass (2.61s); Ruff scoped app/test checks pass.
Snapshot mismatch now keeps its hash/reason but withholds raw source; malformed
timezone offsets fail before comparison; disconnected graph counterclaims do
not affect existing selected-path relationship; selected path kind changes stay
conflicting. Export comparison now uses serialized typed JSON, so integer1 is
never treated as booleanTrue. No-path graph evidence remains conservative over
the full declaration and is explicitly listed as unassessed precision.

Pre-generation runtime cycle: author code review found arbitrary output-root access,
interrupted track/global reservation gaps and unverified stored artifact bytes.
Required hypothesis: lexical isolated namespace and cross-journal/hash replay checks
fail before filesystem access/wire;59offline transport tests support these narrow
properties. No generation occurred. Root also removed silent model-ID truncation
(complete bounded48-ID union), bound outer case identity, rejected duplicate model
keys, and isolated model-schema failures from canonical report failures.
Initial paired allocation is split into D0 six mismatch/alignment cases ?M/H
(12sends), followed by separately committed D1 unknown/conflict/prerequisite cases
(12sends). Any later repeat/ablation allocation is prospective.
Pre-freeze probes are unqualified authoring diagnostics; some exact prototype
source revisions were not pinned. Their inputs/failures remain regression
evidence, not frozen study results or semantic improvement denominators.

H4 prospective (D0 still running; no source change): DEV-F28 H says matching
scope premises may affect alignment. The flat counterevidence list has no
explicit allegation target. Rival: generic hedging/sampling may persist even with
clear metadata. After D0, add explicit scope text, keep outcome semantics fixed,
and repeat matched H/M cases without counting repeats as new discoveries.
Separately, denial applicability must be scoped: denial of X/assetB is not proof
of denial for Y/assetA. Register matched/mismatched denial-scope deterministic
controls before repair; retain all D0 sources/results and frozen keys.

Post-D0 prospective deterministic cycles S9-S10. D0 finished12known-complete;
no provider activity is initiated here. S9 observation: reported_denied returns
mismatch before checking whether the denied operation/principal/asset/endpoint/
window is the observed event's scope. Hypothesis: require exact known same scope
before a declared denial mismatch; unrelated or unknown denial scope must be
underdetermined. Positive control same scope denied remains mismatch, including
failed attempts; single-variable wrong operation/principal/asset/endpoint/time,
null scopes, and boundary/offset controls discriminate applicability. Competing
explanation: denial means universal denial, but this synthetic schema declares
specific scope and no wildcard semantics, so universal reading is unsupported.

S10 observation: Text min_length1 accepts whitespace-only operations and sample
scope, permitting meaningless alignment. Hypothesis: reject text whose Unicode
strip is empty without stripping or changing retained bytes. Matching ordinary
and nonblank Unicode/internal-whitespace strings remain exact literals. Failure
conditions: blank scope yields alignment, or normalization changes original text.
Source revision whitespace is also invalid typed metadata. This is schema
validation, not natural-language policy or operation interpretation.

The existing disconfirming_premise_ids field will gain description/docstring only:
its premises limit broader adverse allegations or oppose primary assertions,
not the final typed result by default. No serialized Assessment field is added;
all12 D0 reports/exports must reproduce exactly on their six canonical cases.
H4 model-context scope text is a separate root-owned prospective ablation.

S9/S10 prerepair deterministic controls: 27 failures and147 passes (3.58s).
Failures comprise11 unrelated/missing-denial-scope outcomes,15 blank scope/sample
values and1 blank revision validator. Same-scope denial/result/time controls
and nonblank Unicode literal preservation already passed. No frozen key changed.

S9/S10 repair:174 focused tests pass (2.85s); scoped Ruff passes. Text validation
rejects Unicode whitespace-only values while preserving every nonblank original
literal, including internal whitespace and Unicode composition. Denial applies
only at known matching operation/principal/asset/endpoint/time scope. Existing
Assessment field description adds no serialized value. Read-only exact replay
of D0 after changes reproduced all11 stored reports and Markdown exports across
all6 distinct cases (the12th record was structurally withheld and has no report;
it remains withheld). Aggregate original/reproduced report+Markdown SHA256:
9d234b17eddb090ead85781e406ffa497e84b7e45282a9a096b13bd510872af5.
No D0 input/key/output, journal, reporter byte or prior source revision changed.

2026-11-06 recovery: retained local branch at e11645b and its two additive
commits, plus expected interrupted readout/reviewhelper edits. No active Python
evaluation was observed. Durable tracks/global journal record D0=12,D1=12,
all24 COMPLETED, no pending/UNKNOWN. D1 finished within its original bounded
foreground process after the authoring interruption. No experiment is rerun.
The original shared14,400second clock has expired; generation is closed without
changing timestamps, identifiers or caps. D3 is NOT RUN, H4 remains untested.
The unused60development and24diagnostic sends remain unspent ceilings.
Offline deterministic diagnostic remains authorized by the original protocol,
with committed selection before input/key execution and zero model requests.
The resume prompt separately authorizes restoring the missing Demo shortcut via
the existing installer; no launcher source/app startup is authorized or needed.

Final local verification2026-11-06:2629passed,1Starlette/httpxwarning,297.57s;
all301trackedPythonfilesRuffPASS,pipcheckPASS,diffchecksPASS. All911historical
rawfiles,645protectedoriginalblobs,79newrawartifacts,25saveddatafiles andsource
inventory verified. The restoredshortcutrecordretainsoriginalCRLFbytes; Git
file-specific cr-at-eol recognizes thatlineending while retaining normalwhitespace
checks, rather than rewritingtheoriginalrecord. No app/holdoutrunnersourcechanged
aftertheonce-only24case diagnostic. Next safe step:normalfeaturecommit/push and
exactfinalSHA CI. No newinference ordiagnosticexecution is permitted/needed.
