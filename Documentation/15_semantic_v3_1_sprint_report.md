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

The full clean gate, framework commit, suite hashes, official runtime, every case
result and final verification are recorded after the corresponding checkpoints.
The framework and exact suite are committed and pushed before any official V3.1
generation. No failure is selectively rerun and no scorer is tuned after outcomes.

## Expectation ledger

Seven pre-live hypotheses are frozen in methodology 14: fewer attribution false
positives; better supported-governance recognition; preserved actor-omission
failure; official out-of-field IP failure; official port failure; measurable
unsupported protocols; and no required aggregate-score direction. Final results
record expected versus actual, whether met, likely reasons and confidence for each.

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
