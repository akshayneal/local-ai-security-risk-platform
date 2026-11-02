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
