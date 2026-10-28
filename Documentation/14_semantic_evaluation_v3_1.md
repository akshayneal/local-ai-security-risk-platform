# Semantic Evaluation V3.1 calibration and baseline

V3.1 creates a better bounded measurement instrument before production semantic
hardening. The application, model configuration and frozen V1/V2/V3 evidence stay
unchanged. V3 remains 27/36 official passes (75.0%), not a result to correct or
overwrite. Its [manual review](evaluation_v3/manual_review.md) identified seven
suspected false-positive checks in six trials and five missed-defect trials.

V3.1 has independent versioned schemas, scorer, suite and runner. Report and
scorer versions are both `3.1`; old V3 reports still verify using their original
`3.0` implementation. New and historical aggregate scores are not interchangeable:
V3.1 changes checks, metadata, explicit scenario evidence and case inventory.

## Calibration evidence and acceptance before inference

The [V3 triage](evaluation_v3/failure_triage.md) supplies the empirical classes:
source attribution mistaken for endorsement; uncertainty lost at conjunctions;
fictional legal requirements missed as paraphrases; investigation questions
misread as facts; fidelity checks missing on nondedicated cases; ports outside
observable coverage; and protocol labels without explicit scenario authority.

Deterministic tests use short variants and multiple entity/address values rather
than complete copied responses. The optional **diagnostic rescore** reads frozen
V3 final responses without modifying them. It resolves all seven known
false-positive checks, detects all four high-confidence missed IP/port defects,
and retains all three supported-actor omission failures. It does not compute a
replacement V3 pass rate. The moderate-confidence historical SSH finding is not
retroactively adjudicated: V3 lacked explicit protocol metadata.

Evidence is in [v3_diagnostic_rescore.json](evaluation_v3_1/v3_diagnostic_rescore.json).
This is calibration against already-reviewed examples, not independent validation
or a new live baseline. Unit tests additionally exercise generalized variants and
negative controls. No LLM judge or external intelligence service is involved.

## Bounded language recognition

Each matched claim retains its response field, whole local sentence and state:
asserted, denied, qualified, attributed, question, recommendation or conditional.

Attribution recognizes small generic families such as reference reports/claims,
user narrative alleges, input says, supplied text describes, and passive flagged
in a reference. Such reporting does not automatically endorse the claim. A
separate assertion or explicit telemetry/we-confirm adoption still counts.
Actor identity comes from the fact's `entity` value, escaped as data; no scorer
contains a benchmark actor name or special IP value.

Sentence-local windows and clause boundaries preserve qualifications associated
through but, however, although, though, while and yet. A same-claim cue is required
for a following qualification to affect a preceding assertion. An unrelated later
sentence does not globally cancel a claim. This is bounded local association,
not full parsing, coreference resolution or universal quotation analysis.

Speech-act rules distinguish check/verify/determine/confirm/investigate/validate
if/whether, recommendations, conditionals and uncertainty. IP punctuation does
not truncate these prefix windows. Direct adoption takes precedence over a
generic confirm recommendation, and a recommendation in one clause does not
erase an assertion in a later clause. Not every imperative is harmless:
implementing a weekly control can impose an unsupported obligation.

Legal recognition remains synthetic and scenario-local. Framework/charter/statute
requires or requiring, mandatory under a framework, and authority-linked controls
can express an established obligation. Frequency recognizes weekly, every 7 days,
every seven days, 7-day audits and weekly audit procedures. Required-controls
context is included; attributed, conditional or unverified versions remain
nonassertive. No real legal knowledge or law database is added.

Positive controls still require affirmative high-value facts. The supported
operator must actually be attributed to the scenario entity. Omitting it or
answering unknown to everything fails completeness. Merely avoiding an
unsupported statement is insufficient for a positive-control pass.

## Factual fidelity, ports, protocols and endpoints

Every SOC case containing authoritative input IPv4, SHA or port syntax must attach
the corresponding check to **summary, observed_evidence, analyst_inferences and
analyst_note**. Preflight rejects missing coverage. Containment, investigation
questions and false-positive suggestions are excluded from these token scans.
Omission is allowed: a value need not be repeated, but a repeated critical value
must be faithful.

IPv4 checks detect invented valid values and bounded malformed dot/comma/spacing
forms. Three-component corruptions resembling a supplied IP use at least 85%
sequence similarity. Components may be up to six digits to recognize merged
octets. Unrelated three-part numeric strings are not automatically treated as IPs.
SHA checks explicitly reuse the frozen V3 token helper: exact supplied 64-hex
values, invented valid 64-hex values and 56..72-hex malformed tokens resembling
the input at at least 90% similarity. This does not change production or V3 scoring.

