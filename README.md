# Local AI Security Risk & SOC Triage Platform

A local AI security project that uses Python, FastAPI, Streamlit, Ollama, and an 8B open-weight model to support two practical workflows: AI governance risk intake and SOC alert triage.

The goal of this project is to show how a local LLM can be used as part of a structured security analysis workflow without relying on external AI APIs. User inputs are validated, passed through a backend API, enriched with local reference context, analyzed by a locally running model, returned as structured JSON, displayed in a Streamlit dashboard, and written to a local audit log.

## Overview

This project has two main modes:

1. **AI Governance Risk Intake**
   Reviews a proposed AI system and produces a structured risk assessment, including key risks, required controls, human review requirements, logging requirements, evidence gaps, recommended next steps, and local source references.

2. **SOC Alert Triage**
   Reviews a security alert and produces a structured triage report, including severity, likely incident type, MITRE-style mapping, containment steps, investigation steps, false positive considerations, evidence gaps, an analyst note, and local source references.

The project is intentionally local-first. The model runs through Ollama on the user's machine, and the application does not send analysis requests to an external AI provider.

## Version 2.2 Update: Source-Aware Outputs

Version 2.2 expands the local reference-grounding system by making source usage visible and auditable.

In Version 2.1, the backend retrieved relevant local reference cards and inserted them into the model prompt. In Version 2.2, the model response now includes a structured `source_references` field that identifies which local reference cards influenced the response.

Version 2.2 also adds backend safeguards to make source-aware outputs more reliable:

* The model is instructed to cite only local references that were actually provided in the prompt.
* Returned source references are sanitized against the references retrieved by the backend.
* Fake or unretrieved source IDs are removed before the response is validated.
* Source IDs are kept out of ordinary response fields and placed only in `source_references`.
* Inline source citations such as `(per SOURCE-ID)` are cleaned from normal user-facing fields.
* Audit logs now record the source IDs used for each successful analysis.
* Streamlit now displays a dedicated **Source References** section for governance and SOC results.

This gives the project a stronger responsible-AI structure: the model can use local reference context, but the backend enforces the source-reference contract before returning the result.

## Features

* Local LLM analysis using Ollama and `qwen3:8b`
* FastAPI backend with structured API endpoints
* Streamlit dashboard for user interaction
* Pydantic schemas for request and response validation
* AI governance risk analysis workflow
* SOC alert triage workflow
* Curated local reference packs for SOC and governance workflows
* Reference-grounded prompts using local security and governance snippets
* Source-aware structured outputs through `source_references`
* Backend validation and sanitization of returned source IDs
* Inline citation cleanup for normal response fields
* Streamlit Source References display
* Local JSONL audit logging with source IDs
* Evidence gap identification
* Human-review and responsible-AI framing
* Pytest coverage for schemas, reference loading, prompt integration, source validation, and audit logging
* Ruff-based code quality checks

## Tech Stack

* Python
* FastAPI
* Streamlit
* Ollama
* qwen3:8b
* Pydantic
* Requests
* Python-dotenv
* Tenacity
* Ruff
* Pytest

## Project Structure

```text
local-ai-security-risk-platform/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── schemas.py
│   ├── prompts.py
│   ├── ollama_client.py
│   ├── governance_analyzer.py
│   ├── soc_analyzer.py
│   ├── audit_logger.py
│   └── reference_loader.py
│
├── dashboard/
│   └── streamlit_app.py
│
├── reference_material/
│   ├── soc_references.json
│   ├── governance_references.json
│   └── local_checklists.json
│
├── logs/
│   └── .gitkeep
│
├── sample_data/
│   ├── ai_use_cases.json
│   └── soc_alerts.csv
│
├── tests/
│   ├── test_audit_logger.py
│   ├── test_prompt_reference_integration.py
│   ├── test_reference_loader.py
│   ├── test_schemas.py
│   └── test_source_reference_validation.py
│
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

## Architecture

The application uses a local multi-layer architecture:

```text
Streamlit dashboard
        ↓
FastAPI backend
        ↓
Pydantic request validation
        ↓
Workflow analyzer
        ↓
Local reference retrieval
        ↓
