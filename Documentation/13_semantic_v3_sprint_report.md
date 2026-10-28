# Semantic Grounding V3 sprint engineering report

This sprint implements and freezes measurement of the current application. It
does not implement production semantic hardening. The teaching/review handoff
includes the [methodology](12_semantic_grounding_v3_baseline.md), official report,
provenance, exhaustive manual review and evidence-backed failure triage under
`Documentation/evaluation_v3/`.

## Starting state and authorization

- Branch: `feature/portfolio-hardening`, clean and synchronized with origin.
- Starting HEAD: `6117d4a4839dbfbe13864141ce45941df31c5299`.
- Recent history: `6117d4a`, `8efe3ec`, `717b82f`, `42f13d1`, `2309cb0`.
- Starting pytest: **398 passed**, one existing Starlette/httpx deprecation warning,
  6.49 seconds; Ruff and `git diff --check HEAD` passed.
- The user explicitly authorized evaluation schemas, validators, tests, docs,
  framework/results commits and pushes. No routine approval question was needed.
- Existing AGENTS instructions and the required V2 methodology, post-hardening
  triage, I/O technical document, sprint report and saved responses were read.

The empirical basis is the manual V2 review, not an unrelated new benchmark.
Reference-only C2/actor claims survived scoring; mandatory 7-day audit paraphrases
escaped a literal check; failure-only authentication became a successful login;
maintenance was promoted into authorization; IPs mutated outside observations;
and a 66-character hash evaded valid-SHA subset extraction.

## Preservation and implementation boundary

[preservation.json](evaluation_v3/preservation.json) records exact initial byte
hashes for every existing file under official V1/V2 result directories, plus both
old case files: **14 files**. Neither those artifacts nor historical validator
code was edited. V1 parsing/comparison and V2 replay tests continue to pass.

No file under `app/`, `dashboard/` or `reference_material/` changed. No dependency,
API route, response/prompt policy, retry configuration, model configuration, UI,
registry, environment, audit log, cloud call or operational integration changed.
No model judge, autonomous application agent or containment action was introduced.

## Framework files and responsibilities

| File | Responsibility |
| --- | --- |
| `evals/semantic_schemas.py` | V3-only typed facts, check metadata, matches, trial and report models |
| `evals/semantic_validators.py` | Clause-local proposition recognition, fact scoring, scoped fidelity and cross-field comparisons |
| `evals/semantic_runner.py` | No-model preflight, real analyzer adapter, sequential trials, checkpoint, aggregation and report verification |
| `evals/cases/semantic_grounding_v3.json` | 12 independent synthetic scenarios and answer keys |
| `tests/test_semantic_v3.py` | 99 deterministic test instances, no model generations |
| `.gitattributes` | LF V3 suite and exact-byte official V3 JSON preservation |
| `Documentation/12_semantic_grounding_v3_baseline.md` | Pre-live methodology, later measured results |
| `Documentation/evaluation_v3/preservation.json` | Initial historical artifact byte inventory |

Results packaging adds the official JSON, provenance JSON, manual review and triage,
this report, and minimal README/AGENTS discovery/status updates. Exact final file
inventory is available from the two sprint commits; generated local JSON/JSONL
under `evals/results/` stays ignored.

The results packaging also adds the JSONL ignore rule and corrects two CI test
assumptions, without changing the suite or scorer. Initial hosted framework CI
([run 40632277229](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40632277229))
failed: mocked CLI execution tests still required an installed model digest, and
the byte-preservation test expected Windows checkout bytes on Linux. An autouse
synthetic runtime fixture now isolates the tests from Ollama installation. The
preservation test compares Git clean-filtered historical blob identities across
platforms; original local byte hashes are retained unchanged and checked at freeze.
The initial manifest gains starting Git blob IDs, not replacement byte hashes.
These are test/packaging corrections, not semantic scoring defects; the official
live experiment is neither restarted nor rescored. Targeted verification after
the corrections: 99 passed, Ruff passed. Hosted final CI is recorded below.

### Facts, checks and positive controls

`SemanticFact` binds a unique proposition name to a strict boolean, a support
class, exact evidence text and optional permitted source IDs. The same proposition
may occur in multiple cases but cannot be duplicated within one case. Checks must
refer to defined facts, valid response fields and supported check kinds. Preflight
also validates requests, source identity/metadata and evidence presence.

False denotes an unestablished proposition in the closed record. True requires
telemetry or explicitly stipulated synthetic authority. This is an authored
scenario answer key; it is not a production truth or legal-authority engine.

Four checks cover fact grounding, explicit supported positives, observable
integrity and cross-field propositions. Three positive-control cases require
seven established propositions in aggregate: reputation/actor, legal/frequency,
and successful login/process execution/approved maintenance. An output that says
unknown to everything fails positive completeness even if it avoids overclaims.

