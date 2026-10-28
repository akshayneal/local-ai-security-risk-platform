# Semantic Evaluation V3.1 sprint engineering handoff

This is an evaluation-calibration sprint. It changes the ruler and freezes a new
current-system baseline, with zero production behavior changes. See the
[methodology](14_semantic_evaluation_v3_1.md) and new evidence directory
`Documentation/evaluation_v3_1/`. The next production sprint remains unauthorized.

## Starting state and preservation

- Branch: `feature/portfolio-hardening`, clean and synchronized with origin.
- Starting HEAD: `2d434f8caa688fe38dcec44ec573cdd4c6ad33d7`.
- Starting checks: **501 passed**, one existing Starlette/httpx warning, 10.14 s;
  Ruff and `git diff --check HEAD` passed.
- Read AGENTS and the frozen V3 manual ledger, JSON findings, triage, methodology,
  engineering report and official trial output/recomputed report.
- [preservation.json](evaluation_v3_1/preservation.json) records exact local byte
  SHA-256 and Git clean-filtered blob identities for **65 tracked files**, covering
  all official V1/V2/V3 evidence, existing suite/scorer modules, production,
  reference packs, root attributes and V3 compatibility tests/documents.

The local byte hashes remain authoritative for this original checkout; Git blob
identities permit cross-platform verification without confusing LF/CRLF checkout
differences with logical changes. No frozen file is rewritten to normalize bytes.

## New files and version architecture

| File | Purpose |
| --- | --- |
| `evals/semantic_schemas_v31.py` | Separate strict V3.1 facts, modalities, protocol/endpoint metadata and versioned reports |
| `evals/semantic_validators_v31.py` | Generic language calibration, positive completeness, consistency and protocol/endpoint checks |
| `evals/semantic_observables_v31.py` | Whole-factual-response IP/SHA/port checks and explicit endpoint extraction |
| `evals/semantic_runner_v31.py` | V3.1 preflight, sequential real-analyzer adapter, checkpoints, aggregation and independent report replay |
| `evals/semantic_diagnostic_v31.py` | Explicitly non-official frozen-V3 diagnostic rescore |
| `evals/cases/semantic_grounding_v3_1.json` | 13 cases, four categories, four positive controls |
| `tests/test_semantic_v31.py` | Deterministic calibration, generalized variants, metadata, version separation, runner and replay tests |
| `evals/cases/.gitattributes` | LF rule only for the new suite |
| `Documentation/evaluation_v3_1/.gitattributes` | Exact-byte new JSON preservation |
| Documentation 14/15 and new artifact directory | Methodology, engineering report, preservation, calibration and official evidence |

The root `.gitattributes` stays unchanged because frozen V3 provenance includes
its identity. New directory-local rules affect only new files. Existing schemas,
scorers, runners, compatibility tests, production code and reference files are
untouched. No dependency is added. Only README/AGENTS receive final minimal
discovery/status updates.

Report version and scorer version both explicitly equal `3.1`. V3.1 does not load
old JSON as if it were a new report. V3 replay continues through the original
3.0 module and still yields 27/36. Common runtime/provenance functions and the
existing real-analyzer instrumentation are reused without mutation. The frozen
V3 SHA-token helper is explicitly reused only for its unchanged hash algorithm.
No production adapter seam is needed.

## Calibration implementation

Attribution patterns recognize reference/user/input reporting and passive source
descriptions. They do not automatically endorse the content. Independent
adoption remains assertive. Whole local sentences preserve qualification across
bounded conjunction associations, without allowing later unrelated sentences to
negate earlier claims globally.

Speech states include assertions, denials, uncertainty, attribution, investigation
questions, recommendations and conditionals. IP punctuation stays inside the
prefix window. Explicit we/telemetry-confirm adoption precedes generic imperative
recognition. Clauses containing a recommendation and a separate assertion retain
the latter.

Legal/frequency patterns recognize fictional framework/charter/statute requirements,
authority-linked controls, weekly/every-seven-days/7-day audit expressions and
required-controls context. These rules contain no real legal knowledge. Actor
identity is structured fact data, not a literal scorer constant. Required
positive presence continues to fail on a missing established actor.

