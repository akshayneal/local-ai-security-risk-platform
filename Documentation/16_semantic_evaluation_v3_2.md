# Final semantic evaluation calibration V3.2

V3.2 is the final calibrated semantic ruler for this project phase. It changes
measurement only. Production semantic treatment has not occurred. V1, V2, V3
(27/36) and V3.1 (37/39) retain their original suites, scorers and official evidence.
Scores across evaluator versions are not directly interchangeable or treatment
effects. Three trials are preliminary stability observations, not statistical
confidence.

## Why a final calibration

The frozen [V3.1 review](evaluation_v3_1/manual_review.md) identified two
high-confidence lexical false positives, an established weekly frequency later
called unspecified, and a copied IP corrupted in an excluded investigation step.
The moderate authorization-context concern motivates a conservative scope
distinction, not universal natural-language contradiction solving. See the
[V3.1 triage](evaluation_v3_1/failure_triage.md) and
[engineering report](15_semantic_v3_1_sprint_report.md).

## Version boundary and preservation

Separate `evals/semantic_{schemas,validators,observables,runner,diagnostic}_v32.py`
modules use explicit report/scorer version `3.2`. The new suite is
`evals/cases/semantic_grounding_v3_2.json`. Historical modules are untouched.
Immutable V3 string/SHA utilities and the existing application-call adapter are
reused explicitly. The historical adapter's carrier check is discarded; only
V3.2 checks score the returned response. No LLM judge is used.

[Preservation](evaluation_v3_2/preservation.json) records initial working-byte
SHA-256 and normalized Git blob identities for 86 historical/source files.
Existing attribute files stay unchanged because historical provenance hashes
them. New official JSON has a scoped `-text` rule. The new suite is committed with
LF bytes under existing automatic normalization; exact-byte provenance describes
the inference checkout, while semantic hashes and Git blob identities support
cross-checkout verification. Do not silently normalize a frozen suite before a
treatment comparison: verify both exact suite hashes first.

## Bounded rules

### Attempt versus completion

Attempted execution, launch, process creation and attempt-to-execute forms attach
to the local event match. They cannot establish completion. Actual execution,
execution completed, process started, process-start telemetry and successful or
accepted authentication remain affirmative forms. An attempt does not absolve a
separate completed event in the same sentence. This remains a bounded English
recognizer, not a dependency parser.

### Possessive attribution

Literal possessive sources (user, reference, source, report, supplied narrative)
with claim/allegation/assertion and that/about are attribution. Local requires
verification, remains unverified, not independently established and lacks
confirmation suffixes retain their qualification. Explicit independent adoption
still counts as assertion. A disclaimer in a different sentence does not repair
an earlier assertion.

### Known values and support scope

`known_values` metadata declares a key, literal subject aliases, value or explicit
unknown, evidence, supplied-scenario/telemetry scope and external-verification
status. A `known_value_consistency` check rejects explicit missing/unspecified/
unknown/not-provided statements about an established value. It permits actually
unknown attributes and distinguishes known weekly cadence from unknown audit
methodology. Positive fact checks continue to require supported statements;
omission and blanket hedging are not valid substitutes.

Explicit external/real-world/independent verification uncertainty attached to the
same subject is permitted. It does not require external confirmation of stipulated
scenario facts. Ambiguous phrases such as without clear authorization context
remain manual-review concerns. The scorer does not infer real legal applicability
or reputation and does not consult external sources.

### Reference-bound investigation identities

Four factual fields retain the V3.1 IPv4, SHA, port, protocol and endpoint checks.
A distinct `proposed_identity_integrity` check covers only
`recommended_investigation_steps`. Containment is deliberately outside this new
scope: it mixes hypothetical operational conditions, and expanding it is not
needed to measure the motivating copied-investigation-identity defect.

IPv4 candidates must resemble supplied identities (70% sequence similarity) or
have explicit case/source/destination/observed/reported/alert context. Near-SHA
tokens use 56..72 hex and 90% similarity; exact supplied hashes are permitted.
Ports require a near-reference endpoint, an explicit source/destination port
label, or local traffic/connection/case context. Endpoint pairs cannot borrow a
different established endpoint's port. Hours, days, PIDs, dates, counts and CVE
numbers are not parsed as identity values. Explicit hypothetical/illustrative/
example clauses are excluded, without absolving a separate next step.