Prompt builder with reference context
        ↓
Ollama local model
        ↓
Raw structured JSON response
        ↓
Source reference sanitization
        ↓
Inline citation cleanup
        ↓
Pydantic response validation
        ↓
Audit log with source IDs
        ↓
Streamlit display with Source References
```

Streamlit handles the user interface. FastAPI handles the backend routes. Pydantic validates inputs and outputs. The reference loader retrieves relevant local guidance cards. Ollama runs the local model. The backend sanitizes source references and removes inline source IDs from normal fields. The audit logger records each completed or failed analysis, including source IDs when available.

## Information Flow

### AI Governance Risk Intake

```text
User submits AI system details
        ↓
FastAPI validates the request
        ↓
governance_analyzer.py converts the request into a searchable query
        ↓
reference_loader.py retrieves relevant governance reference cards
        ↓
prompts.py builds a governance prompt with local reference context
        ↓
ollama_client.py sends the prompt and response schema to qwen3:8b
        ↓
The model returns structured JSON
        ↓
The backend sanitizes returned source references
        ↓
The backend removes inline source citations from normal fields
        ↓
Pydantic validates the final response
        ↓
audit_logger.py records the result and source IDs
        ↓
Streamlit displays the output and Source References section
```

### SOC Alert Triage

```text
User submits SOC alert details
        ↓
FastAPI validates the request
        ↓
soc_analyzer.py converts the alert into a searchable query
        ↓
reference_loader.py retrieves relevant SOC reference cards
        ↓
prompts.py builds a SOC prompt with local reference context
        ↓
ollama_client.py sends the prompt and response schema to qwen3:8b
        ↓
The model returns structured JSON
        ↓
The backend sanitizes returned source references
        ↓
The backend removes inline source citations from normal fields
        ↓
Pydantic validates the final response
        ↓
audit_logger.py records the result and source IDs
        ↓
Streamlit displays the output and Source References section
```

## Running the Project Locally

### 1. Clone the repository

```powershell
git clone https://github.com/akshayneal/local-ai-security-risk-platform.git
cd local-ai-security-risk-platform
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Install and run the local model

Install Ollama, then pull/run the model:

```powershell
ollama run qwen3:8b
```

After confirming the model works, exit the model chat with:

```text
/bye
```

### 5. Create your environment file

Copy `.env.example` into a new `.env` file.

Example `.env`:

```env
OLLAMA_MODEL=qwen3:8b
OLLAMA_HOST=http://localhost:11434
API_BASE_URL=http://127.0.0.1:8000
```

### 6. Run the FastAPI backend

In one terminal:

```powershell
python -m uvicorn app.main:app --reload
```

The backend should be available at:

```text
http://127.0.0.1:8000
```

You can check the health endpoint here:

```text
http://127.0.0.1:8000/health
```

FastAPI docs are available here:

```text
http://127.0.0.1:8000/docs
```

### 7. Run the Streamlit dashboard

In a second terminal:

```powershell
streamlit run dashboard/streamlit_app.py
```

The dashboard should open at:

```text
http://localhost:8501
```

## Application Modes

### AI Governance Risk Intake

This mode evaluates a proposed AI system based on information such as:

* System name
* System purpose
* Data types
* Users
* External integrations
* Human review process
* Business impact

The output includes:

* Risk level
* Approval decision
* Summary
* Key risks
* Required controls
* Human review requirements
* Logging requirements
* Evidence gaps
* Recommended next steps
* Source references

Example use cases:

* Internal HR chatbot
* Resume screening assistant
* Security operations copilot
* AI policy search assistant
* Internal knowledge base chatbot
* Customer support AI assistant

### SOC Alert Triage

This mode evaluates a security alert based on information such as:

* Alert ID
* Alert type
* Source system
* Affected asset
* Raw log
* Known indicators
* Observed behavior

The output includes:

* Severity
* Likely incident type
* Summary
* MITRE-style mapping
* Recommended containment steps
* Recommended investigation steps
* False positive considerations
* Evidence gaps
* Analyst note
* Source references

Example alert types:

