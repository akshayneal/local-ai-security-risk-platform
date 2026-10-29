# Analyst product experience

The 2.3.0rc1 dashboard opens on **Overview**, then groups **SOC Investigation**
and **AI System Risk Review** under Workflows, and **Platform Evaluation**,
**Activity** and **About** under Platform. Overview shows two active and two
planned workflow families. Planned cards have no forms or analysis routes.
The release-candidate wording and native architecture are documented in
[professional release candidate](22_professional_release_candidate.md).

## Run and explore

From the repository root, use the existing environment and local configuration:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard/streamlit_app.py --server.address 127.0.0.1
```

Open `http://localhost:8501`. Platform Evaluation and About need neither FastAPI nor
Ollama. The input pages load bundled synthetic data without inference. An
analysis submission requires the backend and the configured Ollama model. The
sidebar's **Check backend status** checks FastAPI readiness only, not model
readiness. Activity explains when the backend is unavailable.

## SOC Investigation

Three synthetic alerts come from `sample_data/soc_alerts.csv`. The sample loader
parses the JSON-encoded `known_indicators` column and validates every row with
`SocAlertRequest`. Select a sample and press **Load sample** to populate all seven
fields. The first sample is prefilled. Malformed or unavailable sample files
produce a fixed warning while leaving manual input available.

Submitting the form produces a severity/provisional incident header and summary,
then separate **Observed Evidence** and **Analyst Inferences** columns.
Investigation, response recommendations, and context/mapping tabs separate gaps,
steps, containment, false-positive considerations, MITRE-style mapping and analyst
note. Mapping is model-proposed, not STIX-validated. Recommendations execute no
actions. Model/input prose is rendered as text, without active Markdown links.

The **Response checks** panel sits beside the analysis. It exposes the final
SOC contract, recognized identity/endpoint checks, source sanitization, schema
and nonempty-observation checks, repair usage and required human review. Its
expander explains that bounded contracts do not establish every statement's
truth. The observation contract requires nonblank observations; it is not a
universal entailment judge. Critical identity/endpoint checks have the finite
grammar documented in [semantic hardening](18_semantic_production_hardening.md).

The result persists through download and tab reruns without another model call.
Its submitted case identity remains visible even if form values are edited.
Loading another sample or submitting another analysis clears the previous result;
a failure cannot leave a stale downloadable success presented as the new result.
This is session state, not a saved case-management database.

## AI System Risk Review

Two synthetic use cases come from `sample_data/ai_use_cases.json`, validated using
`GovernanceRiskRequest`. Loading fills purpose, data, users, integrations,
oversight and business impact. Results distinguish proposed risk/decision,
concerns and missing evidence, required controls/logging, and human oversight/
next steps. A proposed `approved` decision still requires authorized human review.

The **Validation** panel claims only schema validation and source
sanitization. Authority, applicability, support scope and factual accuracy remain
prompt-guided. The SOC identity/endpoint contract does not apply to governance.

## UI-oriented API and metadata

Existing `POST /analyze/soc-alert` and `POST /analyze/governance` retain their
original request models, successful analysis JSON and generic analysis-error
behavior. New endpoints use those same request models:

| Endpoint | Successful body |
| --- | --- |
| `POST /ui/analyze/soc-alert` | `analysis: SocAlertResponse`, `metadata: SocMetadata` |
| `POST /ui/analyze/governance` | `analysis: GovernanceRiskResponse`, `metadata: GovernanceMetadata` |
| `GET /ui/status` | Backend status, existing application version, configured model |

Metadata is constructed by the backend, never copied from model output. Both
workflows report the configured model, local execution, required human review,
and checks actually applied by their production analyzer. SOC additionally has:

| Field | Meaning on successful response |
| --- | --- |
| `integrity_status: "passed"` | The final production SOC contract accepted the returned analysis |
| `repair_attempted: false`, `repair_succeeded: null` | Initial generation passed; no policy repair used |
| `repair_attempted: true`, `repair_succeeded: true` | One repair was used and its final response passed the full contract |

`ProductTrace` reuses the existing analyzer's repair flags but discards every
stage capture. It never retains raw generations, prompts or violation snapshots.
No trace is serialized into envelopes, exports or audit entries. Existing model
transport/JSON retries are distinct from the single bounded policy repair.

