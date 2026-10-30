# Sprint 6: experimental technical AI Security Assessment

## Gate 0 and immutable baseline

Verified 2026-10-30: local and live remote
`feature/three-pillar-knowledge-foundation` at
`a43814b43df9bd677469f002c785ac0710c4404d`, zero divergence, no tracked/staged diff.
Main and peeled v2.3.0: `fde00d0ca5d21eecbc6973cc784550ed453edb7a`.
Sprint 6 branch was absent locally/remotely; created
`feature/ai-security-assessment-v1` from that exact base, without rewriting history.

All 405 visible untracked s4check files match Sprint 5 hashes. Their flat top-level
structure has no Git/redirect conflict and root pytest discovers only `tests/`.
They remain untracked/unmodified; never hide, stage, remove or operate inside them.
No inherited Python evaluation process was observed. Existing logs/journals,
Ollama and launchers are left alone. The existing Northstar workspace has 13 files
(eight documents, config/reviews, registry and existing WAL/SHM); hash them read-only,
never open its SQLite database or run workspace commands against it this sprint.
The new preservation manifest records exact policy, workspace and inherited hashes.

Existing Windows venv: CPython 3.13.1 AMD64. Baseline
`.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider`:
**1877 passed**, one existing Starlette/httpx warning, 95.44 s.
Ruff `check --no-cache .`, pip check and Git diff inspection pass. No installations.
Use -B and disabled pytest/Ruff caches for subsequent checks.

User observation: the development UI looked provisionally acceptable. This is a
visual smoke observation only. Existing SOC/governance analysis, knowledge retrieval
and generated output have NOT been manually tested or accepted. Release blocked.

## Bounded implementation and file inventory

New focused modules: `app/ai_security_contracts.py` (immutable typed graph/design
claims), `app/ai_security_sources.py` (fixed versioned local guidance),
`app/ai_security_analyzer.py` (prompt, existing model call, deterministic references),
`app/ai_security_api.py` (bounded typed route and sanitized errors),
`dashboard/ai_security.py` (JSON design editor, read-only provenance, safe exports)
and `dashboard/pages/ai_security_assessment.py`.

Existing changes: README, dashboard navigation/product copy after route/UI tests pass, focused navigation
tests, and the historical Sprint 5 changed-path guard. Existing SOC/governance
schemas, prompts, analyzers, inference settings, knowledge contracts/registry,
Inspector/corrections, launchers and dependencies remain unchanged.

New versioned authored guidance under `reference_material/ai_security_v1/`,
synthetic examples under `sample_data/ai_security_demo_v1/`, cases/rubric/runner
under `evals/ai_security_v1/`, and new evidence under `Documentation/ai_security_v1/`.
The exact existing-file allowlist and protected base blobs live in
`Documentation/sprint6_preservation.json`. Do not broadly exempt old source trees.

Discovery refinement before implementation: Sprint 5's frozen runner also binds
`app/main.py` to its original source hash. Preserve that file and the frozen runner.
`app/ai_security_api.py:app` will be an explicit experimental ASGI gateway composing
the existing router and the new route. This is an additional foreground entry point,
not a source/hash exception or a parallel model provider. Existing launchers keep
their two-workflow entry point. The new page must state the gateway requirement;
manual startup instructions are part of the slice. No automatic service switch.

Historical migration: pin only Sprint 5's changed-path comparison to its immutable
end `a43814b...`. Preserve its original allowlists, live protected hashes, policy
checks and inherited-file checks. No old outcomes/gold/scorers/source snapshots change.
Add a separate Sprint 6 diff guard plus a regression for this exact fixed range.

## Contracts and trust boundaries

Input: application/purpose/assumptions, actors, uniquely identified components,
directed flows, declared boundary crossings and classifications, ingestion surfaces,
declared tool capabilities/invokers/human gates, claimed controls, separately supplied
unverified implementation evidence, oversight and limitations. IDs and references
are checked without a graph dependency. Strict extra fields, caps, total UTF-8
budget and duplicate JSON-key rejection prevent ambiguous requests. These are
submitted architecture claims, never access grants or live tool permissions.

Output: bounded candidate technical hypotheses with category, affected component/
flow/control/evidence IDs, prerequisites, possible impact, proposed mitigation,
test recommendation, gaps and allowed guidance IDs. Approval/exploitation/control
verification remain not verified; no actions executed. Empty/insufficient designs
receive an explicit insufficient-information result, never invented graph edges.
Benign designs may have no candidate findings; this is not a clean bill of health.

Use existing local Ollama JSON-schema interface with the existing complete-context
loopback contract, no tools/network scans/provider migration. Original evidence
is preserved; prompt copies are quarantined before JSON escaping. Model prose is
unassessed; structural checks are not general entailment or injection resistance.

Use the shared EvidenceRecord/source-provenance/serialization patterns. Provide a
read-only AI-security provenance panel rather than extending historic Inspector
workflow/correction identities. Session corrections for this new workflow remain
deferred. Sources are locally authored versioned guidance, not OWASP/NIST/MITRE
control mappings or organizational policy. Missing/corrupt guidance fails visibly.

Optional third-pillar organizational knowledge is deferred: no new grants, no
workspace access and no fallback into SOC/AI-risk documents. Extra local-knowledge,
access/path/authority fields are rejected in the new request. Basic execution is
independent of operator workspaces.

## Frozen evaluation and checkpoints

Before evaluation outcomes, commit 24 authored synthetic cases: six technical-risk,
six benign/positive-preservation, six hostile/instruction/source-forgery and six
reference/scope/unknown/malformed controls. Freeze inputs, stub outputs, source
snapshots, expectations, rubric and hashes. Evaluate input rejection, result
structure, source membership, declared category consistency, ID membership,
missing-evidence status, false authority promotion and accepted-case counts with
separate denominators. Stub properties are software checks, not model effectiveness.
Do not tune ranking/prompts to recorded outcomes or change gold after failures.

Live inference is lower priority and will be **LIVE INFERENCE NOT RUN (0)** in this
plan. No embeddings, downloads, cloud AI, service starts/restarts or live evaluation.
No independent human adjudication is claimed. Keep prior evaluation artifacts intact.

Checkpoints: (1) plan/current preservation and narrow historical range;
(2) frozen examples/guidance/cases; (3) contracts and backend with hostile tests;
(4) UI tests then truthful Experimental navigation; (5) offline evidence/report;
(6) full deterministic gates and non-force push of Sprint 6 branch only, exact-SHA CI.

Acceptance: real typed request -> route -> existing model interface (stub in tests)
-> fail-closed ID/source/status validator -> request-bound metadata -> UI/export;
concurrent request-context reset; explicit insufficiency and benign preservation;
all old contracts/replays/corrections unchanged; protected workspace and 405 hashes
unchanged; no phantom Active page, no actions, no release. If core boundaries fail,
leave the page Planned/Prototype and preserve a useful incomplete checkpoint.

Final gates: focused tests, full pytest, uncached Ruff, pip check, diff check,
historic hashes/current scope/policy/protected workspace, exact inventory and CI.
USER VISUAL QA PENDING for the new workflow; both prior workflows' manual acceptance
also remains pending. Final hardening requires fixed-case human semantic and
end-to-end review, not another feature expansion or safety certification claim.
