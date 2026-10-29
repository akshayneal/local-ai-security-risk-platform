# Expansion sprint 2 closeout

Scope: Microsoft Security local input profile, trust-preserving lexical integration,
fresh retrieval V2 comparison and a separate Microsoft app-level stress family.
No new practitioner workflow, cloud AI/API call, credential, dependency, release,
merge or tag. The final handoff SHA is the head of
`feature/microsoft-soc-retrieval-integration` after this closeout is committed.

## State and checkpoints

Started clean/synchronized on `feature/enterprise-retrieval-expansion` at
`8faa103087475be15ef1fc4ee3166dacb56a6d1c`. Fetch confirmed `origin/main` and peeled
`v2.3.0` remain `fde00d0ca5d21eecbc6973cc784550ed453edb7a`; annotated tag object
remains `22e5e1704940c41284d6b29e393fd51958f3ba34`. Created the child branch from
that foundation, preserving the foundation branch. No resets/cleans/force pushes.

| Checkpoint | Commit |
| --- | --- |
| Microsoft contracts, adapter, bounds, samples | `a0cf91fc094c43a5bb7994682ca030a43c9e3593` |
| SOC input profile and submission | `8dab9f6d35596f9ef9cf3ebe5bc6fe645bea4a22` |
| Evidence serialization, shared shadow/opt-in | `99579f6d75f4167a7b9a4c4e879a04c24c7bbf3d` |
| Historical treatment identity correction | `8675d666c17d107f04af1fb5a8bcca41f60ef73d` |
| V2 fixtures/judgments/metrics/plan frozen before results | `cae8dd9fd6369b6ea39609abb63b81c3ce6e740d` |
| V2 live comparison/vectors/exact offline replay | `e4141fa1d33d6b64cbbb305e9c9b229a9280c2a7` |
| Microsoft stress preflight/harness | `acd92d966ce115bd44c884e9e532aa66d0ca94ef` |
| Neighboring telemetry preservation and upload/real lexical coverage | `0f90fd543614e68609f6aedfc0e9d9440e9c368c` |
| Selected live baseline, provenance replay and manual triage | `9c903a9ba8ac90d15008ff0ff9df2035256523fc` |

Each checkpoint was pushed. Early hosted gates exposed historical preservation
assertions that intentionally prohibited any new application change. Their exact
old identities are now checked at the foundation boundary for only four authorized
integration files; original frozen manifests, suite/scorer meanings and results
remain unchanged. The treatment identity assertion was missed in the first retrieval
checkpoint and corrected in the immediate follow-up. No benchmark failure was
addressed by changing a frozen score or relaxing production defenses.

## Delivered input experience

See [Microsoft inputs and SC-200 practice](27_microsoft_security_inputs.md).
Supported tables: AlertInfo, AlertEvidence, DeviceProcessEvents, DeviceNetworkEvents,
DeviceLogonEvents, SigninLogs, SecurityIncident. Official Microsoft Learn source
pages and access date **2026-10-29** are recorded there with original concise KQL.

`SocInputAdapter` protocol / `MicrosoftSocAdapter` produce `NormalizedSocCase`:
unchanged `SocAlertRequest` plus table/row/field/exact-value observations, row counts,
entities, AlertId links and warnings. No vendor-specific analyzer or canonical-schema
expansion. JSON bundle text/files and explicit one-table CSV are supported. Unknown
fields, nested values, row order and duplicate rows remain in canonical raw JSON;
duplicate JSON keys and malformed/oversized structure are rejected. CSV values stay
strings, preserving leading zeros and Windows multiline commands.

Canonical JSON uses deterministic field-per-line formatting so existing instruction
quarantine does not erase unrelated telemetry on the same line. Original evidence
stays intact; only the model-facing high-confidence instruction span is quarantined.
Indicators/entities are deduplicated without interpreting maliciousness. Previews
can truncate summaries/lists but never the raw evidence. Severity disagreements,
unmatched entities, missing protocol and MFA/CA uncertainty remain visible.

Bounds: 80,000 uploaded/serialized UTF-8 bytes; 7 supported tables; 50 rows/table;
100 total rows; 64 fields/object; 128-character names; 4,096-character strings;
8-level nesting; 5,000 values/containers; canonical request limits unchanged.

