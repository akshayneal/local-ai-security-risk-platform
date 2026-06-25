# Local AI Security Risk & SOC Triage Platform

A local AI security project that uses Python, FastAPI, Streamlit, Ollama, and an 8B open-weight model to support two practical workflows: AI governance risk intake and SOC alert triage.

The goal of this project is to show how a local LLM can be used as part of a structured security analysis workflow without relying on external AI APIs. User inputs are validated, passed through a backend API, analyzed by a locally running model, returned as structured JSON, and written to a local audit log.

## Overview

This project has two main modes:

1. **AI Governance Risk Intake**
   Reviews a proposed AI system and produces a structured risk assessment, including key risks, required controls, human review requirements, logging requirements, evidence gaps, and recommended next steps.

2. **SOC Alert Triage**
   Reviews a security alert and produces a structured triage report, including severity, likely incident type, MITRE-style mapping, containment steps, investigation steps, false positive considerations, evidence gaps, and an analyst note.

The project is intentionally local-first. The model runs through Ollama on the user's machine, and the application does not send analysis requests to an external AI provider.

## Features

* Local LLM analysis using Ollama and `qwen3:8b`
* FastAPI backend with structured API endpoints
* Streamlit dashboard for user interaction
* Pydantic schemas for request and response validation
* AI governance risk analysis workflow
* SOC alert triage workflow
* Structured JSON outputs
* Local JSONL audit logging
* Evidence gap identification
* Human-review and responsible-AI framing

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
│   └── audit_logger.py
│
├── dashboard/
│   └── streamlit_app.py
│
├── logs/
│   └── .gitkeep
│
├── sample_data/
│   ├── ai_use_cases.json
│   └── soc_alerts.csv
│
├── tests/
│   └── test_schemas.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Architecture

The application uses a simple local architecture:

```text
Streamlit dashboard
        ↓
FastAPI backend
        ↓
Pydantic validation
        ↓
Workflow analyzer
        ↓
Prompt builder
        ↓
Ollama local model
        ↓
Validated JSON response
        ↓
Audit log
        ↓
Streamlit display
```

Streamlit handles the user interface. FastAPI handles the backend routes. Pydantic validates inputs and outputs. Ollama runs the local model. The audit logger records each completed or failed analysis.

## Running the Project Locally

### 1. Clone the repository

```powershell
git clone https://github.com/YOUR-USERNAME/local-ai-security-risk-platform.git
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
* Recommendations are based on the provided input, structured prompts, and the model's pretrained knowledge.
* Outputs should be reviewed by a human analyst before being used for real operational decisions.

## Future Improvements

Planned or possible improvements include:

* Add local reference grounding using MITRE ATT&CK, CISA incident response guidance, NIST CSF, and NIST AI RMF snippets
* Add source references to model outputs
* Add local RAG over security playbooks
* Add sample data loading in the Streamlit dashboard
* Add SQLite storage for audit logs
* Add exportable incident reports
* Add more schema tests
* Add screenshots and architecture diagrams
* Add a more polished README with demo examples

## Why I Built This

I built this project to practice combining cybersecurity analysis, AI governance concepts, and local AI tooling in a practical application. This project focuses on structured workflows, validated outputs, auditability, and responsible use of local AI in security contexts.
