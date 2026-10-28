# Analyst productization sprint report

## Starting state and scope

Started on clean, synchronized `feature/portfolio-hardening` at
`c5e187e4e9bb02f5e1ce666b84716fa72e66c820`. The exact requested starting branch,
status, HEAD and six-commit history were verified before edits. Baseline:
**1,194 passed**, one existing Starlette/httpx deprecation warning, **39.81s**;
Ruff and `git diff --check HEAD` passed. Starting hosted CI was also successful.

This explicitly authorized productization sprint implements analyst/demo
experience and documentation. It does not change prompts, semantic/identity
validators, analyzers, model settings/retries, retrieval, schemas, document
registry, dependencies or frozen evaluation evidence. No final release, tag or
merge is performed. Recommendations remain human-reviewed proposals.

## Files and design decisions

| Files | Purpose |
| --- | --- |
| `app/main.py` | Shared analysis/audit plumbing, separate UI routes and backend status |
| `app/ui_schemas.py` | Typed envelopes, allowlisted metadata, fixed policy-failure message, snapshot-free repair flags |
| `dashboard/streamlit_app.py` | Readable entrypoint, five-page navigation and explicit backend-status check |
| `dashboard/workflows.py` | Validated forms, sample loading, results, integrity/source presentation and downloads |
| `dashboard/product_pages.py` | Evaluation Lab, filtered Activity and About/architecture |
| `dashboard/sample_loader.py` | Typed CSV/JSON sample parsing, selection and form conversion |
| `dashboard/api_client.py` | Bounded HTTP calls and safe error translation |
| `dashboard/presentation.py` | Pure integrity labels, trust/source caveats and audit projection/filtering |
| `dashboard/exports.py` | Typed identity/analysis projection, JSON and escaped Markdown briefs |
| `dashboard/evaluation_catalog.py` | Read-only frozen artifact summaries and bounded V3.2 comparison |
| `dashboard/__init__.py` | Presentation package |
| `tests/test_ui_api.py` | Real analyzer contracts through UI envelopes with fake model generations |
| `tests/test_product_helpers.py` | Samples, exports, safe errors, catalog, integrity labels and audit filters |
| `tests/test_dashboard.py` | In-process Streamlit navigation, form, result, repair/error and export smoke checks |
| `tests/test_product_preservation.py` | Freeze inventory and authorized source-boundary checks |
| `tests/historical_identity.py`, `tests/test_semantic_treatment_compare.py` | Historical source verification for the explicitly authorized changed UI/plumbing paths |
| `Documentation/productization_preservation.json` | 102 unchanged tracked paths plus three authorized prior source identities |
| `Documentation/20_analyst_product_experience.md` | Product/API semantics, usage and limitations |
| `Documentation/demo_walkthrough.md` | Five-minute local demonstration script |
| This report and `README.md` | Sprint evidence and moderate product-status update |

No frontend framework, custom theme dependency or graphics dependency was added.
Existing Streamlit columns, containers, tabs, tables, expanders and graph rendering
provide the interface. Model/input prose uses plain text. The integrity panel
sits beside analysis; no universal trust/confidence score appears.

All three SOC and both governance samples validate against the existing request
models. The UI parses JSON-encoded SOC indicator lists, populates every field and
clears stale results when a new sample/submission replaces them. Downloads and
other reruns retain the submitted result without repeating inference. Export
timestamps remain stable for that result.

## Endpoint compatibility and trust semantics

Existing `/analyze/soc-alert` and `/analyze/governance` successful response JSON,
request/response models and generic analysis-error behavior remain compatible.
The new `/ui/analyze/soc-alert` and `/ui/analyze/governance` return typed
`analysis`/`metadata` envelopes. `/ui/status` reports backend readiness, existing
version and configured local model without contacting Ollama. The existing
application version is retained; release versioning remains deferred.

Old/new routes share analysis/audit helpers; a normal completed or failed
invocation produces one audit entry. The format remains unchanged. Governance
metadata reports schema/source processing, model, local execution and required
human review. SOC also reports full bounded-contract acceptance and factual
repair flags. `ProductTrace.capture` discards every stage value, so UI execution
does not retain raw diagnostic snapshots. No raw output, prompt, hidden reasoning,
policy details or filesystem path is serialized as product metadata.

Only the UI SOC endpoint maps known `OutputPolicyError` to the fixed
`integrity_validation_failed` code/message. It withholds analysis after the
existing single failed repair. Unrelated analysis exceptions remain generic.
The dashboard never echoes server error prose and removes an earlier result on
failure. No fail-open fallback, third generation or semantic UI workaround exists.

## Evaluation and preservation

Evaluation Lab reads eight frozen run summaries spanning the seven requested
stages, including both V1 runs. It projects official counts, errors, stability and
lessons without running evaluators. Cross-version comparison limits are prominent.
The unchanged-suite V3.2 panel shows valid/attempt denominators, errors,
positive controls, repair/latency cost and 14 per-case transitions. Case 006's
two passes plus an error are explicit. Raw trial responses/traces are not shown.

All frozen V1/V2/V3/V3.1/V3.2 baseline/treatment evidence, suites and scorers remain
unchanged. Existing official artifact/replay tests continue to check original
scoring meanings. The new inventory additionally protects 102 tracked files,
including 79 frozen evidence/evaluator paths, all analysis implementation except
authorized route plumbing, original schemas, samples, references and dependencies.