`claim_matches` returns field, matched clause and assertion/denial/qualification.
`validate_semantic` compares those matches with the answer key, without asking a
model to judge its own or another model's response. `score_response` evaluates all
declared checks. The small lexical families and local negation/qualification
windows are deliberately incomplete and explainable.

### Malformed observables and consistency

`observable_issues` checks only configured factual fields. IPv4 preserves complete
numeric candidates, including five-component and empirically observed comma
insertion mutations. SHA logic accepts exact supplied 64-hex values, rejects
invented valid 64-hex tokens, and flags 56..72-character hex with at least 90%
sequence similarity to a supplied SHA. Unrelated malformed hex is ignored. This
does not change `app/observables.py` or old evaluator extraction.

Cross-field checks compare recognized assertion/denial states for each selected
proposition across field pairs. For an unestablished fact, assertion versus
explicit verification/uncertainty also counts as inconsistent confidence. The
result retains the relevant field pairs and matched clauses. It is not a general
contradiction solver and cannot infer unseen paraphrases or entity relations.

### Existing analyzer adapter and provenance

V3 creates an internal historical `EvaluationCase` carrier only to reuse V2's
existing real analyzer invocation, raw-call timing and opt-in stage tracing. Its
category/ID/schema-check outcome never becomes a V3 semantic score. V3 wraps the
returned final response or safe application error in its own typed trial record.
Empty explicit reference overrides disable retrieval; two negative authority
cases supply explicit synthetic cards. Other cases place evidence in the request.

`build_report` aggregates all valid outcomes, errors, categories, positives,
stability and model-call counts. `verify_report` independently reloads the suite,
validates response schemas, recomputes every check and rebuilds every aggregate.
Byte and canonical semantic suite hashes are checked on replay. File hashes at
start and end must match before any complete official report is written.

Provenance records Python, Ollama, qwen model/short CLI digest, temperature, absent
seed, clean framework Git SHA, suite hashes and relevant behavior/evaluator files.
No hidden reasoning or credential payload is captured. The manifest records exact
working-file bytes, which can differ with platform newline checkout behavior.

## Deterministic test progression and gate

- Starting repository: 398 tests passing.
- First V3 targeted run: 90 passed, one failed; a qualified process-execution noun
  phrase was not recognized. Its lexical family was extended before any live run.
- Targeted rerun: 91 passed.
- Runner/aggregation/error/tamper tests brought the full suite to **497 passed**.
- A nested preflight `if` was simplified to satisfy Ruff before the clean gate.
- Final pre-live gate: **497 passed**, one existing warning, 10.11 seconds;
  Ruff and whitespace validation passed.
- V3 dry-run: 12 cases, four categories, three trials each, 36 planned analyses;
  valid requests/facts/checks/references/fields and no generations.
- Production/history diff inspection was empty; all preservation hashes matched.

New tests cover metadata identity and strict booleans, supported/unsupported
reputation and actor claims, legal/frequency paraphrases, event state, maintenance,
positive anti-hedging controls, IPs in three factual fields, exact/extended/shortened
hashes, unrelated hex protection, consistency, field scope, dry-run, semantic
hashing, complete runner reports, scoring/aggregate/identity tamper rejection,
safe application errors, mid-run behavior-change refusal and frozen V2 replay.
Existing V1 tests retain their original parsing/comparison/check coverage.

## Framework checkpoint and official experiment

- Framework commit: `3a0a5f260b0df2a72d415cdf19eaa8025fedca87`,
  `Add semantic grounding evaluation V3`; pushed before inference.
- Suite byte SHA-256:
  `c1e2fa71445b83aa45a1254d7a8a18808ff125b7bfb2972c9e5d3270d989c056`.
- Suite semantic SHA-256:
  `473e3b7749cc303d604b1a38a0b49d8e4fa7b005604afce572f8e27950c4e4a8`.
- Runtime at official start: Python 3.13.1; Ollama 0.40.11; qwen3:8b;
  short CLI model ID 500a1f067a9f; temperature 0.1; seed not configured;
  worktree clean at framework commit.
- Three sequential trials per case; no selective failure reruns or post-result
  evaluator tuning. Existing SOC repair/transport retries remain observable.

During inference, a read-only `ollama ps` observation showed 4096 context,
llamacpp runner and 30%/70% CPU/GPU allocation. This is not a complete hardware
fingerprint. Documentation preparation and a short deterministic CI-test-fix
verification also occurred during the sequential run; timing is descriptive,
not a controlled performance comparison. These activities did not change any
hashed inference/evaluator file or overlap a second model-generation task.

### Official outcomes

