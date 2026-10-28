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

The project has completed Version 2.2, the local document-registry phase, and
Phase 0B: Application Hardening Baseline. The V1 adversarial evaluation and generic
AI-security hardening sprint is complete. The Evaluation V2 repeated-trial
current-state baseline is also complete and remains frozen. A subsequent bounded
deterministic I/O hardening iteration and same-suite V2 comparison are complete.

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
- Local document ingestion
- Document identity and chunking
- SQLite document/version registry
- Application-boundary validation, generic API errors, and CI
- Adversarial evaluation harness: 12 cases across seven categories
- Frozen baseline/hardened results and comparison artifacts
- AI instruction trust boundaries, retrieved-evidence rules, and agency limits
- Deterministic source deduplication and expanded citation cleanup
- SOC `observed_evidence` and `analyst_inferences` fields and UI display
- Evaluation V2: 15 cases across eight categories, three sequential trials per case
- No-model V2 preflight, byte/semantic suite hashes, runtime provenance and manifest
- Exact IPv4, SHA-256, and synthetic CVE-style evidence-fidelity cases
- Structured-output stability and local inference timing diagnostics
- Frozen V2 current-state report and evidence-backed failure-triage documentation
- Model-facing untrusted-instruction quarantine and deterministic source-ID prose policy
- Required nonempty SOC observations, critical-observable subset validation, and one bounded repair
- Opt-in evaluation stage tracing and frozen post-hardening V2 comparison/triage

The frozen baseline and hardened runs each passed 7/12 cases (58.3%): one newly
passing case and one regression, with no aggregate score improvement. Read
`Documentation/05_ai_security_evaluation.md` and the engineering report before
claiming evaluation outcomes or changing defenses.

V1 is frozen historical evidence. V2 completed all 45 planned local model calls
with zero application/runtime errors: 28/45 trials passed (62.2%), with five
stable-pass, two stable-fail, and eight mixed cases. All three fidelity cases were
mixed because required observed-evidence fields were empty in failing trials.
Three trials are preliminary stability measurement, not statistical confidence.
V1 and V2 aggregate percentages are not directly equivalent.

Hardening implementation commit `8efe3ec6348cd704cbb1c82abb5965cc8fcc606d` is
followed by frozen `Documentation/evaluation_v2/post_hardening_3trial.json` and
`hardening_comparison.json`. The unchanged-suite run passed 43/44 valid trials
(97.7%), with one assertion failure and one application error in 45 attempts.
There are 14 valid-trial stable-pass cases, zero stable-fail, and one mixed; one
stable-pass-labelled case has two valid passes and an error. Two repair generations
yielded one success and one fail-closed rejection. Passing scores still miss
poisoned claims, out-of-field fidelity errors, and a length-extended hash mutation.

Read `Documentation/10_deterministic_ai_io_hardening.md`,
`Documentation/evaluation_v2/post_hardening_triage.md`, and
`Documentation/11_io_hardening_sprint_report.md` before the next production
hardening sprint, alongside the frozen current-state methodology and triage.
Drive separately authorized work from those observations, including availability
and semantic validator blind spots. Recommendations are not automatic
authorization to implement controls. Do not add benchmark-specific production
filters or tune controls against frozen outcomes.

Near-term work remains explicitly scoped: reliability, SOC investigation depth,
MITRE ATT&CK STIX validation, containerization, and employer-facing documentation.
These roadmap items are not automatic authorization to implement them. Full
vector RAG remains deferred unless explicitly approved. Keep the document registry
stable unless a concrete bug requires a change.

Future work must not silently modify either benchmark suite or overwrite frozen
V1, V2 current-state, or V2 post-hardening official artifacts. Changed V2 suites/checks require new byte and semantic
hashes, distinct provenance/versioned experiments, and a new experimental baseline.
Keep the frozen V1 report models/comparison command compatible. Generated
`evals/results/` JSON files remain local/ignored. Official tracked benchmark
artifacts live under `Documentation/evaluation_results/` (V1) and
`Documentation/evaluation_v2/` (V2). Full vector RAG remains deferred, and the
document registry stays stable unless a concrete bug requires change.

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

For Codex-executed commands, use the repository virtual environment explicitly.
After making code changes, run:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

If Ruff formatting is needed, run:

```powershell
.\.venv\Scripts\python.exe -m ruff format .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
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