Prior preservation inventories pinned UI/plumbing source bytes. The historical
helper now verifies only `app/main.py`, `dashboard/streamlit_app.py` and
`tests/test_dashboard.py` at this sprint's starting commit for those old assertions.
Frozen manifests were not edited. Every other frozen path remains current-file
checked. New endpoint/UI tests cover the changed behavior; historical outcomes
are neither weakened nor recalculated. No V3.3 or post-smoke model-wording tuning.

## Deterministic checks and smoke evidence

All pytest runs use the repository virtual environment and need no model,
internet or running Streamlit server. Targeted progression: **71 passed** on the
first product group; **1,263 passed** in the first full regression (**45.98s**);
then **78 passed** (**22.03s**) after additional source/trace-leak, corrupt-artifact
and HTTP-body checks. The full final suite has 1,270 cases, a net increase of 76.
The original two dashboard tests were expanded into 12 product smoke instances;
legacy missing-field rendering remains covered separately. No identity/scorer
regression test was removed or relaxed.

The targeted tests verify no-repair and successful-repair metadata through real
SOC analyzer validation; complete failed repair; old generic policy errors;
unrelated generic errors; no trace/output/source-metadata leakage; governance
check scope; exactly-once audit calls; sample loading and malformed files; both
brief formats; all pages without inference; stale-result removal; audit filtering;
catalog counts, suite identity mismatch and missing/corrupt artifact warnings.

One synthetic live call per new workflow was then made sequentially through local
FastAPI and the real configured `qwen3:8b` Ollama analyzer, with no configuration
changes or warm-up generation:

| Endpoint / sample | HTTP | Elapsed | Result |
| --- | ---: | ---: | --- |
| `/ui/analyze/soc-alert`, `SYNTHETIC-SOC-001` | 200 | 110.65s | Envelope validates; final contract passed; no policy repair; four sources |
| `/ui/analyze/governance`, synthetic policy draft assistant | 200 | 108.37s | Envelope validates; schema/source-only checks; four sources |

These are smoke checks, not official evaluation trials or a new quality score.
No generation was repeated to obtain preferred wording. The real Streamlit
`/_stcore/health` and FastAPI `/ui/status` returned HTTP 200. These endpoint smoke
calls use normal local audit logging. Generated logs remain ignored/uncommitted.

All five pages were executed through Streamlit AppTest. Visual browser inspection
was attempted but blocked: the in-app browser host was unavailable, then Computer
Use stopped because URL-policy enforcement was unsupported for the Windows
Firefox browser. No further UI automation was attempted. **No screenshot assets
were created and no pixel-level visual review is claimed.** Final screenshots
and desktop/mobile visual inspection remain release-polish tasks.

Pre-commit gate: **1,270 passed**, one existing warning, **55.53s**; full-repository
Ruff and `git diff --check HEAD` passed. Changed Python files also pass a scoped
format check; frozen files were not reformatted. New documentation local links
resolve. The 102-file preservation test and all existing artifact checks pass.
Hosted verification is recorded in the closeout section below.

## Remaining release tasks and limits

The product is ready to enter a separately authorized release-polish sprint,
subject to the explicit visual QA gap. Inspect desktop/narrow layouts, capture
honest screenshots and a recorded demo, complete recruiter-facing README polish,
confirm clean-clone setup and demo pacing, then separately authorize any merge,
tag or release. This sprint stops before those actions.

Local inference takes meaningful time; the 300-second UI timeout can occur while
backend work continues, and no generation cancellation/deadline was added.
Fail-closed rejection intentionally costs availability. Deterministic identity
grammar is finite; domains/IPv6, unrecognized endpoints, copied identifiers such
as `alert_id`, governance identifiers and universal support/completeness are not
newly validated. Governance semantics, MITRE mapping, support-scope ambiguity,
formatting and provisional classifications still require review. Frozen scores
retain known scorer false positives/missed defects. Three unseeded synthetic
trials provide no statistical safety guarantee. The demo has no authentication
or multi-user boundary. No cloud calls, external integrations or deferred roadmap
features were introduced.

## Commit and hosted closeout

Implementation and product documentation commit:
`efa2b14bf47934add15dddc0f78da037660961b3` — **Build analyst product experience**,
pushed to `feature/portfolio-hardening`.
[Hosted CI 40785826248](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40785826248)
completed successfully: dependency setup, full pytest and Ruff all passed on
Ubuntu/Python 3.13. The subsequent documentation packaging commit records this
verification without changing product code. Final-HEAD verification is also
reported in the implementation handoff.

The implementation worktree was clean after push; explicit Git comparisons
against the starting commit found no change to frozen evaluation folders,
`evals/`, analyzers, prompts, validators, original schemas, trace implementation,
retrieval, Ollama client, audit logger or dependencies. Temporary Streamlit and
FastAPI smoke servers were stopped; the existing Ollama service/configuration
was left intact. No generated logs or local-only files were staged.

Release-polish recommendation: **ready**, with visual QA/screenshots and the
documented reliability limits remaining explicit. No merge to `main`, branch
deletion, force push, tag or final release was performed.
