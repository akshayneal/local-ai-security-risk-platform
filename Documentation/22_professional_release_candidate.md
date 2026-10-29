# Professional release candidate: 2.3.0rc1

This candidate presents two active analyst workflows within a four-workflow
product direction. It is prepared for human visual approval. No merge to `main`,
release tag or deployment is part of this sprint.

## Information architecture

Streamlit's native `st.navigation` groups file-backed `st.Page` entries:

```text
Overview                 default landing page
Workflows
  SOC Investigation
  AI System Risk Review
Platform
  Platform Evaluation
  Activity
  About
```

`dashboard/navigation.py` contains the page groups and product-map descriptions.
Six small files under `dashboard/pages/` call the existing presentation functions.
This keeps routing native and lets AppTest switch real pages with its supported
`switch_page` method. There are no prefixed labels, fake disabled pages, custom
navigation CSS or external frontend packages.

Overview opens with a factual description, followed by native columns and bordered
cards. Technical and policy/governance columns span Security Operations and AI
Security rows. Active cards link to working pages; Planned cards contain only a
title, status and description. They cannot submit an analysis.

| Domain | Technical | Policy / governance |
| --- | --- | --- |
| Security Operations | SOC Investigation — Active | SOC Policy & Governance Review — Planned |
| AI Security | AI Security Assessment — Planned | AI System Risk Review — Active |

SOC Investigation analyzes supplied security telemetry and presents observations,
inferences, gaps, investigation steps and conditional response guidance. AI System
Risk Review assesses an AI system/use case for governance, security, privacy and
operational risk. The planned SOC policy workflow concerns procedures, escalation,
approval and documentation/evidence constraints. The planned AI technical workflow
concerns attack surface, injection, poisoning, authorization, controls and testing.
Neither planned workflow has endpoints, forms, fake results or partial runtime
implementation.

## Professional copy and presentation

The copy audit covers navigation, page headings, inputs/results, validation,
sources, errors, empty states, exports and current documentation. The sidebar's
“The model proposes. Humans decide.” and About's longer philosophical statement
were removed. The SOC introduction now describes analysis rather than inviting
the viewer to “turn” evidence into a brief. No replacement slogan was added.

Governance Review is now **AI System Risk Review** in current navigation, page
titles, exports and employer-facing guides. Internal governance request/response
models and endpoint names stay unchanged. Evaluation Lab is now **Platform
Evaluation**, explicitly described as this application's frozen test/hardening
history. Historical sprint reports retain the names used at the time.

SOC retains the functional input/results workspace with shorter Investigation,
Response and Context tabs. The incident type is labelled as a model proposal.
The **Response checks** panel reports final contract, schema, source references,
critical identifiers, endpoint relationships, nonempty observations, repair and
human review. AI System Risk Review uses **Validation**, with schema/source
processing and required review only. It does not claim SOC semantic guarantees.

Labels use Passed, Validated, Not required, Successful repair, Required and
Unavailable. Successful repair appears in the checks table without a second
reassurance banner. A single About these checks expander states that the checks
do not independently verify every conclusion. Broader technical limits sit in
About/documentation, not beside every ordinary result.

The UI's known policy-error display starts **Analysis withheld** and describes
failed checks after one repair. Backend error codes/messages and analysis endpoint
behavior are preserved. Other failures remain generic, and stale downloads are
cleared. Empty lists use None provided. Source expanders retain source family,
ID and relevance with one concise context/authority explanation. Exports retain
all analysis sections and review notices under the updated workflow name.

Activity is explicitly platform activity, not an incident queue. Existing workflow
and outcome filters remain, with practitioner-facing workflow names in the table.
Raw stored error strings remain excluded from the normal view. Backend status is
an explicit sidebar control with restrained availability/version/model text.

## About and native architecture

The old Graphviz diagram is completely removed. There is no architecture image,
SVG/PNG substitute, fixed white canvas or fullscreen requirement.

