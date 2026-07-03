# Codex Project Instructions

## Project

This repository is `local-ai-security-risk-platform`.

It is a local AI security operations and governance project using:

- Python
- FastAPI
- Streamlit
- Ollama
- qwen3:8b
- Pydantic
- local curated reference packs
- pytest
- Ruff

The project is intentionally local-first. Do not introduce external AI APIs or cloud-hosted model calls unless explicitly requested.

## Current Status

The project has completed Version 2.2.

Current implemented capabilities:

- AI Governance Risk Intake workflow
- SOC Alert Triage workflow
- FastAPI backend
- Streamlit dashboard
- Ollama local model integration
- Pydantic request and response schemas
- Curated local reference packs
- Source-aware outputs through `source_references`
- Backend source ID sanitization
- Inline citation cleanup for ordinary response fields
- Audit logging with `source_ids`
- Streamlit Source References display
- pytest and Ruff checks

The next planned major phase is Version 2.3, likely involving full local vector RAG, but do not start V2.3 unless explicitly instructed.

## User's Primary Goal

The user is building this project to learn.

Prioritize:

- small, explainable changes
- clear diffs
- minimal architecture disruption
- preserving existing working behavior
- testable incremental steps

Do not make large automatic changes. Do not redesign the project without explicit permission.

## Strict Scope Rules

When given a task:

1. Do only the task explicitly requested.
2. Do not add unrelated features.
3. Do not add new dependencies unless explicitly requested.
4. Do not refactor unrelated files.
5. Do not rename files, functions, endpoints, or schemas unless explicitly requested.
6. Do not change the project architecture unless explicitly requested.
7. Do not modify README, docs, tests, or UI unless the task asks for it or the change is necessary for the requested task.
8. If you believe a broader change is needed, explain it first and wait for approval.
9. If there are multiple possible approaches, ask or present options before implementing.
10. Preserve the learning-oriented, step-by-step development process.

## Coding Style

Follow the existing project style.

Use:

- type hints
- small helper functions
- readable names
- simple control flow
- Pydantic models for structured data
- pytest tests for new logic
- Ruff-compatible formatting

Avoid:

- clever abstractions
- large framework changes
- premature optimization
- hidden side effects
- global rewrites
- broad cleanup commits mixed with feature work

## Security and Governance Rules

The application should remain local-first.

Do not add:

- external AI APIs
- live threat intelligence API calls
- SIEM integrations
- ticketing integrations
- cloud deployment
- automatic containment actions
- destructive security actions
- credential handling
- secrets in code

unless explicitly requested.

The app should continue to avoid overclaiming. It should distinguish between:

- observed evidence
- reasonable inference
- missing information
- unsupported claims

Source IDs should appear only in `source_references` or audit-log `source_ids`, not in ordinary user-facing response fields.

## Existing Architecture

Important backend files:

- `app/main.py` — FastAPI routes and audit logging calls
- `app/schemas.py` — Pydantic request/response schemas
- `app/prompts.py` — system and workflow prompts
- `app/ollama_client.py` — Ollama client and JSON model call
- `app/reference_loader.py` — reference loading, retrieval, source sanitization, inline citation cleanup
- `app/governance_analyzer.py` — governance workflow analyzer
- `app/soc_analyzer.py` — SOC workflow analyzer
- `app/audit_logger.py` — JSONL audit logging

Important frontend file:

- `dashboard/streamlit_app.py` — Streamlit UI

Important data folders:

- `reference_material/` — curated local reference cards
- `sample_data/` — sample inputs
- `logs/` — local generated audit logs, ignored except `.gitkeep`
- `tests/` — pytest test suite

## Git and Branch Rules

Before making changes, identify the current branch.

Do not commit directly to `main` unless explicitly instructed.

For feature work, use a feature branch.

Do not force push.

Do not delete branches unless explicitly instructed.

Do not modify `.env`, `.venv/`, generated logs, cache folders, or local-only files.

Never commit:

- `.env`
- `.venv/`
- `logs/audit_log.jsonl`
- `__pycache__/`
- `.pytest_cache/`
- `.ruff_cache/`

## Required Checks

After making code changes, run:

```powershell
python -m pytest
ruff check .
```

If Ruff formatting is needed, run:

```powershell
ruff format .
python -m pytest
ruff check .
```

Report whether the checks passed.

## Response Format for Codex

After making changes, respond with:

Files changed
What changed
Why it changed
Tests/checks run
Any risks or follow-up items

Do not just say “done.”

## Important Instruction

This project is being developed with a separate ChatGPT teaching/review conversation.

Codex should act as an implementation assistant, not the main architect.

If a requested change seems architectural, risky, or broader than the prompt, stop and ask for confirmation before implementing.