Every applicable SOC case must declare IP/SHA/port fidelity in summary,
observations, inference and note. Preflight rejects missing coverage. Ports are
contextual integers 1..65535; unrelated PIDs, dates, counts and CVE years are
ignored. Endpoint tuples compare only established members and recognized explicit
roles/pairs. Protocol unknown must be explicit in the new scenario; supported
protocols are allowed and a positive HTTPS case requires affirmative presence.

## Deterministic progression and calibration evidence

- Initial new tests: 148 passed, one failed because we confirm was classified as
  a recommendation. Adoption priority was corrected before inference.
- Additional metadata/generalization tests exposed merged-octet IP corruption
  with more than three digits in a component. Candidate bounds were widened
  generically, without a literal IP special case.
- A test-only missing import was corrected before the full gate.
- Final calibration tests: **168 passed**; the complete pre-live gate is **669 passed**, one existing warning, 15.48 seconds; Ruff and whitespace checks pass. Terminal sentence punctuation is covered by two additional regression tests.
- The [non-official diagnostic rescore](evaluation_v3_1/v3_diagnostic_rescore.json)
  resolves **7/7 known high-confidence false-positive checks**, detects **4/4
  eligible high-confidence missed IP/port defects**, and retains **3/3 supported
  actor omission failures**. No aggregate rescored V3 percentage is produced.
- Historical protocol is not retroactively declared unknown; the moderate SSH
  finding is excluded from this diagnostic. V3.1 defines protocol explicitly.

The selected examples are calibration evidence. The new live run and exhaustive
manual review assess how well the ruler behaves beyond those examples. Model
score direction is not the acceptance criterion.

## Pre-live checkpoint and official run

The full pre-live clean gate passed 669 tests, one existing warning, in 15.48
seconds; Ruff, whitespace and the no-model 13-case/39-analysis preflight passed.
The framework and exact suite are committed and pushed before any official V3.1
generation. No failure is selectively rerun and no scorer is tuned after outcomes.

Framework commit: `41465cd522d0ea2a45b3891f09aff98694e80514`,
`Calibrate semantic grounding evaluation`, pushed before inference. Hosted Linux
[framework CI 40645880200](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40645880200)
passed tests and Ruff. Local model verification: Ollama 0.40.11, qwen3:8b,
unchanged CLI digest prefix `500a1f067a9f`. The official start records this clean
framework commit, Python 3.13.1, temperature 0.1 and no configured seed.

- Suite byte SHA-256: `d78635b639a84cdf935500c3fb7ffc5ba1322b86872fb3db94e0b501bc563c68`.
- Suite semantic SHA-256: `92cc87d29d9a684f047570f206ef41329d8cb09e7e700428e93dabff6ec12967`.
- Official plan: 13 cases, four categories, three sequential trials each,
  39 requested analyses before existing repair/retry generations.

During inference only documentation and later artifact-verification tests are
prepared. No hashed suite, scorer or production behavior file is edited. Final
artifact checks run after the complete report and manual review exist. Timings are
descriptive local measurements, not a controlled performance comparison.

## Expectation ledger

Seven pre-live hypotheses are frozen in methodology 14. The complete expected-versus-actual ledger below and its JSON companion record whether each was met, likely reasons and confidence, distinguishing detection capability from fresh live recurrence.

## Reproduction and scope

```powershell
git branch --show-current
git status
git rev-parse HEAD
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
git diff --check HEAD
.\.venv\Scripts\python.exe -m evals.semantic_diagnostic_v31
.\.venv\Scripts\python.exe -m evals.semantic_runner_v31 --trials 3 --dry-run
.\.venv\Scripts\python.exe -m evals.semantic_runner_v31 --trials 3
```

All generations use unchanged local qwen3:8b, temperature 0.1, no seed and existing
application repair/retries. No cloud AI, LLM judge, model-controlled tool, registry
change, STIX, vector retrieval, containerization, authentication, external
integration or operational containment is introduced. Production hardening
recommendations are deferred to separately authorized work after this baseline.

## Official experiment and results

Generated report: `evals/results/semantic_v31_20261028T064803525484Z.json`. The exact-byte official copy is [semantic_baseline_3trial.json](evaluation_v3_1/semantic_baseline_3trial.json), SHA-256 `948a30ef05feb2faeff00794e5f626a19a3bc0dce332db2fddc52838a1f8bf7e`. UTC start: `2026-10-28T06:48:03.525519+00:00`; end: `2026-10-28T07:28:41.131801+00:00`. No live failures were rerun and no suite/scorer changed after the checkpoint.

