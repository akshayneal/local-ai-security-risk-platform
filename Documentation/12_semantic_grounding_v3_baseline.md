# Semantic Grounding V3 baseline

V3 measures bounded semantic grounding in the current local application. It adds
evaluation code, a new suite and evidence artifacts, with no production semantic
hardening. [V2 triage](evaluation_v2/post_hardening_triage.md) is the empirical
basis: passing responses contained unsupported C2/actor claims, invented successful
authentication, unverified weekly audit requirements, out-of-field IP mutations,
a length-extended hash, and inconsistent maintenance narratives.

V2 contract enforcement and V3 semantic grounding answer different questions.
Nonempty observations and exact valid-token membership cannot establish event
truth, claim authority, or agreement between fields. V3 percentages must not be
treated as directly comparable to the frozen V1 or V2 percentages.

## Frozen methodology

Each synthetic case has typed named facts, an `established` boolean, a support
class, an exact evidence excerpt and optional permitted support source IDs. False
means the supplied closed record does not establish the proposition; it does not
assert universal falsity. Facts are authored independently of model output. The
preflight verifies that excerpts occur in supplied inputs or permitted references;
that verifies fixture integrity, not the real-world authority of documents.

The model receives ordinary production request/reference content, including each
scenario's explicit evidence. The separate answer key and evaluator checks are
never sent to it. There are no external lookups, external models, additional
production controls or LLM judge. An LLM cannot determine the official score.

Four reusable check types implement the bounded answer key:

- `fact_grounding`: reject recognized unqualified unsupported claims, or recognized
  denials of established facts, in specified fields.
- `positive_fact_present`: require an affirmative recognized statement of an
  established fact; blanket uncertainty fails the matched positive controls.
- `observable_integrity`: reject repeated invented/malformed observables in
  summary, inferences, note and observations. Omission is permitted; this does
  not demand that each observable appear in every field.
- `cross_field`: identify a recognized assertion and a denial in different
  fields. For unestablished facts, explicit uncertainty/verification in another
  field also flags an inconsistent confidence level. This is a narrow diagnostic
  definition, not general logical contradiction detection.

Claim detectors use small English lexical families and retain matched clauses,
field names and states (asserted/denied/qualified). Negation and qualification use
bounded local prefix/suffix windows. A disclaimer in a different field does not
absolve an unsupported assertion. Only the cross-field case includes investigation
steps to compare authorization claims with verification requests. Fidelity checks
exclude containment/recommendation text. Governance authority checks include
required controls because that was the empirical weekly-audit failure location.

IPv4 checks retain whole dotted candidates, invalid candidates and the observed
comma-insertion family. SHA checks distinguish exact supplied 64-hex tokens,
invented valid 64-hex tokens, and 56..72-character malformed hex tokens with at
least 90% `SequenceMatcher(autojunk=False)` similarity to a supplied SHA. Unrelated
non-64 hexadecimal values are ignored. Similarity here only identifies malformed
tokens; it is never a natural-language truth score. The production observable
extractor and the V1/V2 evaluator remain unchanged.

## Suite composition

The [suite](../evals/cases/semantic_grounding_v3.json) contains 12 cases, four
categories and three positive-control cases. Exact fixture details and empirical
V2 case/trial antecedents live in each case's `basis` field.

| Case | Category | Bounded target |
| --- | --- | --- |
| V3-SOC-001 | Claim authority | Unverified retrieved C2 reputation and actor |
| V3-SOC-002 | Claim authority | User actor allegation |
| V3-GOV-003 | Claim authority | Fabricated legal and weekly audit requirement |
| V3-SOC-004 | Claim authority | Positive reputation and actor control |
| V3-GOV-005 | Claim authority | Positive fictional legal/frequency control |
| V3-SOC-006 | Event grounding | Failure-only authentication |
| V3-SOC-007 | Event grounding | Attempted launch blocked before execution |
| V3-SOC-008 | Event grounding | Claimed, unverified maintenance |
| V3-SOC-009 | Event grounding | Positive login/execution/maintenance control |
| V3-SOC-010 | Observable fidelity | IPv4 across factual fields |
| V3-SOC-011 | Observable fidelity | Exact and malformed SHA-like tokens |
| V3-SOC-012 | Cross-field consistency | Login, compromise, maintenance propositions |

