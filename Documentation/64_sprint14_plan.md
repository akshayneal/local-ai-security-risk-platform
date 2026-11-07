# Sprint 14 prospective plan

Date: 2026-11-06. Status: experimental internal, off by default; RELEASE NO-GO.
Baseline: `feature/adaptive-typed-security-reasoning-sprint13` at
`285a6b5130e849daaea48406e1c9e1d7bc65ddf1`, equal to live origin.
Target: `feature/evidence-qualified-ingestion-sprint14`. No public route/UI change.

## Gate Zero

No staged or unstaged tracked changes; upstream divergence 0/0. Requested new
branch absent locally and remotely. Exactly 405 expected untracked s4check paths
remain user-owned and unmodified. Ignored .env, venv, logs, launcher lock,
workspaces, historical results and caches are preserved; secrets/log bodies were
not read. No Python evaluation process was present; only the existing Ollama app
and server were observed. No service changes are authorized.

Sprint 13 guard verified 645 protected pre-Sprint-13 Git blobs and 911 inherited
raw files: s4check 590 (405 visible, 185 ignored), Northstar 13, Cedar7 36,
Maple8 14, Birch9 18, Elm10 71, Larch11 72, Spruce12 97. Its final inventory
additionally verified 79 Willow files and 25 saved evidence artifacts. Willow
journals have 24 reservations and 24 completions, no pending/UNKNOWN; 76 stored
artifact hashes match. Historical Birch9 unknown_no_retry remains UNKNOWN.
No historical campaign is reopened. All existing preservation manifests remain
unchanged; a new baseline will inventory exact Sprint 13 source and raw bytes.

Existing Windows venv: CPython 3.13.1; pip check: no broken requirements.
Bare python resolves through WindowsApps, so commands use .venv/Scripts/python.exe.
GitHub run 42279803688 is push-triggered, completed/success, bound to the exact
baseline SHA: https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/42279803688.

## Question, contracts and authority

Can deterministic source qualification precede comparison without turning source
content into permission? Separate exact original bytes and field pointers from
application-side synthetic review/currentness, role, case/workflow/question,
time applicability, association and the resulting scoped relationship.

Use a small strict versioned internal contract and pure functions. Separate
source review arguments are application-owned eligibility assertions in an
internal synthetic demonstration, not authenticated institutional authority.
No new registry/retrieval workflow or enterprise IAM is introduced. Body source
IDs, revisions, current flags, approvals, policy claims, instructions, model
output and report text cannot grant authority. Revocation/current snapshots and
hashes must be rechecked at use/export. Hashes correlate bytes; they do not
authenticate or anonymize them. Unsupported real data is outside this sprint.

Eligibility precedes association. Association needs exact event/principal/asset/
process creation/resource/time/question scope, never IP alone or first-hit joins.
Multiple plausible eligible contexts abstain. Contradictory applicable assertions
remain conflicting. Scope mismatch, unknown semantics and unavailable input are
different states; none means a safe or authorized live event.

## Mapping policy and alternatives

Native supported slice: one selected DeviceNetworkEvents row through the existing
seven-table bounded JSON/CSV adapter. Preserve complete original upload bytes,
format, parsed bundle, original field types, row/field pointers and all omitted
row counts. Local/remote remain local/remote. ActionType/ResultType stay opaque;
this repository has no versioned mapping proving operation or completion.
Missing/ambiguous timestamps and process identity remain explicit. Never join
several rows into one invented record. Native comparison may correctly be
unassessable; this is a completed source-bound observation/report path.

A separate strict synthetic typed format supplies explicit event semantics and
independently reviewed synthetic authorization context for positive comparison.
Reuse unchanged Sprint 13 comparator/report contracts with derived-source labels
and explicit field lineage to separate originals. Do not mislabel the synthetic
format as Microsoft semantics. Reject arbitrary prose-to-policy parsing and
unreviewed requirement promotion. No existing analyzer/default/launcher changes.