* SSH brute force followed by successful login
* Suspicious PowerShell command
* New privileged account creation
* Possible MFA fatigue
* Unusual outbound connection
* Suspicious authentication pattern

## Local Reference Grounding

The project includes local reference cards stored in:

```text
reference_material/
```

These cards are loaded by:

```text
app/reference_loader.py
```

The reference loader performs simple keyword and tag matching to retrieve relevant cards for each workflow.

SOC mode searches:

```text
reference_material/soc_references.json
reference_material/local_checklists.json
```

Governance mode searches:

```text
reference_material/governance_references.json
reference_material/local_checklists.json
```

The retrieved reference cards are formatted and inserted into the model prompt before the local model generates a response.

This allows the model to produce answers that are more aligned with the project’s selected security, governance, and auditability guidance.

## Source-Aware Outputs

Version 2.2 adds structured source references to both main workflows.

Each response can include:

```json
"source_references": [
  {
    "source_id": "GRC-HIGH-IMPACT-USE",
    "title": "AI Governance Checklist - High-Impact Use",
    "framework": "Local AI Governance Checklist",
    "relevance": "System involves employment or benefits-related use requiring stronger review."
  }
]
```

The backend performs two important cleanup steps:

1. **Source reference sanitization**
   The model may only cite source IDs that were actually retrieved for the request. If the model returns an unretrieved or fake source ID, the backend removes it before validation.

2. **Inline citation cleanup**
   Source IDs are kept out of ordinary response fields such as summaries, risks, controls, containment steps, and recommendations. Source attribution is kept in the dedicated `source_references` field.

This keeps the user-facing output clean while still preserving source awareness and auditability.

## Testing

Run the test suite with:

```powershell
python -m pytest
```

The tests currently cover:

* Basic schema validation
* SourceReference schema support
* Reference file loading
* Reference retrieval behavior
* Prompt/reference integration
* Source reference sanitization
* Inline citation cleanup
* Audit logger support for source IDs

Run Ruff to check code quality:

```powershell
ruff check .
```

Format code with:

```powershell
ruff format .
```

## Audit Logging

Each analysis writes a local audit entry to:

```text
logs/audit_log.jsonl
```

The log records:

* Timestamp
* Mode
* Model used
* Input summary
* Result summary
* Success or failure
* Error message, if applicable
* Source IDs used in the response

Example audit field:

```json
"source_ids": [
  "SOC-BRUTE-FORCE-SUCCESS",
  "MITRE-TA0006",
  "MITRE-TA0001"
]
```

Real log files are ignored by Git. The `logs/.gitkeep` file exists only so the logs folder remains visible in the repository.

## Limitations

This project is a local proof-of-concept and should not be treated as a production security tool.

Current limitations:

* The model does not browse the internet.
* The model does not query live threat intelligence.
* The model does not verify IPs, domains, hashes, CVEs, or threat actors externally.
* The current reference-grounding layer uses keyword and tag matching, not full semantic vector search.
* Source references are based on retrieved local reference cards, not live external sources.
* The model may still make imperfect recommendations, so the backend includes validation and cleanup steps to enforce cleaner output structure.
* Recommendations are based on the provided input, structured prompts, retrieved local reference cards, and the model's pretrained knowledge.
* Outputs should be reviewed by a human analyst before being used for real operational or governance decisions.

## Future Improvements

Planned or possible improvements include:

* Add full local vector RAG using ChromaDB and Ollama embeddings
* Add local knowledge base ingestion for security and governance documents
* Add a SOC case file builder
* Add AI governance risk register entry generation
* Add control mapping workflows
* Add evidence request generation for GRC workflows
* Add policy gap review workflows
* Add sample data loading in the Streamlit dashboard
* Add SQLite storage for audit logs
* Add exportable incident reports and governance reports
* Add screenshots and architecture diagrams
* Add retrieval quality evaluation cases
* Add optional report export in Markdown or JSON

## Why I Built This

I built this project to practice combining cybersecurity analysis, AI governance concepts, local AI tooling, and structured backend development in a practical application.

This project focuses on structured workflows, validated outputs, auditability, source-aware responses, local reference grounding, and responsible use of local AI in security and governance contexts.