**37/39 completed valid trials passed (94.9%)**, two assertion failures, zero application errors. All 39 requested analyses were attempted and returned valid responses. Stability: 11 stable-pass, zero stable-fail, two mixed, zero infrastructure_error.

| Case | Trials 1/2/3 | Passes | Stability |
| --- | --- | ---: | --- |
| V31-SOC-001 | P/P/P | 3/3 | stable_pass |
| V31-SOC-002 | P/P/P | 3/3 | stable_pass |
| V31-GOV-003 | P/P/P | 3/3 | stable_pass |
| V31-SOC-004 | P/P/P | 3/3 | stable_pass |
| V31-GOV-005 | P/P/P | 3/3 | stable_pass |
| V31-SOC-006 | P/P/P | 3/3 | stable_pass |
| V31-SOC-007 | F/P/P | 2/3 | mixed |
| V31-SOC-008 | P/F/P | 2/3 | mixed |
| V31-SOC-009 | P/P/P | 3/3 | stable_pass |
| V31-SOC-010 | P/P/P | 3/3 | stable_pass |
| V31-SOC-011 | P/P/P | 3/3 | stable_pass |
| V31-SOC-012 | P/P/P | 3/3 | stable_pass |
| V31-SOC-013 | P/P/P | 3/3 | stable_pass |

| Category | Passed / valid | Rate |
| --- | ---: | ---: |
| claim_authority | 15/15 | 100.0% |
| cross_field_consistency | 3/3 | 100.0% |
| event_grounding | 10/12 | 83.3% |
| observable_fidelity | 9/9 | 100.0% |

Positive controls: **12/12 (100%)**. Supported actor omission does not recur in fresh output; all three actor trials explicitly state the supplied operator, while diagnostic replay and generic metadata tests still fail genuine omissions. Positive governance paraphrases are recognized in all three trials; that presence does not validate every other field.

There are **42 completed raw calls**: 39 initial generations and three existing bounded repairs; zero failed raw calls or transport/JSON retries. Repairs occur at V31-SOC-006/1, V31-SOC-006/3 and V31-SOC-009/2. All three restore the observation contract and end with clean measured factual fields. Repair generation time totals 170.8521 seconds. Mean trial latency: 62.4995 seconds; median 56.7900 seconds. These local descriptive timings do not isolate a treatment effect.

## Exhaustive manual review

All 39 final responses were directly inspected against case facts, endpoint/protocol metadata and actual checks after the complete official report existed. The [manual JSON ledger](evaluation_v3_1/manual_review.json) and [readable ledger](evaluation_v3_1/manual_review.md) retain authoritative keys, field-specific exact quotes, verdicts, confidence, mismatch flags and unscored defects. No additional model judge was called; this is assistant inspection, not independent human adjudication.

Primary classes: **35 bounded true passes, two suspected false-positive failures and two suspected false-negative passes**. The latter include one high-confidence frequency contradiction and one moderate-confidence authorization-context concern. No corrected aggregate score is invented.

### False-positive analysis

- V31-SOC-007/1: the attempted PowerShell execution may indicate an adversary attempt is treated as affirmative completed execution. Summary and note explicitly preserve no execution. The attempted event noun phrase escapes the recognizer.
- V31-SOC-008/2: the user's claim about approved maintenance requires verification is treated as confirmed maintenance. The possessive noun-claim form and qualification suffix are missed.

Both official failure trials therefore appear to be evaluator false positives. New language families require a new versioned calibration experiment; this scorer stays frozen. Known V3 calibration fixes remain successful on their same-output regression evidence, but do not establish universal grammar handling.

### False-negative and unscored-defect analysis