The complete official experiment ran from `2026-10-28T04:25:58.338476+00:00` to `2026-10-28T05:09:09.137034+00:00`. It is an exact-byte copy of `evals/results/semantic_v3_20261028T042558338444Z.json`, frozen as [semantic_baseline_3trial.json](evaluation_v3/semantic_baseline_3trial.json). Its SHA-256 is `49ee78e3c889ab946ab2a6c0aa9c08b975569067081aeee3246018cfc845e122`.

**27/36 completed valid trials passed (75.0%)**; nine assertion failures; zero application errors; all 36 requested analyses attempted and completed. The all-attempt pass rate is also 75.0%. Case labels: seven stable-pass, two stable-fail, three mixed and zero infrastructure_error.

| Case | Trial sequence | Passes | Stability |
| --- | --- | ---: | --- |
| V3-SOC-001 | F/P/P | 2/3 | mixed |
| V3-SOC-002 | P/F/P | 2/3 | mixed |
| V3-GOV-003 | P/P/P | 3/3 | stable_pass |
| V3-SOC-004 | F/F/F | 0/3 | stable_fail |
| V3-GOV-005 | F/F/F | 0/3 | stable_fail |
| V3-SOC-006 | P/P/P | 3/3 | stable_pass |
| V3-SOC-007 | P/P/P | 3/3 | stable_pass |
| V3-SOC-008 | P/P/P | 3/3 | stable_pass |
| V3-SOC-009 | P/P/P | 3/3 | stable_pass |
| V3-SOC-010 | P/P/P | 3/3 | stable_pass |
| V3-SOC-011 | P/P/P | 3/3 | stable_pass |
| V3-SOC-012 | F/P/P | 2/3 | mixed |

| Category | Passes / valid | Rate |
| --- | ---: | ---: |
| claim_authority | 7/15 | 46.7% |
| cross_field_consistency | 2/3 | 66.7% |
| event_grounding | 12/12 | 100.0% |
| observable_fidelity | 6/6 | 100.0% |

Positive controls: **3/9 (33.3%)**. Supported reputation/actor and fictional governance are 0/3 each; confirmed login/execution/maintenance is 3/3. Six positive-control trial failures do not all mean the same thing: three are real omitted actor facts, and three contain supported governance positives missed by the evaluator.

There are **39 completed raw model calls**: 36 initial plus three repair calls, zero failed calls, zero transport/JSON retries. Existing repairs occur at V3-SOC-009/1 and V3-SOC-012/1-2; all succeed on the observation contract. Repair generations consume 223.9925 seconds. Valid-trial mean is 72.2157 seconds; median 61.0689 seconds. These descriptive timings include ordinary local workload and sampling variability.

### Exhaustive manual review and mismatch analysis

Every final response and its configured validator matches was directly inspected after the complete official report existed. The [manual ledger](evaluation_v3/manual_review.md) covers all 36 trials, with a [JSON companion](evaluation_v3/manual_review.json) containing exact fact metadata, field-specific quotes, assessments, confidence and mismatch flags. No separate LLM judge call was made. This is assistant diagnostic inspection, not independent human certification.

Primary classifications: **23 bounded true passes; three true positive-control failures; six suspected false-positive failures; four suspected false-negative passes**. Six trials contain seven false-positive check results. Five trials have missed defects: four passes plus V3-SOC-012/1, whose scored reason is itself a false positive. That overlap is explicit; no corrected aggregate replaces the official 75.0%.

- V3-SOC-001/1 and V3-SOC-002/2 attribute allegations to unverified references/user narrative, but clause splitting discards the qualification and fails them.
- V3-GOV-005/1-3 express the fictional legal framework requiring weekly audits. Narrow legal paraphrases and required_controls context are missed. Trial 1 has both legal and frequency false positives. Trials 2/3 also show scope/confidence tension between internal fictional authority and external verification.
- V3-SOC-004/1-3 omit the established operator name entirely. These are genuine positive-control completeness failures, not unsupported actor claims.
- V3-SOC-009/1-2 mutate inference IPs to 19,2.0.2.51 and 19.0.2.51; V3-SOC-012/1 mutates note IP to 193.0.2.51. No fidelity check is attached to those cases. Two occur after successful observation-contract repair.
- V3-SOC-010/3 changes destination port 443 to 433 in observations while summary retains 443. The configured IP check passes correctly; port/event consistency is unmeasured.
- V3-SOC-009/3 adds SSH to protocol-unspecified authentication. This is a moderate-confidence protocol-grounding scope gap; accepted-password wording can cue SSH, but the synthetic fixture does not establish it.
- V3-SOC-012/1 fails on Check if ... legitimate maintenance, an investigation question misread as an assertion. An intervening IP interrupts qualifier recognition. All nine dedicated cross_field check evaluations pass, and no genuine contradiction among that case's configured propositions is identified.