SOC Investigation now has Generic/Microsoft input profiles. Microsoft mode supports
sample loading, paste/upload JSON, CSV/table/case selection, normalization preview,
existing hardened API submission and existing JSON/Markdown export semantics.
Changing profile/input invalidates Microsoft results. Generic behavior remains
covered by the original UI suite. No internal prompts are displayed. No native-browser
visual smoke was run; Streamlit AppTest covers rendering, sample/paste/upload,
invalid/oversize input, submission, exports and stale-result handling.

Eight synthetic SOC examples cover MFA/CA uncertainty, embedded command injection,
443 without protocol, severity conflict, maintenance, multistage evidence, logon
identity ambiguity and a strong suspicious sequence. No real tenant/customer data.

## Retrieval integration and experiment

See [application integration](28_retrieval_application_integration.md) and
[V2 findings](29_retrieval_v2_report.md). Both existing analyzers share orchestration.
Default remains legacy with exact original prompts/context/source handling.
`RETRIEVAL_SHADOW_BACKEND=lexical` runs the candidate separately and writes only safe
identity/rank/overlap/latency/fingerprint/fixed-error diagnostics to an ignored JSONL.
Shadow retrieval and log failures cannot change analysis. Active
`RETRIEVAL_BACKEND=lexical` is explicit, curated-card-only and fails without fallback.
It imports no request-supplied access grants; ranking text is bounded at 20,000
characters while model input remains intact. No registered-document migration.

Opt-in JSON envelopes distinguish application provenance/scope from untrusted
content. Metadata includes evidence/source ID, title/family/type, authority, policy
scope, version/currentness/dates and applicability, excluding ranking diagnostics.
Only supplied evidence IDs can be cited. Application-owned source titles/families
and deterministic provenance text prevent source-reference authority upgrades.
Policy scope/currentness are not a claim of universal legal applicability.
SOC repair/output enforcement and governance's existing validation remain unchanged.

V2: **96 records, 40 cases, 10 no-answer, 12 multi-chunk**. Frozen before results.
Positive Recall@5: keyword .8222, lexical .9111, dense 1.0000, hybrid .9667.
Required-group recall: .6250 / .8333 / 1.0000 / .9583. All eight violation counters
are zero for every candidate. Every candidate falsely retrieves on **10/10** negative
queries. Dense has complete positive coverage; hybrid has strongest MRR/NDCG but
misses one requirement group. These are separate findings, not one migration score.

Fresh query median ms: .212 / 1.542 / 28.339 / 25.859; warm .203 / 1.531 / 1.322 /
2.776. First embedding/client readiness: dense 3,451.188 ms, hybrid 82.938 ms;
remaining document prep 817.640 / 709.358 ms. Independent provider/query caches were
used, but shared model/OS residency was uncontrolled; no forced unloaded-model cold
run. Full timing inclusions and p95 values are in the V2 report. Exact offline replay
passes for every ranking/score/metric/violation. No default migration is justified.

## Microsoft stress

See [harness contract](30_microsoft_stress_harness.md). Eight SOC plus six AI risk
cases cover the Microsoft ecosystem without live vendor integration. All 14 pass
no-model preflight; deterministic checks cover exact canonical evidence, source
discipline, canary absence, critical-token membership and nonempty observations.
Protocol/support/false-positive/containment quality remain manual semantic review.
Selected live results and triage are recorded separately; single trials do not
establish reliability or authorize outcome-driven hardening.

[Selected live baseline and manual review](microsoft_stress/manual_triage.md):
three SOC and one FAQ case, one unseeded trial each, clean implementation `0f90fd5`,
local qwen3:8b `500a1f067a9f`, temperature .1, legacy retrieval. Three returned
analyses pass narrow deterministic checks; one port-443 trial failed closed after
one repair. Injection/source/agency boundaries held in the injection trial. The SOC
positive control recognized suspicion/high severity but omitted shadow-copy deletion
and suggested unsupported credential access. FAQ invented sensitivity/employment
impact. These are manual findings, not a replacement reliability score.
No rejected-generation stages were saved, so the port error's root cause is unknown.
No post-result production changes or repeated live trials were performed.

## Verification and preservation

