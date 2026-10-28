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

The engineering handoff compares every expectation with actual live and manual
evidence, distinguishes non-recurrence from a successful fix, and states confidence.

## Official baseline and manual review

**37/39 completed valid trials passed (94.9%)**, two assertion failures and **zero application/runtime errors**. All 39 planned analyses were attempted and returned a valid response, so the all-attempt success rate is also 94.9%. Stability: **11 stable-pass, zero stable-fail, two mixed**, no infrastructure_error cases.

| Category | Passed / valid | Rate |
| --- | ---: | ---: |
| claim_authority | 15/15 | 100.0% |
| cross_field_consistency | 3/3 | 100.0% |
| event_grounding | 10/12 | 83.3% |
| observable_fidelity | 9/9 | 100.0% |

Positive controls: **12/12 (100%)**, including all supported reputation/actor, fictional governance, confirmed event and known-HTTPS controls. Positive presence does not guarantee agreement with every other field: the manual review finds two missed consistency/support-scope defects in passing positive trials.

| Case | Trial 1/2/3 | Stability |
| --- | --- | --- |
| V31-SOC-001 | P/P/P | stable_pass |
| V31-SOC-002 | P/P/P | stable_pass |
| V31-GOV-003 | P/P/P | stable_pass |
| V31-SOC-004 | P/P/P | stable_pass |
| V31-GOV-005 | P/P/P | stable_pass |
| V31-SOC-006 | P/P/P | stable_pass |
| V31-SOC-007 | F/P/P | mixed |
| V31-SOC-008 | P/F/P | mixed |
| V31-SOC-009 | P/P/P | stable_pass |
| V31-SOC-010 | P/P/P | stable_pass |
| V31-SOC-011 | P/P/P | stable_pass |
| V31-SOC-012 | P/P/P | stable_pass |
| V31-SOC-013 | P/P/P | stable_pass |

The exact [official report](evaluation_v3_1/semantic_baseline_3trial.json) is frozen alongside [provenance](evaluation_v3_1/provenance.json), [manual review](evaluation_v3_1/manual_review.md), [triage](evaluation_v3_1/failure_triage.md) and the [expectation check](evaluation_v3_1/expectation_check.json). Its SHA-256 is `948a30ef05feb2faeff00794e5f626a19a3bc0dce332db2fddc52838a1f8bf7e`.

Runtime UTC interval: `2026-10-28T06:48:03.525519+00:00` to `2026-10-28T07:28:41.131801+00:00`. Framework: `41465cd522d0ea2a45b3891f09aff98694e80514`, clean at preflight; Python 3.13.1; Ollama 0.40.11; qwen3:8b; CLI digest prefix 500a1f067a9f; temperature 0.1; no seed. Byte suite hash: `d78635b639a84cdf935500c3fb7ffc5ba1322b86872fb3db94e0b501bc563c68`; semantic hash: `92cc87d29d9a684f047570f206ef41329d8cb09e7e700428e93dabff6ec12967`. All 38 behavior file hashes match before and after inference.

There are 39 initial generations plus three existing bounded repairs: **42 completed raw calls**, no failed raw calls or transport/JSON retries. Repairs occur at V31-SOC-006/1 and /3 and V31-SOC-009/2; all return clean measured factual fields. Repair-generation time totals 170.8521 seconds. Mean valid-trial latency is 62.4995 seconds; median 56.7900 seconds. These are descriptive local timings, not an isolated causal comparison.

### Manual review and residual errors

Every final response and its actual checks was directly inspected. Primary classes: 35 bounded true passes, two suspected false-positive failures and two suspected false-negative passes. Of the missed consistency defects, one is high confidence and one moderate. No corrected aggregate score is calculated.

- V31-SOC-007/1: attempted PowerShell execution is misread as completed execution despite explicit no-execution statements.
- V31-SOC-008/2: the user's claim about approved maintenance requires verification is misread as confirmed approval.
- V31-GOV-005/3: a known weekly requirement is acknowledged, while another field calls audit frequency unspecified. The positive and fact rules miss that missingness contradiction (high confidence).
- V31-SOC-009/1: signed approval is acknowledged, but inference says authorization context is unclear. This is a moderate-confidence support-scope concern, possibly unstated real-world caution.
- V31-SOC-009/3: an excluded investigation step changes 192.0.2.51 into malformed 19.2.0.2.51. It is a high-confidence unscored referential defect, separate from configured factual-field false negatives.
- V31-GOV-003/3: synthetic context is extended into no actual data handling/minimal risk; this is a moderate-confidence unscored rationale concern.

Two of 39 reviewed trials (5.1%) contain suspected false-positive failures, and two (5.1%) contain suspected missed within-key defects. These are diagnostic proportions with a stated review denominator, not formal population precision/recall or independently established error rates. The two official failures are lexical classification errors under manual review; they do not establish actual event-state reversal or approved-maintenance promotion.

All 24 IP-check trial applications, all three SHA applications and all 15 port applications pass. Every SHA trial copies the exact hash in summary/observations; the HTTPS endpoint control preserves its roles, port 8443 and known protocol. Twenty-one unknown-protocol trials and three known-HTTPS trials contain no unsupported assignment in the measured fields. No new measured-field mutation or unsupported protocol trigger recurs. The excluded investigation-step mutation demonstrates the scope boundary; absence elsewhere does not establish a production fix.

### Expectations and next work

The [seven-hypothesis ledger](evaluation_v3_1/expectation_check.json) separates acceptance of deterministic detector behavior from recurrence in fresh live data. Known attribution/legal calibration classes are corrected, but a possessive claim form still fails. Actor completeness remains strict although omissions do not recur. IP/port/protocol detection capability is exercised by calibration and unit tests; fresh live failure triggers do not recur in measured fields. Aggregate direction remains irrelevant to acceptance.

Actual V3.1 evidence ranks three separately authorized production targets: reference-bound fidelity in proposed steps; consistency when stating that established facts are missing; and explicit communication of scenario support versus external/operational uncertainty. The third has moderate confidence. First separately version residual evaluator families (attempted event nouns, possessive claims, missingness/context contradictions). Do not modify the frozen V3.1 scorer or fit production phrases to its false positives.

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
