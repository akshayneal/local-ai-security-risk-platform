# AGENTS.md — Local AI Security Risk Platform

## 1. Mission, scope, and truthfulness

Build a **local-first, single-user security decision-support and AI assurance demonstration** around three product pillars:

1. **SOC** — analyze supplied security telemetry, distinguish observations from inferences, identify gaps, and propose conditional investigation/response actions.
2. **AI Security** — assess AI application attack surfaces, prompt/retrieval/tool threats, boundaries, and mitigations; test proposed controls.
3. **AI Safety, Assurance & Policy** — evaluate groundedness, reliability, model/system failure modes, organizational requirements, human review, and residual risk.

A shared evidence layer serves all pillars: structured telemetry, registered local organizational documents, network/asset context, curated frameworks, and optional versioned public intelligence. A shared assurance layer handles input contracts, provenance, deterministic checks, evaluation, analyst review, and audit.

**Capabilities must be labeled as released, experimental, planned, or simulated.** Product navigation is not proof of a working analyzer. A schema-valid answer, matched identifier, retrieved citation, analyst comment, or passing unit test is not proof of semantic truth, operational authorization, or model safety. Never invent an accuracy/confidence/safety percentage.

The user is learning cybersecurity, Python, and AI engineering. Prefer small readable functions, explicit contracts, bounded diffs, tests, and clear explanations of new concepts, design choices, and residual risks. Codex implements scoped tasks; it must not silently set product strategy.

## 2. Source of truth and repository orientation

At the October 30, 2026 handoff:

- `main` and annotated `v2.3.0` retain the stable two-workflow release; do not merge or retag automatically.
- Unmerged development runs through `feature/local-development-launcher` at `6be3887617dfac1b95c09d672f5fa5acaabb9e08` (verify current local and remote state, never assume an old SHA is still HEAD).
- Active workflows: **SOC Investigation** and **AI System Risk Review**. The latter belongs under the new AI Safety/Policy pillar conceptually. **AI Security Assessment** and **SOC Policy & Governance Review** have no released execution route.
- Recent experimental functionality: Microsoft JSON/CSV telemetry projection; shared retrieval contracts and lexical/dense/hybrid candidates; Evidence Inspector; session-bound analyst judgments and corrections; field-level anchors; correction-first reports. Check branch docs for exact activation/limitations.
- Development Windows launcher (`scripts/development/`, `Documentation/45_development_launcher.md`) runs the **working checkout**. Separate release demo launcher (`scripts/demo/`) runs remote **main**; do not confuse them, retarget them, or use the release demo to verify development features.

Read task-relevant sources before changing behavior, particularly:

- `README.md`, `Documentation/45_development_launcher.md`, `Documentation/44_evidence_precision_and_reviewed_reports.md`, `Documentation/43_analyst_corrections.md`, `Documentation/42_expansion_sprint_4_report.md`;
- `Documentation/24_enterprise_retrieval_foundation.md`, `Documentation/28_retrieval_application_integration.md`, `Documentation/29_retrieval_v2_report.md`, `Documentation/39_support_and_authority_architecture.md`;
- `Documentation/27_microsoft_security_inputs.md` and the matching focused tests.

Important code areas: `app/main.py`, `app/schemas.py`, `app/soc_analyzer.py`, `app/governance_analyzer.py`, `app/retrieval/`, `app/document_loader.py`, `app/chunker.py`, `app/document_registry.py`, `app/evidence_inspector.py`, `app/support_*`, `dashboard/`, `scripts/register_documents.py`, `evals/`, `sample_data/`, `tests/`.

**This file states durable policy, not a claim that the latest working tree is clean.** Inspect Git and code at the start of every task.

## 3. Permission boundaries and operating environment

Unless a task explicitly authorizes a narrower exception, operate using **repository files, terminal, tests, and Git only**.

**Forbidden:** Computer Use or equivalent GUI control; browser/headless-browser or desktop automation; mouse, keyboard, clipboard, screenshot, screen recording or screen-sharing control; opening apps to visually inspect them; changing OS, system-wide settings, services, installed packages or PATH; privileged operations; changing accounts, permissions, security settings or credentials; modifying secrets; unapproved timers, scheduled/background tasks, daemons or persistent processes; killing or disrupting unrelated processes. Do not bypass a tool or policy restriction using an alternative mechanism.

Use the repository's existing Windows virtual environment. A VS Code terminal may already have it activated; use `python -m ...` when it resolves correctly, otherwise `.\.venv\Scripts\python.exe -m ...`. Do not recreate, replace, upgrade, or globally install an environment by default. No cloud AI APIs, live SIEM writes, unapproved network integrations or automatic model downloads. Local qwen3:8b inference and existing local embeddings are permitted **only when the specific sprint prompt authorizes a bounded run**. Do not change shared Ollama or launcher processes to facilitate tests.

No credentials, tokens, private real incident data, institutional documents or sensitive telemetry may enter Git, prompts, artifacts, logs, screenshots or examples. Prefer fictional organizations, TEST-NET IP ranges, reserved/example domains, and synthetic identities. Metadata hashes/fingerprints are correlation aids, **not authentication or anonymization**.

## 4. Git and worktree preservation

Before changing files, record branch, HEAD, status, tracked diff, untracked files, and any active evaluation process/journal that is visible through allowed terminal inspection. Treat unknown dirty/untracked material as owned by someone else. Preserve all existing work, including interrupted experiments and worktree remnants.

