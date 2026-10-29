# Local AI Security Risk Platform

Local analyst-support software for security-event investigation and AI-system risk review. It combines a Streamlit application, FastAPI backend, curated local references and Ollama inference with `qwen3:8b`.

**Release: 2.3.0.** Two practitioner workflows are active.

## What it does

**SOC Investigation** accepts security telemetry and returns a structured analysis: severity, likely incident type, summary, observed evidence, analyst inferences, evidence gaps, investigation steps, conditional containment recommendations and MITRE-style mapping. It helps an analyst decide what to verify next. It does not operate a SIEM, verify threat reputation or execute response actions.

**AI System Risk Review** assesses an AI system or proposed AI use case for governance, security, privacy and operational risk. It presents a proposed review decision, risks, controls, missing evidence, human oversight, logging requirements and next steps. The reviewed object is an AI system/use case; incident policy review is a separate planned workflow.

Both workflows support validated synthetic sample loading, structured source references, local audit logging and JSON/Markdown brief downloads. Results remain proposals for human review. The application does not approve deployments or make operational decisions.

## Product direction

| Domain | Technical | Policy / governance |
| --- | --- | --- |
| Security Operations | **SOC Investigation — Active** | SOC Policy & Governance Review — Planned |
| AI Security | AI Security Assessment — Planned | **AI System Risk Review — Active** |

The planned workflows communicate product direction and are not included in this release. They have no forms, endpoints, analysis actions or sample outputs. Future SOC policy review would cover escalation, approval boundaries, procedural constraints and evidence/documentation obligations. Future AI security assessment would examine attack surface, prompt/retrieval/tool risks, authorization boundaries, controls and evaluation planning.

## Why the architecture matters

The application treats input logs, retrieved material and model-generated output as untrusted data. Local references provide guidance, not automatic authority for every claim. Model prompts distinguish supplied facts, unverified claims and missing information; deterministic processing then enforces specific response contracts.

Both workflows validate structured responses and sanitize source references against the retrieved local cards. SOC additionally checks nonempty observations and recognized critical identifiers and endpoint relationships across analyst-facing fields. A rejected SOC generation gets at most one policy repair, with the same complete checks applied again. If repair fails, the application withholds the analyst result.

These protections are bounded. Matching an identifier does not prove that a sentence using it is supported. Governance semantics, legal applicability, event support, protocol reasoning and broader consistency remain prompt-guided and require review. There is no numerical truth, confidence or safety score attached to an analysis.

## Current application

Navigation separates practitioner work from platform assurance:

| Area | Page | Purpose |
| --- | --- | --- |
| Landing | Overview | Current release and four-workflow product map |
| Workflows | SOC Investigation | Security telemetry, evidence/inference separation and investigation guidance |
| Workflows | AI System Risk Review | AI-system risks, controls and oversight |
| Platform | Platform Evaluation | Frozen evaluation history and same-suite comparisons for this application |
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

The current deterministic suite has **1,287 tests** and requires no Ollama, internet connection or running application server:

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

The next product families are SOC Policy & Governance Review and AI Security Assessment, both planned. Other possible expansion areas include investigation depth, ATT&CK STIX validation and deployment packaging. Implementation requires separate authorization. Vector RAG and external integrations remain deferred. The immediate release step is human visual inspection, followed by separately authorized merge/version-tag decisions.
