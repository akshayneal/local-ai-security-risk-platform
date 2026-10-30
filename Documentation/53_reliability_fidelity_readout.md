# Sprint 8 reliability and information fidelity

Experimental reliability patch, no new features or release. Manual workflow,
launcher/final visual acceptance and independent semantic review remain PENDING.

## Source, preservation and diagnosis

Started from verified local/remote `feature/cross-pillar-rc-hardening` at
`e7f61f4e7f8b56e14c6cf0d65fa461aff3e79417`. Work branch:
`feature/reliability-fidelity-sprint8`. Stable main/peeled v2.3.0 remain
`fde00d0ca5d21eecbc6973cc784550ed453edb7a`.

The 405 original s4check files plus 185 caches, 13 Northstar files, all 36 files
in the original Sprint 7 official run and installed AGENTS bytes matched before
work. No inherited evaluation was active. They remain read-only: no s4check code
import/execution, no old database query/rebuild, no old run resume/replay or raw
outputs copied into new gold. No launcher/port/shortcut, reference pack, dependency,
environment, model/service, authorization, workflow or API endpoint change.

| Symptom | Verified cause / limits | Narrow correction and test |
| --- | --- | --- |
| Sprint 7 AI Security 0/4 returned | Raw provider outputs 9-12 completed but used insufficient_information with 3/4/2/3 findings. Python correctly rejected them. The model-visible schema did not encode that cross-field restriction. | Two provider-visible response variants encode the existing restrictions; raw payload is validated against variants and the original public response. Contradictory output still yields a fixed withheld error. |
| Shared prompt described only two workflows | Verified wording mismatch; contribution to model behavior is plausible, not isolated or proven. | Correct description to three existing workflows; explicitly distinguish reviewable architecture from missing implementation proof and valid benign zero findings. |
| Invented SOC infrastructure mismatch / overstated attack | Verified raw statements; finite identifier validation does not entail ownership or intent. | General prompt instructions retain unknown inventory/reputation/intent, scoped positive record facts and bounded hypotheses. No phrase/IP heuristic or broad semantic filter. |
| Unknown controls presented as absent | Verified raw governance summaries/gaps; no deterministic evidence-status interpreter exists for arbitrary prose. | Distinguish unknown/proposed/required/reported absent/established absent/implemented and preserve scope, positive approval and low-impact facts. Remains prompt-guided. |
| Selected documents not finally cited | Two logical document citations were correctly sanitized; this alone is not a citation bug. | Clarify exact envelope evidence_id. Temporary registered-source tests show an eligible relevant chunk survives with its version/authority, while a logical ID remains rejected. Selection/membership is not entailment. |

The fresh cases and rubric were committed at `e70b654` before application edits.
Implementation identity for inference: `40202f41ae59ca18077db882be0a6b6183f08ac8`.
The exact scope is [sprint8_preservation.json](sprint8_preservation.json).

## Before/after contracts and Python explanation

Only three application files change: `app/ai_security_contracts.py`,
`app/ai_security_analyzer.py` and `app/prompts.py`.

Previously the provider saw an independent coverage enum and a findings list;
an `after` validator enforced their relationship only after generation. Two small
Pydantic subclasses now describe the valid branches: advisory with 0-12 findings,
or insufficient with zero findings and at least one gap. A `TypeAdapter` generates
their `anyOf` JSON Schema. The analyzer validates raw output against that union,
then independently against the original public response. It never changes a raw
coverage value, discards findings, invents missing claims or upgrades authority.
The public API fields/enums, source alias compatibility, strict byte/JSON limits,
graph/source/category checks and no-actions/not-verified status remain intact.
Truly missing components/flows still return explicit gaps without generation.

Prompt tests verify that rules are outside quarantined input and preserve supplied
positive/unknown data. They do not prove that arbitrary model prose follows them.
No new SOC/governance semantic validator or automatic action is claimed. The
original SOC repair/identifier checks, Microsoft adapter, eligible knowledge opt-in,
Inspector identities/corrections, exports and runtime fail-closed behavior remain.