Native columns and bordered containers show request validation, local reference
retrieval/untrusted-content handling, configured local Ollama inference, separate
SOC and AI-system-risk processing, then audit/result/export with human review.
The SOC branch describes bounded checks, one policy repair and withholding failed
output. The risk-review branch describes schema/source processing and prompt-guided
analysis without the SOC identifier/endpoint contract.

About now has Product scope, Architecture, Current release and Operational
boundaries, plus an optional Validation limits expander. It lists local inference,
no cloud AI API, no automatic actions, no live threat intelligence, no multi-user
authentication boundary and required human review. All components inherit
Streamlit's theme; no custom colors, HTML tables or architecture graphics are used.
This supports dark/light themes by construction, but pixel-level appearance is
still subject to human inspection.

## Platform Evaluation

The page remains read-only. Its concise version-comparison warning appears once.
History includes both V1 runs, V2 baseline/I/O treatment, V3, V3.1 and V3.2
baseline/treatment. The exact-suite V3.2 comparison retains official counts,
valid/attempt denominators, errors, stability, positive controls, repair/latency
cost and all 14 case transitions. The error/pass/pass case remains explicit.
The progression uses factual labels from adversarial testing through production
semantic treatment. No evaluator, arbitrary-model service or model call was added.

## README and demonstration

The README is restructured around current workflows, product direction,
architecture, evaluation highlights, setup, tests, limitations and documentation.
Detailed historical/evaluation reports remain linked and unchanged. The
[demo walkthrough](demo_walkthrough.md) now follows Overview → SOC Investigation →
AI System Risk Review → Platform Evaluation → About.

## Reproducibility and versioning

`requirements.txt` is unchanged and remains the readable direct manifest.
`requirements-windows-py313.lock.txt` includes that manifest and pins 79 exact
resolved packages. It was generated with `pip freeze` from a fresh Windows x64 /
CPython 3.13.1 virtual environment installed from the direct manifest with the
existing primary environment's tested versions as constraints. This deliberately
avoids broad upgrades. `pip check` passes.

This is a tested platform-specific package snapshot, not a hash-verified lock,
vendored wheel archive, exact Python installer or universal cross-platform
resolution. Ubuntu CI continues testing the direct manifest. Use a separately
validated resolution on other platforms; do not infer a Linux lock from this file.
The clean-checkout replay and exact results are in the
[sprint report](23_release_candidate_sprint_report.md).

Application version is centralized in `app/version.py` as `2.3.0rc1`, consumed
by FastAPI, the root response and `/ui/status`. It is a minor application increment
from 2.2.0 for the product interface. Frozen suite/scorer versions, old report
provenance and model configuration remain independent and unchanged. No tag is
created.

CI uses `actions/checkout@v5` and `actions/setup-python@v6`; their
[official checkout manifest](https://raw.githubusercontent.com/actions/checkout/v5/action.yml)
and [setup-python manifest](https://raw.githubusercontent.com/actions/setup-python/v6/action.yml)
declare Node 24. Full-history checkout remains enabled for historical identity
tests. Hosted validation and warning status are recorded in the sprint report.
The separate existing Starlette/httpx Python deprecation warning is retained;
changing the test transport dependency is not needed for this candidate.

## Preservation and approval boundary

Semantic production behavior, prompts, deterministic output policy, analyzers,
schema models, source processing, reference packs, registry and all frozen
V1/V2/V3/V3.1/V3.2 evidence/suites/scorers remain unchanged. Analysis APIs, safe UI
envelopes, repair flags, auditing and fail-closed behavior remain compatible.
Only application naming/version plumbing changes in the backend.

Browser inventory again reported the browser access host unavailable. No new
pixel-level QA or screenshots are claimed. AppTest verifies routing, cards,
forms, result presentation and the native architecture structure. The user must
inspect Overview, both active workflows, Platform Evaluation and About in dark
and light themes, including a narrow viewport, before final approval. Check
clipping, spacing, columns, architecture readability, navigation grouping and
active/planned status. Then separately authorize merge/tag decisions. No new
workflow, semantic hardening, integration or deployment feature is implemented.