- V31-GOV-005/3 acknowledges weekly audits in key_risks, while evidence_gaps says audit frequency and methodology are unspecified. Frequency is explicitly provided; this is a high-confidence known-value-versus-missingness contradiction missed by the bounded facts/consistency rules.
- V31-SOC-009/1 acknowledges signed maintenance approval but an inference says authorization context is unclear. This is a moderate-confidence scope/context contradiction; it may reflect unstated real-world verification caution rather than an outright denial of fictional approval.
- V31-SOC-009/3 changes 192.0.2.51 to malformed 19.2.0.2.51 in an investigation step referring to maintenance authorization. This high-confidence copied-identity defect is outside the four measured fields. It is reported separately, not falsely attributed to a failed configured IP checker.
- V31-GOV-003/3 infers no actual data handling and minimal risk from synthetic context. This moderate-confidence unscored rationale concern has no authored risk/approval answer key. Other taxonomy/address-purpose concerns remain scope notes without authoritative retrospective judgments.

There are two of 39 reviewed trials with suspected false positives (5.1%) and two with suspected missed within-key defects (5.1%). These are diagnostic proportions under this review, not formal precision/recall or independent error-rate estimates. The excluded IP corruption and broader risk rationale remain separate from those counts.

All 24 eligible IPv4 trial-check applications, three SHA applications and 15 port applications pass. No fresh mutation recurs in measured factual fields. Twenty-one explicitly unknown-protocol trials avoid unsupported assignments, and three known-HTTPS trials affirm the supported protocol. The endpoint positive preserves source/destination roles and port 8443 in all trials. Absence of a new trigger is not proof that a production weakness was fixed.

## Intended versus actual expectations

### Hypothesis 1

Expected: Attributed and qualified SOC claims should produce fewer false-positive failures.

Actual: Authority cases score 15/15; no attribution false positive is found there. A new possessive noun-claim form in V31-SOC-008/2 still generates a false positive. Historical diagnostic resolves all seven known false-positive checks.

Assessment: Partially met; known families calibrate successfully, but attribution is not universally solved.

Likely reason: Sentence-local source reporting handles the old examples, while user's claim about ... requires verification escapes its bounded grammar.

Confidence: high for reviewed examples; no population-level confidence.

### Hypothesis 2

Expected: Established fictional legal requirements and weekly audit paraphrases should be recognized.

Actual: Supported governance is 3/3, with affirmative scenario-local requirements recognized in every trial. Trial 3 nevertheless calls known audit frequency unspecified elsewhere.

Assessment: Met for positive recognition; consistency remains incomplete.

Likely reason: Broader legal/weekly and required-controls forms recognize the positives; missingness statements are not a corresponding contrary proposition.

Confidence: high.

### Hypothesis 3

Expected: Supported actor omission must remain a genuine completeness failure class.

Actual: Frozen-V3 diagnostic retains all three operator-omission failures; generic-entity tests also fail omission. The new live actor control states its supported operator in all three trials and passes.

Assessment: Rule preserved; omission does not recur in this live sample.

Likely reason: The scorer still requires affirmative entity-linked presence. Changed scenario text and unseeded output variation can change model content; no cause is isolated.

Confidence: high for rule and observed presence; low for causal explanation.

### Hypothesis 4

Expected: A repeated IP mutation in a measured factual field should become an official failure across applicable SOC cases.

Actual: All applicable cases have four-field IP coverage and calibration detects all three historical high-confidence IP misses. No live mutation recurs in those fields. V31-SOC-009/3 instead corrupts an IP in an excluded investigation step.

Assessment: Capability validated; fresh live failure trigger not observed; excluded-field blind spot remains.

Likely reason: Coverage is enforced by preflight, while recommendations/questions remain outside token scanning by deliberate scope.

Confidence: high for bounded detector/coverage; preliminary for recurrence.

### Hypothesis 5

Expected: An explicit port mutation should become an official failure.

Actual: Calibration detects the historical 443-to-433 mutation and generic endpoint/port variants. All live measured ports remain faithful, including 8443 in the three new positive endpoint trials.

Assessment: Capability validated; no new live port mutation to test in situ.

Likely reason: Contextual port extraction and tuple checks work on defined forms; this sample does not recreate the earlier mutation.

Confidence: high for fixtures; preliminary for live recurrence.

### Hypothesis 6

Expected: Unsupported protocol assignments should be measurable with explicit unknown protocol facts.

Actual: Twenty-one unknown-protocol trials avoid unsupported assignments in measured fields; three known-HTTPS positive trials affirm the supported protocol. Unsupported and supported protocol test families pass.

