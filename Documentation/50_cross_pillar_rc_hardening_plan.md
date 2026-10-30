# Sprint 7 frozen scope and checkpoint plan

Status: experimental development; no release, merge, tag, PR or main push.
Starting branch: feature/ai-security-assessment-v1. Verified local/remote base:
`1c4f937f2b067a4a2b0d8ac8cf5db4f552555d00`. Work branch:
`feature/cross-pillar-rc-hardening`. Main and peeled v2.3.0 remain
`fde00d0ca5d21eecbc6973cc784550ed453edb7a`.

## Gate 0 evidence and inherited exception

Windows 11 build 26300; Windows PowerShell 5.1.26100.9711; existing .venv
CPython 3.13.1. Bare python resolves to the Windows Store alias, so commands use
`.\.venv\Scripts\python.exe -B`. Baseline `-m pytest -q -p no:cacheprovider`:
1958 passed, one existing Starlette/httpx deprecation warning, 101.02 seconds.
Ruff `check --no-cache .`, pip check and diff check passed. No tracked/staged
changes; one worktree. Git reports 405 known untracked snapshot files. Every
original snapshot hash, 13 Northstar workspace hashes and AGENTS exact bytes match.
185 additional ignored caches (181 bytecode, four pytest cache files) caused the
required initial stop. The user explicitly authorized preserving them untouched.
Their exact hashes are now bound in sprint7_preservation.json. No s4check code
will be executed/imported. No inherited journals or evaluation processes observed;
only shared Ollama processes. All checks use -B and no pytest cache provider.

## Ordered checkpoints

0. This scope/manifest commit, before implementation.
1. Freeze 12 new synthetic submissions, fresh reviewed synthetic corpus, rubric,
   source hashes, runner and transport accounting; no historic cases reused as
   tuning data. Optional holdout omitted to prioritize baseline evidence.
2. Canonical development ASGI gateway app.ai_security_api:app; strict legacy
   state stop-only migration; mocked Windows and cross-platform regressions.
   Historical guards retain their old intervals and immutable source snapshots.
3. One foreground sequential real-provider run if read-only preflight remains
   available, 12 scheduled submissions, 32 total raw generation HTTP attempts,
   no model/embedding downloads or requests to external providers. SDK/default
   and complete-context paths both pass evaluation-only counting transports.
   Durable exclusive run directory and append-only journal; no selective reruns.
4. Only demonstrated general defects with a failing deterministic regression
   before a smallest compatible fix. Model semantic failures may remain open.
5. Full deterministic/PowerShell/Ruff/pip/diff gates, protected identity checks,
   readout and inventory; non-force feature push and exact-SHA CI inspection.

## Migration invariants and source boundaries

New launches use only the composed three-workflow gateway on 8235; UI remains
8535 and shared Ollama 11434. Start refuses legacy recorded state with manual
Stop/Start instructions before any automatic stop/reuse. Stop validates exactly
the old or new fixed command plus live provenance; no arbitrary module override.
No shortcut installer, scripts/demo, app/main.py, original analyzers/prompts,
dependencies, environment, registry or prior frozen evaluation changes.

The manifest lists exact authorized paths in advance. Sprint 5/6 historical
scope endpoints/source hashes are checked at immutable commits, with executable
AST proofs for the narrowly changed guards; new current-tree protection covers
all unmodified base files and all inherited bytes. No old allowlists broadened.

## Evaluation commitments before outcomes

Preflight saw Ollama 0.40.13 and qwen3:8b digest
500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41.
The next checkpoint freezes inputs, rubric and precise runtime/limits before any
model generation. No background services/browser/GUI are started. Full synthetic
responses stay in a new ignored bounded directory; tracked reports retain hashes,
minimal evidence and descriptive metrics. Implementation-authored qualitative
review is explicitly separate from deterministic checks; independent adjudication
and user workflow/final visual acceptance remain pending. NO-GO while any required
manual acceptance or important semantic/reliability gate is unresolved.