Five new regressions failed before the patch and passed afterward. Current-behavior
related batch: 319 passed, one existing warning, 10.16 s. Additional source/artifact
batch: 47 passed, one warning, 23.65 s. No real model calls in those tests.

## Prospective six-attempt run

The new [plan](../evals/reliability_v1/plan.json) freezes six distinct Maple cases:
OCR-to-HTML design, offline text translator, uncertain DNS lookup, a scoped approved
archive copy, proposed caption review, and an explicitly tested export prototype.
These are not replays/edited Cedar cases. SEC-A/B run first. Supporting facts are
inside synthetic input records; no live registered workspace or embedding is used.

One explicit foreground command, only after focused checks and implementation commit:

```powershell
.\.venv\Scripts\python.exe -B -m evals.reliability_v1.runner
```

The new adapter reuses the unchanged Sprint 7 HTTP transports, adding a locked,
durable GLOBAL cap of six generation requests, including SDK retries and SOC
repairs. It denies regeneration after the cap and marks later cases NOT RUN.
No warm-up, optional extra case, selective rerun or automatic resume. Model digest
must match the installed qwen3:8b. Metadata preflight is loopback-only; no service
start, download, proxy/redirect/cloud fallback. Temperature 0.1, num_ctx 8192,
180-second HTTP timeout, 1500-second deadline, 256 KB/response and 4 MB retention.
Timeout does not prove provider cancellation.

Fresh exclusive ignored root:
`knowledge_base/workspaces/maple-sprint8-live/sprint8-primary-001/`.
Synthetic full outputs stay there. Application audit writes are redirected to the
run's bounded journal; ordinary user audit logs and old workspaces are untouched.
Inputs/code/rubric use literal LF hashes and were checked through Git staging,
avoiding the earlier byte-transport defect. No prior frozen file was modified.

The run completed with **6 scheduled, 6 submitted, 6 raw generation attempts,
6 provider responses and 6 schema-valid HTTP 200 returns**. There were zero
retries/repairs, timeouts/unknowns, withheld returns, budget denials, NOT RUN cases,
embedding calls or extra live runs. The cap is exhausted; no further inference.
Both technical returns used `insufficient_information` with no findings:
**usable technical advisories 0/2**, despite sufficient declared architecture.
This is valid structured output, but fails the intended usefulness criterion.

| Case | Return and implementation-author finding |
| --- | --- |
| MAPLE-SEC-A | Insufficient, zero findings. OCR-to-model and generated-HTML-to-renderer facts survive, but the candidate concern is lost to false insufficiency. |
| MAPLE-SEC-B | Insufficient, zero findings. Offline/TEXT-ONLY fragments survive, but the full benign design, parser/escaped preview and human gate are not carried into analysis. No safety certification is warranted. |
| MAPLE-SOC-A | Low risk; DNS source, answer and absent subsequent actions retained. Unknown inventory stays a gap. A PowerShell citation is explicitly called irrelevant; membership does not establish useful support. |
| MAPLE-SOC-B | Low risk; supplied lab inventory, completed 23-file TLS transfer and narrow copy approval retained. Unsupported `Credential Access` mapping remains. |
| MAPLE-RISK-A | Low risk / needs review. Proposed curator review and low-impact context retained. Summary says it "lacks implemented controls" while a gap says "Implementation status of controls unknown": unknown is still promoted to absence. |
| MAPLE-RISK-B | Low risk / proposed approved decision. Known gate absence and implemented logging retained, but ten sample events and pilot approval scope are omitted. "human review is not explicitly required" contradicts the supplied review-before-publication rule. The proposed decision enum is not an actual approval grant. |

