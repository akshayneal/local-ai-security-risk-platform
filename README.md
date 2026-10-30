# Local AI Security Risk Platform

Local-first, single-user decision support across SOC, AI Security, and AI Safety, Assurance & Policy. It combines a Streamlit application, FastAPI backend, curated local references and Ollama inference with `qwen3:8b`.

**Released main: 2.3.0.** Two practitioner workflows are active. This development branch is unmerged. Local knowledge defaults off. The development launcher uses one gateway for all three workflows, including experimental technical AI Security Assessment. See the Sprint 7 readout for actual local-model evidence and release blockers.

## What it does

**SOC Investigation** accepts security telemetry and returns a structured analysis: severity, likely incident type, summary, observed evidence, analyst inferences, evidence gaps, investigation steps, conditional containment recommendations and MITRE-style mapping. It helps an analyst decide what to verify next. It does not operate a SIEM, verify threat reputation or execute response actions.

**AI System Risk Review** assesses an AI system or proposed AI use case for governance, security, privacy and operational risk. It presents a proposed review decision, risks, controls, missing evidence, human oversight, logging requirements and next steps. The reviewed object is an AI system/use case; incident policy review is a separate planned workflow.

Both workflows support validated synthetic sample loading, structured source references, local audit logging and JSON/Markdown brief downloads. Results remain proposals for human review. The application does not approve deployments or make operational decisions.

## Product direction

| Pillar | Working capability | Status |
| --- | --- | --- |
| SOC | SOC Investigation; generic telemetry and experimental Microsoft JSON/CSV file adapter | Two-workflow core released; Microsoft adapter unmerged |
| AI Security | Typed component/flow threat model and structured technical hypotheses | Experimental AI Security Assessment via Sprint 6 gateway; no exploitation or control verification |
| AI Safety, Assurance & Policy | Existing AI System Risk Review; human review, evidence gaps, policy/implementation distinction | Core released; Inspector/corrections unmerged |

A shared local evidence layer supplies telemetry, curated guidance and explicitly opted-in, reviewed current organizational documents. A shared assurance layer supplies contracts, provenance, deterministic checks, application self-evaluation and analyst review. Platform Evaluation describes this application's evaluations; it is not another analyzer. Standalone SOC Policy & Governance Review remains Planned.

| Development status | Capabilities |
| --- | --- |
| Unmerged but functional | Evidence Inspector, session-bound corrections, field anchors, correction-first exports, curated lexical opt-in and working-checkout launcher |
| Sprint 5 experimental | Reviewed local document CLI, registered current-version BM25 bridge for both analyzers, read-only Knowledge Workspace, synthetic Northstar demo |
| Sprint 6 experimental | Technical AI Security Assessment, immutable graph contracts, local authored guidance, read-only provenance and safe exports |
| Planned | Authenticated document portal, AI Security organizational knowledge and broader natural-language support/applicability evaluation |

An applicable policy does not prove implementation, granted approval or a correct model answer. A citation is evidence provenance, not an entailment certificate.

## Why the architecture matters

The application treats input logs, retrieved material and model-generated output as untrusted data. Local references provide guidance, not automatic authority for every claim. Model prompts distinguish supplied facts, unverified claims and missing information; deterministic processing then enforces specific response contracts.

Both workflows validate structured responses and sanitize source references against the retrieved local cards. SOC additionally checks nonempty observations and recognized critical identifiers and endpoint relationships across analyst-facing fields. A rejected SOC generation gets at most one policy repair, with the same complete checks applied again. If repair fails, the application withholds the analyst result.

These protections are bounded. Matching an identifier does not prove that a sentence using it is supported. Governance semantics, legal applicability, event support, protocol reasoning and broader consistency remain prompt-guided and require review. There is no numerical truth, confidence or safety score attached to an analysis.

## Current application

Navigation separates practitioner work from platform assurance:

