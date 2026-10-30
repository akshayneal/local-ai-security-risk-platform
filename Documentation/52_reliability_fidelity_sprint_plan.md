# Sprint 8 diagnosis and pre-implementation scope

Experimental reliability patch only; no new feature, endpoint, UI, retriever,
reference pack, dependency, launcher/port change or release. Branch:
`feature/reliability-fidelity-sprint8`, from verified local/remote
`e7f61f4e7f8b56e14c6cf0d65fa461aff3e79417`. Main/peeled v2.3.0 remain
`fde00d0ca5d21eecbc6973cc784550ed453edb7a`.

## Gate 0

Windows 11 build 26300, existing CPython 3.13.1 venv, PowerShell 5.1.
No tracked/staged changes; one worktree; only 405 known untracked snapshot files.
All 590 s4check files, 13 Northstar files, 36 Sprint 7 official-run files and
installed AGENTS bytes match original manifests. Sprint 7 journal is completed;
no inherited Python/evaluation process or unknown journal. No inherited DB is
opened. Exact baseline CI 41133748390 rechecked completed/success at e7f61f4.
Focused baseline: 100 passed, one existing Starlette/httpx warning, 11.44 s.
Ruff/diff passed. No repeated full baseline. All commands use existing venv,
-B, pytest without cache provider and Ruff --no-cache.

## Verified diagnosis and ranked narrow corrections

1. AI Security: original provider attempts 9-12 all completed and returned
   insufficient_information with 3/4/2/3 findings. The public validator correctly
   rejected all four. The provider JSON Schema contains coverage enum and findings
   maxItems=12, with no cross-field branch constraint. Encode two explicit schema
   variants (advisory permits zero findings; insufficient requires zero findings
   and at least one gap). Validate the raw union and then the original public
   response. No relabeling, deletion, fabricated field or weaker outward contract.
   Shared system prompt saying two workflows is a plausible additional cause,
   not proven primary cause; correct that description and clarify coverage scope.
2. SOC: raw MAINT-ON inference asserted an infrastructure mismatch without an
   inventory. AUTH-ON used unqualified brute-force language. Existing finite
   identifier checks do not prove these semantic predicates. Add general task
   instructions preserving unknown ownership/reputation/intent, scoped supplied
   inventory facts and exact account roles. Keep useful conditional hypotheses.
   This remains prompt-guided; do not claim a deterministic entailment checker.
3. AI-risk: raw draft summary calls controls unimplemented; no-answer gaps call
   a policy undefined when only evidence is missing. Explicitly distinguish unknown,
   proposed, required, reported/established absent and supplied implemented/approved.
   Preserve supplied positive internal policy/approval and low-impact facts.
4. Citations: two raw logical document IDs were correctly removed. Do not promote
   them. Clarify exact envelope evidence_id as citation identity and test an eligible
   selected chunk through real analyzers/Inspector. Selection is not entailment.

## Tests, freeze and boundaries

Before application edits, commit six newly authored Maple submissions and rubric:
SEC-A/B first (highest priority), SOC-A/B, RISK-A/B. No Cedar replay/variant and no
old cases used as tuning gold. Supporting facts are embedded in new input records;
no live knowledge workspace/registry is needed. Test eligible citations with existing
synthetic fixtures in temporary test roots only. Record external API/schema
expectations and literal LF hashes, including Git round-trip identity.

Use explicit provider-visible anyOf variants, preserving the source_ids compatibility
alias, strict duplicate/extra fields, graph/source/category binding, byte caps,
quarantine and no-actions/not-verified status. Missing graph still avoids inference.
Write failing schema/fidelity-prompt regressions first; test good candidate, benign,
insufficient and hostile/contradictory paths without real calls. Semantic prompt
checks are software checks, not evidence that arbitrary model prose obeys them.

The exact allowlist is sprint8_preservation.json. Three application files only.
Historical source replay runs from a bounded immutable e7f61f4 archive in pytest
scratch directories, using a scratch Git index and process-local Git paths; no
real index/config/worktree modification. Old tests change only call/decorator
endpoints. AST proofs and corrupted-snapshot negatives retain every original
assertion/denominator. Old frozen runners/cases/readouts/manifests remain untouched.
The new active guard checks every other base blob and inherited hashes now.

## Live authorization and stopping

Exactly one optional foreground prospective run, at most six scheduled submissions
and SIX GLOBAL raw HTTP generation attempts, including retries and SOC repairs.
Reuse Sprint 7 transport classes read-only with a small locked six-attempt adapter;
reserve/fsync before sending, deny over-cap attempts and mark remaining cases
NOT RUN. No warm-up, debugging calls, retry of a failed case, resume or holdout.
Per HTTP timeout <=180 s, whole-run deadline 1500 s, response <=256 KB, retained
output <=4 MB. Freeze exact settings in the new plan. Read-only loopback preflight
must find exact installed qwen3:8b digest; no provider start/config/pull/fallback.
Use a fresh absent ignored Maple sibling, exclusive run ID, isolated audit journal.
Record executing HEAD before inference; synthetic outputs stay ignored and bounded.

Checkpoint order: (1) this diagnosis/protection and fresh frozen suite, (2) narrow
regressions/fixes, (3) one actual run/readout or truthful NOT RUN, (4) historical/
current gates, final full pytest once, Ruff/pip/diff, report, normal feature push
and exact-SHA CI. Repeat full software gates only after a genuine defect fix.
Manual workflow/visual acceptance and independent semantic adjudication remain
PENDING; no model-safety or causal improvement claim. Keep NO-GO for unresolved
semantic/availability failures or manual acceptance, regardless of green CI.