Starting tests: **1,440 passed**. Implementation gate at `0f90fd5`: **1,500 passed**,
Ruff, `git diff --check HEAD`, and `pip check` (no broken requirements). One existing
Starlette/httpx deprecation warning remains. No new dependency was added to silence it.
Targeted tests preceded the checkpoints. A separate clean local Windows clone at that
source commit reused the repository's explicit Python environment and also passed
**1,500 tests**, Ruff and diff checks with a clean worktree. This is a clean source
checkout replay using the already-tested environment, not a fresh dependency install.
It verifies fixture hashes/provenance, JSON/CSV CRLF parsing and all Windows/PowerShell
demo preservation tests. Hosted Ubuntu skips only the existing 11 Windows executions.

After adding the selected-live artifact identity/check replay, final local gate:
**1,501 passed** (61 added), Ruff and diff check passed. The baseline/provenance and
all exact case requests are checked without another model generation.

Hosted implementation CI passed at `0f90fd543614e68609f6aedfc0e9d9440e9c368c`:
[CI run](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40822910757).
The results checkpoint `9c903a9` also passed
[hosted CI](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40824123186).
Final hosted CI is verified on the exact final handoff SHA after the final push.

Read-only remote verification confirms main/release/tag preservation. No diff from
the foundation exists in frozen output evaluations, V1 retrieval, reference packs,
prompts, SOC output policy/observable enforcement, public schemas/routes, registry,
Ollama configuration, dependency manifests, root attributes or demo scripts. The demo
still tracks remote main and explicitly selects legacy. No live demo restart was
needed; its Windows execution tests pass. No default analyzer behavior changes
without new config, apart from the requested additional UI input-profile selector.

Files added/changed are grouped under `app/soc_inputs.py`, `app/retrieval/`, the two
analyzer hooks, `dashboard/microsoft_input.py` and its loader/workspace hooks,
`sample_data/microsoft/`, new `evals/retrieval_v2/` and `evals/microsoft_stress/`,
associated tests, docs 27–31, new experiment artifacts and the narrow source-identity
preservation manifest/test adjustments. Frozen artifact hashes were not rewritten.

## Limitations and next decision

This is bounded local ingestion, not a Microsoft connector. Projection omissions,
unknown fields and ambiguous identity/correlation still need analyst judgment.
Correlations use exact AlertId links; richer time-qualified process/entity linking
is not automatic. The model can still miss semantic facts, infer unsupported scope,
or fail closed. JSON-shaped telemetry does not extend the frozen endpoint recognizer
to every vendor field pair. An IP/port pair repeated in a different textual form can
therefore trigger repair/rejection despite being visible to a human in the raw rows.
Accepted bundle size also does not guarantee that every row fits the configured
model context; no token budgeting or context-size change was introduced.
Evidence-preservation is stronger than universal semantic
entailment. Optional lexical consumes curated cards only; ACL metadata is not an
authenticated authorization service. No retrieval abstention/answer-support gate,
true unloaded cold-start experiment, enterprise scale test or repeated Microsoft
stability measurement was implemented.

Highest-value next sprint: separately authorize bounded Microsoft evidence/output
compatibility diagnostics, beginning with machine-only rejection-stage capture in
a new stress experiment and investigation of the failed port case. Establish its
cause before a fix. Test fresh support-scope/positive-control hypotheses suggested
by the missed destructive activity and invented FAQ rationale. A predeclared
retrieval abstention/answer-support experiment on **new** no-answer queries should
report false-retrieval versus missed-support tradeoffs. Keep default legacy and
frozen comparisons intact; do not tune against scorer wording or this suite.
No new workflow, V3.3, cloud integration or default migration is implied.

Recommended implementation assistant: **GPT-6.1 Sol, high reasoning effort** for
the bounded code/experiment work. This is engineering judgment informed by
[official model-selection guidance](https://developers.openai.com/api/docs/guides/model-selection)
and [reasoning-effort guidance](https://developers.openai.com/api/docs/guides/deployment-checklist).
It does not change the application's local qwen model.

| Maturity | Assessment |
| --- | --- |
| Microsoft foundation complete | Yes |
| Microsoft product-integrated | Yes |
| Retrieval shadow-integrated | Yes |
| Lexical opt-in ready | Yes, curated cards / both active workflows |
| Retrieval V2 complete | Yes; true unloaded cold timing remains a stated limitation |
| Microsoft stress baseline complete | Yes: 14 preflights, 4 selected live trials with separate manual triage |
| Default-migration ready | **No** |