| Area | Page | Purpose |
| --- | --- | --- |
| Landing | Overview | Three pillars and honest capability statuses |
| Workflows | SOC Investigation | Security telemetry, evidence/inference separation and investigation guidance |
| Workflows | AI System Risk Review | AI-system risks, controls and oversight |
| Workflows | AI Security Assessment | Experimental technical threat-model review via the development gateway |
| Platform | Platform Evaluation | Frozen evaluation history and same-suite comparisons for this application |
| Platform | Knowledge Workspace | Read-only operator workspace status and eligible source identities |
| Platform | Activity | Recent local audit entries, filtered by workflow and outcome |
| Platform | About | Native architecture overview and operational boundaries |

Response checks expose actual backend metadata, including whether a SOC repair was used. Sources show title, family, ID and relevance. Downloads contain submitted case identity, analysis sections, sources, a generation timestamp and human-review notice. Internal prompts and diagnostic traces are excluded.

## Evaluation highlights

The repository retains frozen adversarial and semantic experiments, including their original suites, scorers, provenance and manual reviews. Platform Evaluation reads these artifacts without generating new model outputs.

| Milestone | Official result | Interpretation |
| --- | --- | --- |
| V1 adversarial baseline / treatment | 7/12 → 7/12 | One gain and one regression; no aggregate improvement |
| V2 repeated baseline / deterministic I/O treatment | 28/45 → 43/44 valid | One treatment application error in 45 attempts; semantic blind spots remained |
| V3.2 semantic baseline / production treatment | 32/42 → 37/41 valid | 37/42 treatment attempts passed; one fail-closed application error |

Results from different evaluation versions measure different properties and are not directly comparable. Each before/after pair above uses its own unchanged suite. V3 and V3.1 provide the intermediate grounding/calibration history in the [evaluation documentation](Documentation/16_semantic_evaluation_v3_2.md).

The exact-suite V3.2 treatment had zero stable-fail cases, compared with two at baseline. One stable-pass-labelled case had two valid passes and an application error. Positive controls improved from 9/15 to 13/15, while mean attempt latency rose from 65.31 to 81.29 seconds. Manual review identified suspected scorer false positives and missed defects; official scores were not replaced. Three unseeded trials per synthetic case do not establish statistical safety or isolate individual control effects.

## Architecture

```text
Streamlit input → FastAPI / Pydantic request validation
    → local reference retrieval → untrusted-content handling
    → local Ollama inference → citation cleanup / source sanitization
    ├─ SOC: schema + bounded identifier/endpoint/observation checks
    │       → at most one policy repair → return or withhold analysis
    └─ AI-system risk: schema + prompt-guided risk analysis
    → local audit entry → analyst review / optional brief export
```

The original `/analyze/soc-alert` and `/analyze/governance` analysis interfaces remain compatible. The dashboard uses separate `/ui/analyze/*` envelopes with allowlisted execution metadata. Existing local document ingestion and the SQLite version registry remain available; this release does not replace retrieval with vector RAG.

## Run locally

Prerequisites: Git, Python 3.13, and Ollama with `qwen3:8b` for analysis. Start from a full clone: historical artifact tests require Git history, so a source ZIP or shallow clone is insufficient.

```powershell
git clone https://github.com/akshayneal/local-ai-security-risk-platform.git
cd local-ai-security-risk-platform
python -m venv .venv
```

On Windows x64 / CPython 3.13, install the exact tested package snapshot:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-windows-py313.lock.txt
.\.venv\Scripts\python.exe -m pip check
```

`requirements.txt` remains the readable direct-dependency manifest. The snapshot was generated from a fresh Windows x64 / CPython 3.13.1 environment using the existing tested versions; it pins 79 packages. It is not a hash-verified or cross-platform lock. On another platform, install `requirements.txt` and validate that environment separately. Hosted CI exercises the direct manifest on Ubuntu/Python 3.13.

Prepare the local model and configuration:

```powershell
ollama pull qwen3:8b
Copy-Item .env.example .env
```

Keep Ollama running. The example configuration uses local Ollama on port 11434 and FastAPI on port 8000. No cloud AI key is required. In separate terminals from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard/streamlit_app.py --server.address 127.0.0.1
```