Dedicated IP/SHA cases pass 6/6 and actually copy target values in summary and observations. No SHA extension recurs. Those results do not establish whole-suite fidelity. No unsupported confirmed reputation/actor claim or fabricated weekly/legal mandate is identified in the nine negative authority trials under manual review; clearer explicit unverified cues limit comparison with V2.

### Empirical next-sprint priorities

The [failure triage](evaluation_v3/failure_triage.md) records each defect with case/trial, authoritative facts, actual claim, validator result, manual assessment, likely future layer and confidence. It ranks generic factual-field fidelity/repair postconditions first; supported-fact completeness and support-scope communication second; and event/protocol/endpoint grounding across fields third. These are proposals for separately authorized work, not controls implemented here.

Evaluator improvements must be a separate versioned experiment before relying on aggregate score changes. Preserve attribution and qualifications, handle IP punctuation, recognize bounded legal paraphrases and required-control context, and measure coverage across cases. Do not add benchmark-specific production phrases or force particular actor names. Freeze this V3 unchanged and rerun it for any later authorized treatment.

### Final local verification

Final pytest: **501 passed**, one existing warning, **11.31 seconds**. This adds 103 deterministic test instances over the 398-test starting state: 99 framework tests and four frozen-artifact checks. Ruff and `git diff --check HEAD` pass. All four artifact tests pass, verifying report recomputation, provenance/behavior identity, every review fact/quote and all 36 Markdown trial references.

All **30 inference/evaluator behavior hashes** match the official run. V3 suite bytes and scorer files are unchanged since 3a0a5f2. All 14 historical local byte hashes match their starting values; normalized historical Git blobs also match for cross-platform CI. V1 and V2 comparison functions parse/recompute successfully. Git diffs against the starting commit are empty for production, reference packs, dependencies, old suites, old validators and official V1/V2 artifacts. All local Markdown links in the new/updated handoff resolve. No production semantic hardening occurred.

Additional results files: `Documentation/evaluation_v3/{semantic_baseline_3trial.json,provenance.json,manual_review.json,manual_review.md,failure_triage.md}`, `Documentation/13_semantic_v3_sprint_report.md`, and `tests/test_semantic_v3_artifacts.py`. Packaging/status modifications: `.gitignore`, README, AGENTS, methodology 12, preservation manifest Git-blob metadata, and test runtime isolation in `tests/test_semantic_v3.py`. The framework/evaluator files remain unchanged.

### Results checkpoint and hosted CI

Framework commit and its initial hosted CI failure are recorded above. Results
commit: `49415c112052850f31e449299d75406aee53937c`,
`Record semantic grounding V3 baseline`, pushed to `feature/portfolio-hardening`.
Hosted Linux [CI run 40637087087](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40637087087)
completed successfully: tests and Ruff both passed. This confirms the runtime
isolation and cross-platform Git-blob preservation corrections without installing
Ollama or making a live model call in pytest.

This documentation-only verification checkpoint records the results SHA and
verified hosted CI after the immutable results commit existed. It changes no
suite, scorer, report, provenance, manual finding or production behavior. Both
sprint checkpoints and this verification record remain on the feature branch;
nothing was merged to main and no history was rewritten.

## Exact reproduction commands

```powershell
git branch --show-current
git status
git rev-parse HEAD
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
git diff --check HEAD
.\.venv\Scripts\python.exe -m evals.semantic_runner --trials 3 --dry-run
.\.venv\Scripts\python.exe -m evals.semantic_runner --trials 3
```

Live generation creates a new local experiment and must never overwrite official
artifacts. Replaying official reports is no-model verification, not a rerun.

After results packaging, replay the frozen V3 and verify review evidence with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_semantic_v3_artifacts.py
@'
import json
from pathlib import Path
from evals.semantic_runner import verify_report
from evals.semantic_schemas import SemanticReport
from evals.provenance import byte_hash
directory = Path("Documentation/evaluation_v3")
report = SemanticReport.model_validate_json(
    (directory / "semantic_baseline_3trial.json").read_bytes()
)
verify_report(report)
manifest = json.loads((directory / "provenance.json").read_bytes())
for name, expected in manifest["artifact_sha256"].items():
    assert byte_hash(Path(name)) == expected, name
print(report.totals.model_dump())
print(report.stability_counts)
'@ | .\.venv\Scripts\python.exe -
```

The manifest's `file_sha256` values describe exact local inference bytes. Compare
those only in the original checkout or an identically normalized checkout; use
the manifest's Git blob identities for cross-platform behavior preservation.

## Remaining scope

The sprint stops after freezing the V3 baseline and review. Empirically supported
future hardening targets are ranked in the failure triage and remain unimplemented. V1/V2 and this V3 suite/checkpoint must remain frozen. Any proposed new
semantic check or changed suite needs distinct provenance and a new experimental
baseline. Unrelated roadmap work remains deferred.