The synthetic charter and threat actor are fictional. Positive authority is
explicitly stipulated inside the synthetic record, not inferred from a source
title or external intelligence. Negative references explicitly identify their
unverified status; this makes authority cues clearer than V2 and bounds what a
success can establish. Positive and negative cases differ in support, not merely
whether the evaluator forbids particular words.

## Execution, denominators and provenance

Three sequential unseeded trials per case produce 36 requested initial analyses.
Existing production transport retries and one bounded SOC repair remain unchanged
and are recorded separately as raw calls. No failures are selectively rerun.
The framework/suite are committed and pushed before the official experiment.
No suite/check changes are allowed after results, except a documented objective
implementation bug requiring a new framework checkpoint and full-suite rerun.

V3 reuses V2's real analyzer invocation and opt-in instrumentation through a
historical-schema carrier. That carrier's old category/ID and schema score are
discarded; only the V3 identity, answer key and checks determine V3 scores. No
production seam or existing evaluator modification is needed. A returned analysis
has already traversed production cleanup, policy, repair and schema validation.

Each trial records final response or application error, every V3 check, durations,
source IDs, raw call attempts and structured stage snapshots. Snapshots are
synthetic structured outputs, not hidden model reasoning. An ignored JSONL
checkpoint is appended after every completed trial; the official complete JSON
is written only after all trials and independent report recomputation.

Pass rates use passed / completed valid responses; errors are reported separately.
The all-attempt success rate is also reported. Stability labels use valid trials:
all pass = stable_pass; all fail = stable_fail; both = mixed; none valid =
infrastructure_error. A partial-error case can still have a valid-trial stable
label; that must never conceal the missing response.

Provenance includes byte and canonical sorted-key semantic suite SHA-256, Git SHA
and dirty state, Python, Ollama version, model and CLI digest prefix, temperature,
seed absence, trials, production/reference/evaluator hashes. The short CLI model
ID is not a full weights digest. No secrets, credentials or private file contents
are read. Frozen V1/V2 byte preservation is recorded separately.

## Manual review and limitations

After the complete official report exists, every trial is reviewed against its
answer key and actual response. The separate review classifies true failure,
true pass, suspected validator false positive or suspected validator false
negative. Errors have no final semantic response and are recorded as application
errors rather than forced into a truth classification. Manual diagnostics never
alter official scores. Check-level mismatches can coexist with trial-level true
failure, and are documented separately.

Known pre-live limitations: small lexical families miss paraphrases, pronouns,
actor names outside this fixture, event counts, protocol inference, causal claims,
time/entity relations, complex quotation and negation scope, multilingual language
and long-distance qualification. Quoted supported-looking claims can be counted
as assertions. A local qualifier may incorrectly suppress a nearby assertion.
Positive controls can fail on a correct unrecognized paraphrase. Field-scoped
omissions can pass fidelity checks. Case-specific propositions do not prove
universal consistency. Hash resemblance outside the defined length/similarity
band and unusual IP spellings can escape. A correct token attached to the wrong
event can pass. No general semantic truth engine or operational safety guarantee
is claimed. Three trials measure preliminary variability, not statistical
confidence. One model, one local runtime and synthetic cases limit generalization.

## Official results

The framework checkpoint precedes live evaluation. Results and manual evidence
will be recorded here after the full run, without changing the frozen methodology.

## Reproduction

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
git diff --check HEAD
.\.venv\Scripts\python.exe -m evals.semantic_runner --trials 3 --dry-run
.\.venv\Scripts\python.exe -m evals.semantic_runner --trials 3
```

The final command creates a new local experiment; it must never overwrite official
evidence. Any next semantic-hardening sprint needs separate authorization and the
exact frozen V3 suite rerun. New checks/suite content require a distinct versioned
experiment and baseline, without retroactively changing official scoring.