Open `http://localhost:8501`; API documentation is at `http://127.0.0.1:8000/docs`. Overview, Platform Evaluation and About do not need FastAPI or Ollama. Load a synthetic workflow sample and submit once to run analysis. A backend-status check confirms FastAPI availability, not model readiness. Local generation may take minutes; a UI timeout does not cancel backend work, so check Activity before resubmitting.

## Testing

The released product checkpoint documented **1,287 tests** (the current development count is recorded in report 51) and requires no Ollama, internet connection or running application server:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
git diff --check HEAD
```

Coverage includes API compatibility, source controls, bounded SOC repair/fail-closed behavior, identifier/endpoint contracts, frozen evaluation evidence, sample parsing, exports, navigation and Streamlit page execution. AppTest checks are not pixel-level visual validation. Final human inspection in dark and light themes remains required.

## Limitations

- A local demonstration with no authentication or multi-user access boundary.
- No automatic containment, live threat intelligence, SIEM/SOAR or ticketing integration.
- Finite SOC identifier/endpoint grammar; domains, IPv6, arbitrary governance identifiers and universal semantic support are not guaranteed.
- Model-proposed classifications, governance decisions and MITRE-style mappings require review.
- Repair adds latency, and fail-closed rejection reduces availability. No backend generation deadline or cancellation mechanism is implemented.
- Local audit summaries and exported briefs can retain supplied sensitive information; review them before sharing.
- Small synthetic evaluations retain known scorer ambiguities and do not certify operational safety.

## Documentation

- [Release-candidate experience and reproduction](Documentation/22_professional_release_candidate.md)
- [Release-candidate sprint report](Documentation/23_release_candidate_sprint_report.md)
- [Demo walkthrough](Documentation/demo_walkthrough.md)
- [Analyst product experience and UI API semantics](Documentation/20_analyst_product_experience.md)
- [Original adversarial evaluation](Documentation/05_ai_security_evaluation.md)
- [Deterministic I/O hardening](Documentation/10_deterministic_ai_io_hardening.md)
- [V3.2 methodology](Documentation/16_semantic_evaluation_v3_2.md)
- [Semantic production treatment](Documentation/18_semantic_production_hardening.md)
- [Treatment manual review and residual issues](Documentation/evaluation_v3_2/treatment_failure_triage.md)

## Roadmap

The experimental technical AI Security Assessment now supports submitted assets, flows, retrieval/tool boundaries and candidate threats. The Sprint 7 live matrix exposed semantic overstatements and withheld all four technical advisories for inconsistent model coverage. Independent fixed-case review and user acceptance remain pending; see the [RC readout](Documentation/51_cross_pillar_rc_readout.md) before expanding it. Standalone SOC Policy & Governance Review, authenticated portals, default dense/hybrid migration and external integrations remain deferred. This branch is not a release recommendation; visual and independent semantic review remain pending.

## Experimental reviewed local knowledge (Sprint 5)

Start with the [synthetic CLI and human walkthrough](Documentation/47_three_pillar_knowledge_foundation_report.md). No real organizational documents are bundled. Keep private material under the ignored `knowledge_base/workspaces/<name>/documents/`; never put it into tracked sample directories.

```powershell
.\.venv\Scripts\python.exe -m scripts.knowledge_workspace init northstar --demo
.\.venv\Scripts\python.exe -m scripts.knowledge_workspace register northstar
.\.venv\Scripts\python.exe -m scripts.knowledge_workspace build northstar
.\.venv\Scripts\python.exe -m scripts.knowledge_workspace query northstar --workflow soc_investigation --text "incident containment approval procedure"
```

`build` validates and builds a bounded in-memory lexical projection; no persistent vector index is created. Normal new-document reviews default to unapproved/unverified. Review exact-version sidecars separately from document contents. Missing, corrupt or stale workspaces withhold opted-in analysis without fallback. The checkbox grants no access; only operator-owned workspace configuration supplies eligibility scopes. This local eligibility mechanism is not authenticated IAM/RBAC.

For a manual foreground backend, set `$env:LOCAL_KNOWLEDGE_WORKSPACE = 'northstar'` before the existing loopback uvicorn command. The development launcher also reads that operator setting; use Stop then Start to load it. Do not modify the preserved `northstar-sprint5` workspace. In either active analysis page, explicitly select **Include reviewed local knowledge (experimental)**, default off. Check Knowledge Workspace and the Inspector for eligible, selected and cited chunks, versions, categorical authority and incomplete-evidence warnings. Full raw documents and hidden grants are not automatically exported. Related hits and requirements remain unassessed as evidence of specific implementation or approval.

Opted-in requests reuse the existing complete-context local runtime path (`truncate=false`, `shift=false`) and can be withheld if the installed provider cannot meet it. No model download, cloud call, authentication, live Microsoft connection or autonomous response is added. See [sprint plan](Documentation/46_three_pillar_sprint_plan.md) and [results/limitations](Documentation/47_three_pillar_knowledge_foundation_report.md). **USER VISUAL QA PENDING.**

## Experimental technical AI Security Assessment (Sprint 6)

This distinct workflow reviews a caller-declared AI architecture: actors, components,
directed flows, ingestion origins, declared tool capabilities, claimed controls and
separately supplied unverified implementation evidence. It returns candidate technical
hypotheses, mitigations, proposed tests and gaps. It performs no penetration test,
network scan, tool execution, real permission check or deployed-control verification.
Missing graph information produces an explicit insufficient-information response.

The Windows [development launcher](Documentation/45_development_launcher.md)
uses `app.ai_security_api:app` on port 8235 for all three workflows, with Streamlit
on 8535. Existing shortcut targets remain valid. If an older two-workflow dev
instance has recorded ownership state, Start requests a strictly verified Stop,
then Start; it never silently reuses that instance as the new gateway.

```powershell
.\scripts\development\Stop-Development.cmd
.\scripts\development\Start-Development.cmd
```

For a manual foreground development backend, use the same composed entrypoint
and point Streamlit's `API_BASE_URL` at its loopback port. The earlier run-local
`app.main:app` commands describe the stable compatible two-workflow backend.
Release demo/main/v2.3.0 remain unchanged. No real service is started by tests.

Use AI Security Assessment's bounded JSON editor and synthetic examples. Its source
panel is read-only and unassessed; existing Inspector correction history is not
extended to this workflow. The six source categories are locally authored guidance
v1, not external framework/control mappings. Organizational knowledge and grants are
unsupported for this workflow; SOC/AI-risk workspace eligibility remains unchanged.
Never reinitialize or modify the preserved `northstar-sprint5` workspace for this demo.

See the [Sprint 6 plan](Documentation/48_ai_security_sprint_plan.md) and
[technical report and manual acceptance checklist](Documentation/49_ai_security_assessment_report.md).
The historical Sprint 6 offline suite ran **zero real inference calls**. Sprint 7
completed a frozen 12-submission local-Qwen matrix: SOC 4/4 and AI-risk 4/4 returned;
AI Security 0/4 returned because contradictory coverage/findings were withheld.
Semantic overstatements and positive fact omissions remain in returned answers.
See the [Sprint 7 evidence and NO-GO readout](Documentation/51_cross_pillar_rc_readout.md).
Software checks, citations and small synthetic live trials do not establish
semantic accuracy or model injection resistance. The user's
prior brief UI observation was provisional; both older workflows' retrieval/output
acceptance and Sprint 6 end-to-end/visual acceptance remain pending.