This is reference-bound fidelity, not universal numeric subset validation.
Distant invented identifiers without a case cue, far-corrupted hashes, prose
outside the selected fields and unmarked hypothetical intent remain bounded
limitations. Observable omission is allowed; dedicated positive checks separately
measure supported semantic completeness.

## Suite and preflight

Fourteen cases span four families, three sequential trials per case: 42 planned
application analyses before existing repair/retry generations. Thirteen requests
are inherited unchanged from V3.1; the fourteenth is a paired known-weekly,
unknown-methodology, external-applicability governance control. New case IDs and
checks make this a distinct baseline.

| Family | Cases | Coverage |
| --- | ---: | --- |
| Claim authority | 5 | Unverified reputation, actor, legal/frequency; supported actor/reputation and governance |
| Event grounding | 4 | Failed/successful login, attempted/completed process, claimed/established maintenance |
| Observable fidelity | 3 | IP, SHA, endpoint/port; copied investigation identities; HTTPS positive |
| Cross-field consistency | 2 | Event contradictions; known cadence, unknown methodology, conservative scope |

Five positive-control cases yield 15 positive-control trials. They require actor,
governance, event and protocol presence. Preflight validates requests, references,
fact evidence, endpoints/protocols, positive controls, literal known-value metadata,
support scope, field coverage and proposed-step fidelity coverage; it performs no
generations. Runtime collection uses read-only CLI metadata.

```powershell
.\.venv\Scripts\python.exe -m evals.semantic_runner_v32 --trials 3 --dry-run
.\.venv\Scripts\python.exe -m evals.semantic_diagnostic_v32
```

## Diagnostic calibration and pre-live expectations

The [non-official transition artifact](evaluation_v3_2/v31_diagnostic_transitions.json)
replays historical V3.1 final responses under explicitly mapped new keys. It
corrects V31-SOC-007/1 and V31-SOC-008/2 and detects V31-GOV-005/3 missingness and
V31-SOC-009/3 proposed-step IP corruption: four of four intended transitions.
The moderate V31-SOC-009/1 concern remains separate. No corrected V3.1 aggregate
is calculated. V3/V3.1 official replay and historical supported-actor omissions
are independently tested.

These hypotheses are recorded before live inference:

1. H1: both known V3.1 lexical false-positive families are corrected diagnostically.
2. H2: the known weekly/unspecified contradiction is detected.
3. H3: the known proposed-step IP mutation is detected.
4. H4: supported actor/governance/event facts remain positively measurable.
5. H5: unrelated recommendation numbers do not trigger identity failures.
6. H6: no known high-confidence evaluator blind spot prevents measuring the
   bounded production controls planned next.
7. H7: aggregate score direction is irrelevant; no tuning or causal cross-version
   improvement claim follows a higher or lower score.

The final ledger will record expected/actual, assessment, explanation and
confidence, distinguishing capability tests from actual live recurrence.

## Official protocol, review and freeze

Run once after a committed/pushed framework and passing pre-live tests, Ruff,
whitespace, preservation, historical replay and dry-run gates. Use local qwen3:8b,
temperature 0.1, no configured seed and unchanged application repair behavior.
Record the actual Ollama version and CLI model digest kind; a short CLI ID is not
a complete weights digest. Never rerun failed semantic trials.

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
git diff --check HEAD
.\.venv\Scripts\python.exe -m evals.semantic_runner_v32 --trials 3
```

The runner hashes behavior files before/after inference, preserves error trials,
writes ignored per-trial checkpoints and verifies complete scoring/aggregation.
Official evidence is copied to a new `evaluation_v3_2` directory. Inspect every
final trial only after the complete report exists; retain exact quotes, answer
keys, official outcomes, true passes/failures, suspected scorer false positives/
negatives, unscored defects and confidence. Assistant manual inspection is not
independent human certification. Never calculate a replacement aggregate score.

**Final-calibration stop rule:** suite and scorer are immutable after the pre-live
framework commit. No live-result-driven tuning, new grammar family for an ordinary
missed paraphrase, or V3.3 recommendation for lexical imperfections. Residual
ambiguity belongs in manual review. Further evaluator versioning is justified
only by an objective defect that makes the planned treatment scientifically
uninterpretable. Authorized production treatment must rerun the exact frozen
V3.2 suite/scorer with both suite hashes verified. Production hardening requires
separate authorization and is not part of this sprint.

Results, exhaustive review and priorities are recorded in the
[engineering report](17_semantic_v3_2_sprint_report.md) after the one official run.