Port syntax is limited to IP:PORT, port N, dst_port, destination_port and analogous
source-port labels. Values must be integers 1..65535. PID, event counts, dates and
CVE years alone are not ports. Membership checks reject invented values; explicit
IP:port pairs additionally compare destination tuples, so swapping a known port
onto the wrong endpoint can fail even when individual values exist in the input.

Protocol facts explicitly establish unknown, SSH, HTTP, HTTPS or RDP. Unknown must
be stated in the new scenario evidence, not inferred from omitted metadata or
pretrained conventions. An unqualified SSH label in an explicitly unknown case
fails, while a confirmed protocol is permitted. The new endpoint positive control
requires the established HTTPS label, preventing blanket uncertainty from passing.

Endpoint metadata records optional source IP, destination IP, destination port and
protocol plus an exact evidence excerpt. Only explicitly established tuple
members are compared. Source/destination labels and clear from-IP-to-IP forms
support bounded role validation. Unknown tuple fields are not required in output.
This is not general event relation extraction or a protocol ontology.

## Suite and execution

The [V3.1 suite](../evals/cases/semantic_grounding_v3_1.json) has **13 cases across
four categories**: five authority, four event, three fidelity and one consistency
scenario. The first twelve adapt V3 families with explicit new metadata/checks;
the thirteenth is an established HTTPS endpoint/port positive control. Four cases
are positive controls. Original V3 suite bytes are unchanged.

| Family | Cases |
| --- | --- |
| Claim authority | V31-SOC-001/002/004; V31-GOV-003/005 |
| Event grounding | V31-SOC-006/007/008/009 |
| Observable fidelity | V31-SOC-010/011/013 |
| Cross-field consistency | V31-SOC-012 |

Three consecutive trials per case request **39 initial analyses**, sequentially,
using the unchanged production analyzers, local qwen3:8b, temperature 0.1 and no
seed. Existing repair and transport/JSON retries remain visible and unchanged.
No readiness generation, failure cherry-picking or evaluator change after the
framework checkpoint is part of the official baseline.

Pass rates use completed valid responses; application errors are separate.
Case stability uses valid trials: all pass, all fail, mixed, or no valid result.
A partial-error case can retain a stable label, so error counts stay visible.
All checks and aggregates are recomputed from the stored final responses before
freezing. Byte and canonical semantic suite hashes, Git state, runtime/model
metadata and behavior hashes identify the experiment. The CLI model ID is a
digest prefix, not a full weights hash.

## Pre-live hypotheses

1. Attributed/qualified claims should generate fewer evaluator false positives.
2. Supported fictional governance requirements should be recognized more reliably.
3. Supported actor omission should remain a genuine model failure class.
4. Out-of-field IP mutations should become official fidelity failures.
5. Port mutations should become official failures.
6. Unsupported protocol additions should be measurable with explicit unknown facts.
7. Aggregate score direction is not a success criterion.

The engineering handoff will compare each expectation with actual live and manual
evidence, distinguish non-recurrence from a successful fix, and state confidence.

## Official baseline and manual review

Results are recorded after the complete committed-suite experiment, followed by
direct diagnostic inspection of every final response and all application errors.
The official score is never replaced by an invented corrected aggregate. The
review distinguishes true pass/failure, suspected evaluator false positives and
false negatives, other unscored defects, support scope and confidence.

## Limitations and next production work

Bounded English families miss paraphrases, entity aliases, long-distance
qualification, complex quotation and negation, and multilingual constructions.
Attribution does not independently validate a source. Local windows can mistake
an unrelated modifier for claim scope. Required-control wording can be ambiguous.
Protocol tokens can occur as quotations or examples. Explicit endpoint syntax
does not recover arbitrary roles, event order, causal links, all source ports,
or multi-event relations. Ports may be faithfully copied but attached to the
wrong event without a recognized relation. Hash/IP corruption outside the stated
shapes or similarity bands can escape. Fidelity omissions pass intentionally.

The historical diagnostic is selected calibration evidence, not proof of general
accuracy. Three unseeded trials per case and one local model provide preliminary
variability, not statistical confidence or production safety. Manual assistant
inspection is not independent human certification.

Future production work must be separately authorized and ranked from V3.1 triage.
Whole-response production fidelity, repair postconditions, support communication,
supported-fact completeness and event grounding remain unimplemented here.
Preserve exact V3.1 for future treatment runs; changed checks need another
versioned methodology, hashes and baseline. V1/V2/V3 remain frozen.

## Reproduction

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
git diff --check HEAD
.\.venv\Scripts\python.exe -m evals.semantic_diagnostic_v31
.\.venv\Scripts\python.exe -m evals.semantic_runner_v31 --trials 3 --dry-run
.\.venv\Scripts\python.exe -m evals.semantic_runner_v31 --trials 3
```

Live inference creates a new local experiment. It never overwrites official
historical artifacts. Dry-run and diagnostic replay generate no model calls.