The predeclared 18 full expected facts were all assessable: **11 retained,
4 omitted, 3 contradicted**. Partial fragments do not count as full-fact retention;
for example RISK-B retains logging implementation but omits its sample count.
These are implementation-authored judgments, not independent adjudication, a
statistical accuracy/safety score, or a causal comparison with different Sprint 7
cases. No application/prompt or frozen case/rubric changes followed these outcomes.

Deterministic identity/schema/source-membership checks pass 6/6. There are 34
selected source occurrences and 13 cited occurrences; the technical returns cite
none and put guidance IDs in ordinary gap text (2/2). Valid IDs and a selected
reference do not prove entailment, authority, relevance or a useful answer. Local
knowledge was off: live results make no claim about registered-chunk citation
quality. The separate deterministic eligible-chunk tests establish only software
identity/provenance behavior.

Ollama 0.40.13, existing qwen3:8b, 8.2B Q4_K_M GGUF; digest
`500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
Submission wall time summed to 565.531125 s; provider-reported total durations
summed to 565.2291281 s (median 98.3933019 s, range 64.2169731-112.0679853 s).
These include loading/prompt/generation and are descriptive, not a controlled
performance claim. Per-case duration, source IDs, short synthetic excerpts,
review origin, model/runtime/source blobs and all 14 raw artifact hashes are in
[the machine readout](reliability_v1/readout.json). Full raw outputs stay ignored.

## Historical checks and final gates

Historic tests now call original backends from immutable tracked-only Git archives:
Sprint 6 AI Security at `1c4f937`, and the later historical wrappers/source checks
at `e7f61f4`. A bounded cached archive and scratch Git index live only under pytest
temporary storage. Process-local Git paths avoid changing the real index/config
or registering a worktree. No ignored/private/inherited executable content enters
the archive. Old runners, data, scorers, result files and manifests stay unchanged.

Six old test files change only replay call/decorator endpoints. New AST comparisons
preserve every original function body/assertion, other than explicit call/fixture
substitutions. The archived corrupt-snapshot negative still fails the original
verifier. A new active Sprint 8 guard checks exact current paths, every other base
blob, inherited sets and current mutation-negative controls. Historical replay is
not new semantic/model validation. Focused historical/current checks: 37 passed;
original AI Security replay: 4 passed, one existing warning, 9.99 s.

The first full-run terminal result was lost during context compaction; the next
run saved its output and reported 2023 passed / 1 failed, one existing warning,
136.37 s. The failure was the unchanged original SOC prompt hash guard in
`tests/test_microsoft_inventory.py`, which still hashed today's intentionally
changed prompt. Under Sprint 8 section 6, the exact scope contract was extended
by this one test path (baseline blob `27a6e2a88001f465779cc510329e2cd8bb528285`)
before editing it. Only its import/decorator now runs its original assertion and
digest in the immutable e7f61f4 source. All other current Microsoft tests remain
active. An additional AST comparison and an actual archived prompt corruption
test demonstrate that the hash/assertion is preserved and still rejects changes.
No application, prompt, model result, old frozen file or evaluation gold changed.
The final deterministic suite is repeated solely to verify this migration fix.

Final Windows gate: **2026 passed, one pre-existing Starlette/httpx deprecation
warning, 147.59 s**. Full `ruff check --no-cache .` passed; `pip check` reported
no broken requirements; `git diff --check` passed. No launcher edits, so no new
launcher-specific PowerShell run was needed beyond its existing full-suite tests.
Runtime: existing CPython 3.13.1, Windows 11 10.0.26300, pytest 9.1.1, Ruff 0.17.2,
Pydantic 2.13.4, FastAPI 0.138.0, httpx 0.28.1, requests 2.34.2, Ollama Python SDK
0.6.2. No dependencies were installed or changed. Every Python command used `-B`;
pytest cache was disabled, and final gates also set `PYTHONDONTWRITEBYTECODE=1`.
The saved final test log is task-owned temporary output outside the repository.
The protected sets and all 14 new live artifacts were rehashed successfully;
the inference source blobs and frozen suite literal hashes are unchanged.

Release candidate: **NO-GO**. Validated usable technical behavior remains
unproven, false insufficiency persists, and governance certainty/policy fidelity
and SOC mapping/citation quality still fail. Resolving these needs a separately
scoped intervention and a newly authorized prospective run; this sprint does not
tune or rerun against the observed failures. USER WORKFLOW QA / USER FINAL VISUAL
QA and independent semantic review remain PENDING. Do not merge/tag/release based
on green software checks alone.

## Reproduction and handoff

Use the existing Windows environment; do not rerun the live runner (its cap is
exhausted and its existing run directory refuses reuse). Deterministic commands:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests/test_reliability_evaluation.py tests/test_reliability_fidelity.py tests/test_sprint8_preservation.py
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B -m ruff check --no-cache .
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
```