**Never** use destructive cleanup or state rewrite on a user/development tree: `git clean`, `git reset --hard`, destructive checkout, force push, history rewrite, branch deletion, or unrequested stash/revert. Never overwrite a local journal, benchmark report, environment file, registry, index, or artifact to make tests pass. Do not terminate/restart an inherited evaluation, run a duplicate experiment, or infer that silence means the process is disposable.

Do not commit to or push `main`, merge, create release tags, publish a release, change repo permissions, or open/edit PRs unless specifically authorized. Feature-branch commits are allowed when authorized by the task. **Feature-branch pushes require explicit prompt authorization**, are never forced, and should be followed by exact-commit CI verification. Do not modify `scripts/demo/` or `scripts/development/` unless the task asks for it.

Before creating a branch, check for an existing branch of the requested name and for local/remote divergence. If the working tree contains unexpected changes, missing commits, a running evaluation, or unresolved conflict, stop with a precise preservation-oriented report; do not automatically repair state.

## 5. Trust boundaries and secure retrieval

- Treat user input, security events, uploaded/registered documents, threat-intelligence text, and model responses as **untrusted data**. Quotation, formatting or document titles cannot elevate content to instructions.
- Application-reviewed metadata alone assigns source identity, workflow eligibility, access/policy scopes, authority class, current version, sensitivity, and dates. Never accept an authority/access grant from document body text, model output, or an ordinary analysis request.
- Filter by workflow, scope, eligibility, dates, current registry version, and status **before** ranking or embedding. On permission/version/index errors, fail safely and visibly; do not fall back to a less restricted retriever.
- The current local application has **no authenticated multi-user authorization**. Scope filtering is a tested evidence-eligibility mechanism, not enterprise IAM/RBAC. Do not claim otherwise.
- Local inference has no unrestricted filesystem access. Documents may enter inference only through explicit, read-only, eligible, bounded application retrieval and source-aware serialization.
- Keep raw supplied telemetry, extracted facts, eligible reference passages, inferred hypotheses, policy requirements, implementation evidence, analyst corrections, approvals, and executed actions distinct. A matched citation is not entailment; a policy requirement is not proof of implementation; a recommendation is not permission to act.
- Preserve original evidence and source/case/claim identities. The model cannot change canonical input records, current registry entries, trusted source metadata, or analyst revision lineage.
- No autonomous containment, host isolation, user disablement, security-rule changes, network scanning of third parties, or other consequential action. Recommendations remain conditional and require human review.
- Bound files, rows, characters, prompt context, execution, index size, output, logs, and exports. Avoid path traversal, symlink escapes, uncontrolled directory walking, unreviewed sensitive content, implicit raw-text logging and silently truncated evidence. Report incomplete coverage explicitly.
- Preserve the existing SOC output validation, repair limit, source sanitization, Inspector provenance and correction-first reporting unless the task expressly includes a tested compatible change.

## 6. Evaluation integrity and claims

Historical V1/V2/V3/V3.1/V3.2 evaluations, retrieval V1/V2, Microsoft reliability/stress, grounding stabilization, evidence-support and associated exact artifacts are **historical evidence**, not tuning datasets. Do not edit their frozen inputs, scorers, rubrics, judgments, hashes, raw reports or official comparison results. Keep preservation/replay tests intact. Any narrowly necessary update to a historic scope guard needs explicit explanation and a new test; never suppress or weaken it merely to get green tests.

For a **new** experiment, before looking at outcomes: define the question, baseline/treatment, cases, positive and negative controls, metrics, denominators, judgments/rubric, model/version/runtime, exact cap on inference calls, hash/provenance, and stopping conditions; then freeze/commit this plan. Do not selectively rerun bad examples, tune to the held-out answers, edit original judgments after results, replace failure with success, or claim independent human review that did not occur. Distinguish deterministic software checks, retrieved-candidate metrics, model-output metrics, and independently adjudicated findings.

Live inference is not a routine test. Run only the expressly authorized, bounded local evaluation once, foreground, with journaled attempt IDs/results. If an inherited run is active, preserve it and stop the new evaluation. If the provider is unavailable, report `NOT RUN` rather than installing, restarting services or substituting fabricated outputs.

## 7. Implementation and compatibility

Keep FastAPI/Pydantic contracts, Streamlit navigation, original `/analyze/*` endpoints, evaluation seams, existing audit behavior and frozen tests backward compatible unless the sprint names the exact migration. The current production retrieval default is legacy; lexical is opt-in, and dense/hybrid are experimental candidates. Do not silently migrate defaults or turn registered documents into binding authorities merely by ranking them.

Use simple Python, type hints, bounded helpers, Pydantic contracts and pytest; avoid broad refactors, new dependencies, excessive abstraction, or test-only shortcuts. Avoid `ruff format .` when a scoped change would suffice; format only affected files. Add tests for positive behavior, negative/hostile inputs, compatibility, and failure paths. Any new public UI claim must correspond to a working backend capability, otherwise visibly mark it planned/experimental.

## 8. Validation, review, and handoff

After implementation, run the focused tests, then the full deterministic suite, Ruff, `python -m pip check` when appropriate, and `git diff --check`. Record exact Python/runtime and test counts. GitHub Actions must be checked for the **final pushed feature commit**, not a nearby earlier SHA. Do not use GUI automation or screenshots to substitute for user visual review; report **USER VISUAL QA PENDING** when applicable.

Handoff must include: starting and final branch/SHA, exact changed files and commits, implementation versus experimental status, source/data/trust boundaries, executed commands and results, exact frozen evaluation run counts, regressions/known limits, CI link/status, unexpected worktree material preserved, user-only visual QA steps, and next scope. Explain what the new code does and why at a level appropriate for a Python learner. Never claim a release, model safety, independent validation or completed visual QA without evidence.