Only the new UI SOC route maps `OutputPolicyError` to HTTP 500 with:

```json
{
  "detail": {
    "code": "integrity_validation_failed",
    "message": "The generated analysis could not satisfy the application's factual-integrity contract after one repair attempt. No analyst result was returned."
  }
}
```

No violating value, prompt or exception internals accompany that error. Other
analysis exceptions remain generic. The UI recognizes the code and uses its own
fixed message rather than echoing backend error prose. Input validation has a
fixed form-review message; connection failures explain service availability.
The 300-second UI request timeout does not cancel backend inference: the UI asks
the viewer to check Activity before resubmitting. No backend generation deadline
was added.

Old and new routes share small analysis/audit helpers. Each completed or failed
analyzer invocation is audited once using the unchanged JSONL format. Request
validation failures occur before analyzer/audit execution, as before. Repair
metadata was deliberately not added to the audit format.

## Sources and exports

Source expanders show title, family/framework, source ID and relevance, with a
warning that retrieval provides context rather than authority for every claim.
Source IDs remain in the structured references and audit `source_ids`.

Each successful analysis offers JSON and Markdown downloads. Pure helpers
project typed request/response models into a brief containing a UTC generation
timestamp, submitted case identity, analysis sections, references and human-review
disclaimer. SOC identity includes alert ID/type and affected asset; governance
identity includes system name. Exports omit raw input logs, internal prompts,
diagnostics and traces. Markdown escapes model/input markup. Analysis prose can
still contain sensitive supplied facts; review exports before sharing.

## Platform Evaluation

The read-only catalog loads explicitly named tracked frozen JSON artifacts. It
does not import evaluators, run models, rerun suites or rescore outputs. It shows
V1 baseline/treatment, V2 repeated baseline and I/O treatment, V3, V3.1, V3.2
baseline and V3.2 production treatment, with purposes, counts, errors, stability
and lessons. Missing/corrupt artifacts produce safe warnings.

Cross-version percentages are **not directly comparable**. The V3.2 comparison
verifies matching recorded byte/semantic suite hashes and scorer version, and
projects the existing `treatment_comparison.json` aggregates and 14 case
transitions. It displays 32/42 baseline, 37/41 valid treatment and 37/42 attempted
treatment passes; errors 0 to 1, stable-fail 2 to 0, positive controls 9/15 to
13/15, repair generations 4 to 6, mean attempt latency 65.31 to 81.29 seconds.
Case 006's error/pass/pass label is explained explicitly. No misleading trend
chart, raw response/trace browser or replacement manual-review percentage exists.

The security story explains injection, poisoning, source and evidence integrity,
claim authority, grounding and consistency. Limitations include small synthetic
suites, three unseeded trials, local-model scope, scorer mismatches and missed
defects, no statistical safety guarantee, finite identity grammar, latency/
availability costs and remaining human judgment.

## Activity and About

Activity reads the 100 most recent audit entries with workflow and outcome
filters. It projects timestamp, workflow, model, input/result summaries,
success/failure and source IDs. Stored internal error strings never enter the
normal page; failed rows use fixed language. Existing `/logs` compatibility and
on-disk error storage remain unchanged.

About uses native Streamlit columns and bordered containers for its architecture. It shows request validation, retrieval, quarantine, local model,
source processing, separate SOC/governance paths, full SOC contract, bounded
repair/fail closed, audit and human review. It lists local inference, human review and operational boundaries. There is no authentication
or multi-user boundary; run this demo locally.

## Preservation and release boundary

[Productization preservation](productization_preservation.json) inventories
unchanged evaluation evidence, evaluators, analysis implementation, schemas,
samples, references and dependencies. Historical UI/plumbing identities are
verified at the starting commit only for the three explicitly authorized changed
paths. Frozen manifests, report/scorer meanings and evaluation test assertions
remain intact. No semantic hardening, V3.3, dependency, registry or roadmap feature
was introduced.

See the [sprint report](21_productization_sprint_report.md) and
[demo walkthrough](demo_walkthrough.md). Release-candidate README restructuring is complete. Human visual approval, screenshots, merge and tagging remain pending.