Checkpoint 1: `e70b654e8aec4891a14107dd9c09d6dbe1f6dd13` freezes diagnosis,
scope, inputs, rubric, runner and budget before application changes. Checkpoint 2:
`40202f41ae59ca18077db882be0a6b6183f08ac8` contains narrow application changes,
regressions and historical/current guard migration. Checkpoint 3:
`d42c3819b63800a016618bc6f765a7e135cc729e` fixes only the additional legacy prompt
guard endpoint and adds its AST/mutation proofs (17 focused tests passed, 16.32 s;
scoped Ruff and diff checks passed). The final documentation commit
contains the screened new readout, this report and the README status correction;
its exact SHA, remote match and exact-commit Actions result are supplied in the
final handoff. No PR, merge, main change, release tag or publication is authorized.

Exact 26 changed/new paths relative to the starting commit:

| Purpose | Paths |
| --- | --- |
| Plan and preservation | `Documentation/52_reliability_fidelity_sprint_plan.md`, `Documentation/sprint8_preservation.json` |
| Status and outcomes | `README.md`, `Documentation/53_reliability_fidelity_readout.md`, `Documentation/reliability_v1/readout.json` |
| Application | `app/ai_security_contracts.py`, `app/ai_security_analyzer.py`, `app/prompts.py` |
| New frozen suite | `evals/reliability_v1/.gitattributes`, `evals/reliability_v1/__init__.py`, `evals/reliability_v1/plan.json`, `evals/reliability_v1/cases.json`, `evals/reliability_v1/rubric.md`, `evals/reliability_v1/freeze.json`, `evals/reliability_v1/runner.py`, `evals/reliability_v1/transport.py` |
| Current tests and replay helper | `tests/test_reliability_evaluation.py`, `tests/test_reliability_fidelity.py`, `tests/test_sprint8_preservation.py`, `tests/sprint8_history.py` |
| Narrow historical endpoint migration | `tests/test_sprint4_preservation.py`, `tests/test_sprint7_preservation.py`, `tests/test_ai_security_evaluation.py`, `tests/test_knowledge_evaluation.py`, `tests/test_cross_pillar_evaluation.py`, `tests/test_microsoft_inventory.py` |

All other baseline tracked blobs are guarded unchanged. The 590 s4check files,
13 Northstar files, AGENTS and 36 Sprint 7 raw artifacts remain hash-identical,
unstaged and uncommitted. The new official run is also ignored and hash-verified.
The inherited 405 untracked snapshot files remain visible; this is not a wholly
clean worktree claim. No `.gitignore` edit, cache cleanup or protected code import.

User-only acceptance remains pending. In a separately authorized manual session,
use the existing development Start/Stop shortcuts, verify three workflow routes,
inspect source identity and correction-first exports, and review sufficient and
benign technical designs alongside unknown/positive SOC and policy records. Do
not generate more model outputs under Sprint 8. Independent review should first
compare these frozen inputs with the preserved six outputs and the author labels.
Next scope should address false insufficiency and scoped evidence-state fidelity
with a new preregistration and budget, followed by manual acceptance. No new
features are introduced here.
