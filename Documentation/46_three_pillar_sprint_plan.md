# Sprint 5: three pillars and reviewed local knowledge

Status: experimental development, not a release. Date: 2026-10-30.

## Observed starting state and preservation

Starting branch `feature/local-development-launcher`, HEAD and live remote
`6be3887617dfac1b95c09d672f5fa5acaabb9e08`; ancestor evidence-precision checkpoint
`d7348af17f054a0d4d2c96b8f7d1b2265a712d9c`, followed by three launcher commits.
Main and peeled v2.3.0 remain `fde00d0ca5d21eecbc6973cc784550ed453edb7a`.
The sprint branch was absent locally/remotely and was created from that exact HEAD.
No merge, tag, launcher edit or stable demo change is authorized.

The user replaced AGENTS.md intentionally. Preserve its bytes, SHA-256
`17269f4f2e115f2b0c161ccbfd8832fa176e9a2bf17a365440b0c7dd16814a3d`.
Its unchanged contents may be included in the initial checkpoint.

Protected preexisting material: 405 untracked files under `evals/results/s4check/`.
The user explicitly authorized continuing around these remnants. Read-only structure
inspection found copied app/dashboard/tests/docs, no .git entry, no redirect target,
and no registered secondary worktree. Root pytest.ini specifies `testpaths = tests`;
the snapshot is outside discovery. Root Ruff passed with it present. Do not stage,
modify, relocate, hide or remove it. Preserve ignored logs, evaluation journals,
registries, caches, .env and .venv. No Python evaluation process was observed; a
preexisting Ollama process was left alone. This is a point-in-time observation.

Existing Windows venv: CPython 3.13.1, AMD64. Baseline command
`.\\.venv\\Scripts\\python.exe -m pytest -q`: **1792 passed, 4 failed**, one existing
Starlette/httpx deprecation warning, 90.85 seconds. The failures are solely the
intentionally replaced AGENTS.md against old scope/hash guards: correction scope,
grounding preservation, release retrieval scope, Sprint 4 preservation. Baseline
Ruff, pip check and git diff --check passed. Two exploratory rg commands used an
absent pyproject.toml / Windows wildcard operand and returned errors; no files changed.

## Product status map

| Status | Capabilities |
| --- | --- |
| Released (main/v2.3.0) | SOC Investigation and AI System Risk Review, curated local guidance, advisory results |
| Unmerged but functional | Microsoft file adapter, shared retrieval contracts, opt-in curated lexical, Inspector, session corrections/field anchors, reviewed reports, development launcher |
| Sprint 5 experimental | Reviewed registered local-document bridge, bounded CLI/workspace inspection, three-pillar copy, synthetic organization, offline bridge evaluation |
| Planned | Runnable technical AI Security Assessment; standalone SOC Policy & Governance Review; authenticated document portal |

SOC analyzes supplied telemetry. AI Security has a product location and pipeline
adversarial tests, but no third analyzer. AI Safety, Assurance & Policy contains
the existing AI System Risk Review; API/workflow identities stay unchanged.
Platform Evaluation is application self-evaluation. Policy applicability and model
correctness are separate: even an applicable requirement does not prove execution,
approval, implementation or semantic entailment.

## Contracts and acceptance gates

1. Historical audits use fixed original ranges, retaining old allowed paths and
   exact artifact hashes. A separate Sprint 5 manifest freezes base identities and
   allows only the named implementation files; frozen inputs/results/scorers remain
   live byte-checked. No historical outcomes are tuning data.
2. No changes to public analysis schemas, default generation arguments, legacy or
   curated lexical defaults. UI routes add only a strict boolean, default off,
   projected away before the original analyzers. Forged grants are rejected there.
3. Only an operator-selected workspace name under the designated ignored local
   directory is accepted. Flat bounded TXT/MD/PDF admission reuses existing loader,
   chunker, registry and importer. Reviewed sidecars bind exact full hashes and
   versions separately from content; new/changed documents have no implicit approval.
4. Workflow/access/unit/policy/date/status/current registry checks precede BM25.
   No fallback on malformed/missing/stale workspace, no API upload/path reader,
   model tools, cloud dependency, dense migration or automatic ingestion.
5. Bound corpus, metadata, extraction, context and output metadata. Report eligible,
   selected and cited identities and incomplete/no-answer limits. A related hit is
   never certified as support. Existing instruction quarantine and source allowlist
   remain. Context failures refuse before generation; no silent source eviction.
6. For each active workflow, test request -> registered retrieval -> serialized
   prompt -> stub model -> existing validator -> Inspector -> export, including an
   eligible citation and rejection of fabricated/stale/forbidden sources.
7. Freeze new synthetic cases/source hashes/rubric before evaluation. At least 20
   distinct deterministic cases with denominators; no semantic reliability claims.
   Optional live evaluation is **NOT RUN unless separately predeclared and all gates
   pass**; this sprint may deliver offline evidence only, with zero live calls.
8. Focused checks then full pytest, Ruff, pip check, diff check, protected-material
   identity check, checkpoint commits and one non-force push of this branch only.
   Verify hosted CI for the exact final SHA. USER VISUAL QA PENDING.

## Planned file inventory

The machine-readable exact allowlist is `sprint5_preservation.json`. Existing edits
are limited to .gitignore (private workspace only), README, orchestration, Inspector,
main/UI request contracts, dashboard navigation/product/workflow/Microsoft/client
and Inspector display plumbing, and narrowly explained preservation tests/helpers.
New modules: local knowledge contracts/workspace/CLI and dashboard inspection page;
new synthetic pack, bridge evaluation, focused tests, docs 46/47 and new manifest.
No dependencies, launchers, original prompts/analyzers, frozen suites/scorers/results,
source cards, public schemas or existing ingestion implementation need alteration.

## Checkpoints and evaluation discipline

Plan/preservation -> frozen synthetic sources/cases -> bridge/security tests ->
three-pillar UI -> report/final gates/CI. Small commits may combine adjacent steps.
If a hard security boundary fails, preserve artifacts and report it; do not disguise
an incomplete bridge as delivered. General prose entailment, authenticated approval,
transactional multi-user authorization, portal and third analyzer remain deferred.

Implementation-authored synthetic judgments are not independently adjudicated.
Optional live inference is skipped to prioritize deterministic security and review.
No model outcomes may be invented. See report 47 for actual final execution results.

## Historical closeout checkpoint

`9af0344` fixed the old correction/retrieval scope comparisons at their final
pre-Sprint-5 boundary, retaining their original allowed changes. Other historical
hash guards resolve only named authorized source edits at the verified Sprint 5
base; every other old data/scorer/report hash remains checked against current bytes.
The new guard freezes all other tracked files and installed AGENTS.md bytes.
Thirteen focused historical/preservation checks passed before implementation.

`45a845d` committed 26 new cases, rubric and synthetic snapshots. `65b6587` corrected
only the pre-outcome freeze hashes to repository LF bytes for Windows/Linux replay;
no case, judgment or source content changed and no evaluation had run.

The bridge also needs one narrow `app/inference_context.py` edit: enable the existing
complete-context, no-truncation/no-shift local runtime contract for opted-in knowledge
requests in both analyzers. The old default remains unchanged. The source exception
is recorded explicitly in the new manifest; original analyzer/prompt files remain
untouched. Focused bridge/compatibility/correction/report checks: 134 passed, one
existing warning. Initial Ruff found import order, fixture-import and nested-with
style issues, corrected with scoped edits; these were not application failures.
