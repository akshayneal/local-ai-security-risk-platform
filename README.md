# Local AI Security Risk & SOC Triage Platform

A local AI security project that uses Python, FastAPI, Streamlit, Ollama, and an 8B open-weight model to support two practical workflows: AI governance risk intake and SOC alert triage.

The goal of this project is to show how a local LLM can be used as part of a structured security analysis workflow without relying on external AI APIs. User inputs are validated, passed through a backend API, enriched with local reference context, analyzed by a locally running model, returned as structured JSON, and written to a local audit log.

## Overview

This project has two main modes:

1. **AI Governance Risk Intake**
   Reviews a proposed AI system and produces a structured risk assessment, including key risks, required controls, human review requirements, logging requirements, evidence gaps, and recommended next steps.

2. **SOC Alert Triage**
   Reviews a security alert and produces a structured triage report, including severity, likely incident type, MITRE-style mapping, containment steps, investigation steps, false positive considerations, evidence gaps, and an analyst note.

The project is intentionally local-first. The model runs through Ollama on the user's machine, and the application does not send analysis requests to an external AI provider.

## Version 2.1 Update: Curated Local Reference Grounding

Version 2.1 adds a curated local reference layer. Before the model generates a response, the backend retrieves relevant local reference cards from JSON files and injects them into the model prompt.

This gives the model more useful context for security and governance workflows while still keeping the project local and offline.

Current reference materials include:

* MITRE-style SOC tactic cards
* Local SOC triage checklists
* NIST AI RMF-style governance cards
* Local AI governance checklists
* General auditability, evidence gap, and human-review guidance

This is not full vector RAG yet. The current reference retrieval system uses simple keyword and tag matching over curated local JSON files. Full vector RAG over larger documents is planned as a future improvement.

## Features

* Local LLM analysis using Ollama and `qwen3:8b`
* FastAPI backend with structured API endpoints
* Streamlit dashboard for user interaction
* Pydantic schemas for request and response validation
* AI governance risk analysis workflow
* SOC alert triage workflow
* Curated local reference packs for SOC and governance workflows
* Reference-grounded prompts using local security and governance snippets
* Structured JSON outputs
* Local JSONL audit logging
* Evidence gap identification
* Human-review and responsible-AI framing
* Basic pytest coverage for schema validation, reference loading, and prompt/reference integration

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
│   ├── test_schemas.py
│   ├── test_reference_loader.py
│   └── test_prompt_reference_integration.py
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
Validated JSON response
        ↓
Audit log
        ↓
Streamlit display
```

Streamlit handles the user interface. FastAPI handles the backend routes. Pydantic validates inputs and outputs. The reference loader retrieves relevant local guidance cards. Ollama runs the local model. The audit logger records each completed or failed analysis.

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
ollama_client.py sends the prompt to qwen3:8b
        ↓
The model returns structured JSON
        ↓
Pydantic validates the response
        ↓
audit_logger.py records the result
        ↓
Streamlit displays the output
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
ollama_client.py sends the prompt to qwen3:8b
        ↓
The model returns structured JSON
        ↓
Pydantic validates the response
        ↓
audit_logger.py records the result
        ↓
Streamlit displays the output
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

## Testing

Run the test suite with:

```powershell
python -m pytest
```

The tests currently cover:

* Reference file loading
* Reference retrieval behavior
* Prompt/reference integration
* Basic schema validation

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

Real log files are ignored by Git. The `logs/.gitkeep` file exists only so the logs folder remains visible in the repository.

## Limitations

This project is a local proof-of-concept and should not be treated as a production security tool.

Current limitations:

* The model does not browse the internet.
* The model does not query live threat intelligence.
* The model does not verify IPs, domains, hashes, CVEs, or threat actors externally.
* The current reference-grounding layer uses keyword and tag matching, not full semantic vector search.
* The model receives local reference context, but Version 2.1 does not yet return explicit source citations in the output schema.
* Recommendations are based on the provided input, structured prompts, retrieved local reference cards, and the model's pretrained knowledge.
* Outputs should be reviewed by a human analyst before being used for real operational or governance decisions.

## Future Improvements

Planned or possible improvements include:

* Add explicit `source_references` fields to model outputs
* Validate that returned source IDs match retrieved reference cards
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

## Why I Built This

I built this project to practice combining cybersecurity analysis, AI governance concepts, local AI tooling, and structured backend development in a practical application.

This project focuses on structured workflows, validated outputs, auditability, reference-grounded prompts, and responsible use of local AI in security and governance contexts.