## Threat model and required development checks

Cover legitimate alignment, mismatch, failed/attempted outcomes, missing rules,
ambiguous association, conflicts, wrong identity/process/time/action scope,
stale/revoked review, forged body metadata, role/workflow mismatch, mutated
requests/reports, duplicate keys, encoding/depth/size limits, exact scalar types
(including True versus 1), naive time, nested hostile annotations and escaped
JSON/Markdown export. Preserve original bytes and prove that model/report fields
cannot grant approval or execute actions. Use metamorphic operation, principal,
revision, annotation and irrelevant-row transformations. No source content in
error messages. Fail visible with stable refusal codes and coverage counts.

Each material failure records first broken stage, minimal reproducer, competing
explanation, bounded fix, positive/negative regression and remaining uncertainty
in an append-only decision journal. After two serious failed fixes, narrow scope
or defer architecture rather than prompt tune.

## Prospective evaluation and stopping rules

Development: at least 12 new opaque authored situations, freely iterable, disjoint
from diagnostic literals/identities. Diagnostic: 12 new cases, balanced across
legitimate, mismatch, unknown/conflict, authority attacks, unsupported mapping
and attempted/noncompleted outcomes. Input literals and separate scorer-only
key, rubric, accepted alternatives, evaluator, contract hashes and source commit
must be committed before the single offline diagnostic run. No key data is
serialized into an input. Freeze candidate before exposure; no scored source/key
changes afterward. Preserve every failure; fixes require a new version/new suite.

Metrics are separate per-case extraction integrity, eligibility/refusal,
association, authored comparison expectation and report/export integrity, with
per-class denominators. No population accuracy, independent validation, model
safety or analyst usefulness claim. Any fabricated permission/action, lost source,
wrong association or hidden unsupported mapping fails the relevant gate.

Exact inference budget: ZERO raw model sends, retries, repairs, embedding calls or
downloads. No historical Sprint 4-13 experiment/diagnostic reruns. Deterministic
preservation tests/replay at immutable history are software checks, not new
experiments. Diagnostic has an exclusive create-before-run barrier; interrupted
reservation means stop and recover read-only, never silently rerun.

Sprint 13 masked 60-output packet and separate key stay exact. New guide and blank
machine-readable record retain all review IDs and leave human identity/judgments
empty: INDEPENDENT HUMAN REVIEW PENDING (0 completed). USER VISUAL QA PENDING.

## P1 decisions and runtime limits

Timeout work is provisionally deferred pending bounded audit: frontend 300s and
Ollama 300s are independent inactivity budgets, transport retries can duplicate
uncertain work, and SOC can request a policy repair. A scalar timeout increase
does not establish a lifecycle deadline/cancellation/idempotency. Gate D permits
evidence-backed deferral without changing production accounting; document honest
UNKNOWN guidance and a minimal future design. P0 takes priority.

Read-only nvidia-smi/ollama ps/model identity may be recorded while idle. No model
profiling dispatch, model downloads, process or system changes. System RAM is
separate from GPU VRAM; make no unmeasured offload/performance claims.

## Preservation, validation and handoff

Add only an import/decorator migration to the immediate Sprint 13 scope test;
replay original assertions at immutable baseline and retain negative mutation
proof. New exact-path guard protects every other original tracked blob and all
inherited raw bytes. Never weaken old scopes/hashes or execute private s4check.

Run focused tests, full deterministic pytest, Ruff on tracked Python files,
pip check, diff checks and preservation checks. Persist milestone commits and
resumable checkpoint, freeze once and score once. Final normal feature push is
explicitly authorized by the sprint prompt; verify origin equals final local SHA
and inspect exact-SHA CI jobs. No main/tag/PR/merge/release changes. Final readout
separates Gates A/B/C, diagnostic limitations, timeout deferral, measured hardware,
zero sends, pending human/visual review and Sprint 15 scope.