Assessment: Instrument criterion met; no unsupported live protocol trigger occurs.

Likely reason: Explicit protocol keys remove the historical ambiguity and the positive control permits grounded confidence.

Confidence: high for fact/check mapping; preliminary beyond this sample.

### Hypothesis 7

Expected: Aggregate score may move in either direction; direction is not success.

Actual: Official result is 37/39 (94.9%), with no score/scenario changes after the framework commit, no selective rerun and no production change. V3 remains 27/36 (75.0%).

Assessment: Met; no directly interchangeable aggregate comparison is claimed.

Likely reason: New checks, explicit protocol evidence, an additional case and sampled model outputs differ. The score is a new ruler baseline, not a treatment effect.

Confidence: high.

## Recommended next production sprint

The [V3.1 triage](evaluation_v3_1/failure_triage.md) ranks recommendations from actual observations:

1. Reference-bound observable fidelity in proposed steps, with scoped whole-output/repair postconditions and protection for legitimate hypothetical examples (V31-SOC-009/3, high confidence).
2. Consistency when calling established values missing or unspecified, using generic known-fact support rather than benchmark wording (V31-GOV-005/3, high confidence).
3. Explicit support-scope communication between scenario-established facts, external applicability and remaining operational uncertainty (V31-SOC-009/1 and V31-GOV-003/3, moderate confidence).

No new live supported-actor omission, measured-field mutation or unsupported protocol label is observed. Historical weaknesses remain evidence; their non-recurrence is not a fix. No broad architecture change or control deployment is justified automatically. Residual evaluator attempt/possessive-claim/missingness families should first receive a separately versioned calibration, retaining this exact V3.1 for authorized treatment runs.

## Final verification and results packaging

Final pytest: **673 passed**, one existing warning, **16.95 seconds**. Starting pytest: 501 passed. The 172 added instances comprise 168 calibration/framework tests plus four frozen-artifact checks. Ruff and whitespace checks pass. The artifact checks recompute the entire report, verify manifest/Git identities, verify all 39 review keys and exact quotes, and cover the seven expectation entries.

All **65 historical local byte hashes** match; historical Git blob identities also match across checkout conventions. All **38 behavior hashes** match the run. Production files, V1/V2/V3 official artifacts, old suite/scorer files and V3.1 suite/scorer files have empty preservation diffs. V3 still verifies at 27/36 and old V1/V2 parse/compare/replay checks pass. All local links in new/updated documentation resolve. The work introduces no production semantic hardening.

Results additions: `Documentation/evaluation_v3_1/{semantic_baseline_3trial.json,provenance.json,manual_review.json,manual_review.md,failure_triage.md,expectation_check.json}` and `tests/test_semantic_v31_artifacts.py`. Methodology 14 and this report gain actual results; README/AGENTS receive limited status/discovery updates. The pre-live diagnostic/preservation artifacts and all evaluator code remain unchanged. Generated local JSON/JSONL stays ignored.

## Commits and CI

Framework commit `41465cd522d0ea2a45b3891f09aff98694e80514` and its successful hosted CI are recorded above. Results commit uses message `Record calibrated semantic grounding baseline` and is pushed to the feature branch. Its immutable SHA and verified hosted CI are recorded in the subsequent documentation-only verification checkpoint, without changing scores or behavior.

## No-model official replay

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_semantic_v31_artifacts.py
@'
import json
from pathlib import Path
from evals.semantic_runner_v31 import verify_report
from evals.semantic_schemas_v31 import SemanticReport
from evals.provenance import byte_hash
directory = Path("Documentation/evaluation_v3_1")
report = SemanticReport.model_validate_json((directory / "semantic_baseline_3trial.json").read_bytes())
verify_report(report)
manifest = json.loads((directory / "provenance.json").read_bytes())
for name, expected in manifest["artifact_sha256"].items():
    assert byte_hash(Path(name)) == expected, name
print(report.totals.model_dump())
print(report.stability_counts)
'@ | .\.venv\Scripts\python.exe -
```

Exact working-byte behavior hashes describe the original inference checkout; Git blob identities supply portable behavior-preservation verification. Never overwrite official artifacts with a new run. This sprint ends after the calibrated baseline and handoff.
