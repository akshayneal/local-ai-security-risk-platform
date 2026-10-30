# Expansion Sprint 4: evidence support and analyst workbench

Sprint 4 delivers a frozen support/relevance experiment, a conservative reusable
support contract, and an Evidence Inspector in both existing workflows. It does
not establish general semantic verification or a reduced generated unsupported-claim
rate. Legacy retrieval and local qwen3:8b remain the defaults. No merge, tag or release.

## Mini-Sprint 3.5 recovery and closure

The original treatment completed all eight scheduled cases. Journal/report identity,
request hashes, treatment source identity, manual quotations and unchanged paired
rubric were verified. No existing trial or judgment was discarded or rerun. Both
phases returned 8/8, with 16 actual model requests total, zero repairs and no hidden
availability loss. The immutable mini-sprint branch is
`feature/evidence-grounding-stabilization` at
`47f038602b03b38854dfe82024941f2d4204ca76`.
[Exact-SHA hosted CI passed](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40975409627).
Local Windows validation passed 1668 tests, uncached Ruff, pip check and diff check.

The paired review records unsupported factual claims present in 5/8 untreated and
3/8 treatment returns, with ambiguity increasing from 3/8 to 4/8. Unsupported authority
present increased from 0/8 to 1/8; source applicability concerns were 3 present and
1 ambiguous in each phase. Positive-control loss changed from 0 present/1 ambiguous
to 0/0. Incorrect classification among five SOC returns changed from 2 present/1
ambiguous to 2/2. Median latency rose from 94.249 to 117.012 seconds. These overlapping
manual dimensions are not a score or statistical reliability estimate.

The treatment isolates Microsoft table evidence from adapter/routing-ID query noise
and makes legacy governance source relevance application-owned guidance provenance.
It does not solve body-level semantics: lone-connection C2, training-note Initial
Access, missing supplied command-line details, mandatory logging without a mandate,
and a quarterly charter described as satisfied without implementation evidence remain
in the archived treatment. See [the full mini-sprint report](37_evidence_grounding_stabilization.md).
The Sprint 4 child branch was created only after that closure and successful CI.

## Engineering and trust boundaries

Work is on `feature/evidence-support-workbench`. Checkpoints:

| Commit | Reviewable work |
| --- | --- |
| abd9ab214e24bccd9f052bfd75dffe87afbdca16 | Freeze corpus, gold, methods, runner and preservation plan |
| 1d123a7db13c12089fb13a9ca55dc164ca8b767b | Shared support contracts/assessor and exact ranking/vector artifacts |
| 63a779c | Offline assessment and four-backend replay |
| 2707a620d8c7f179462b2754f84d9a9d567e347d | Both workflows, API metadata, Evidence Inspector, exports and tests |
| 379853ee6040039627823ac357d7120e8390cca9 | Freeze eight fresh live diagnostic cases before outputs |
| 75d5e2052ac12c06c8a8fcb4e3cc97ab56d0f46a | Isolated policy-review design contracts and fixtures |
| 91fb65cbd6337ca2243f5beb0e2b88a646d8f238 | Complete live artifacts/review and post-run API routing-ID correction |

The exact final handoff SHA and its hosted CI are supplied in the handoff; a document
cannot contain its own final commit identity. Artifact manifests separately bind
the actual experiment launch and candidate implementation, rather than substituting
the eventual documentation commit for the code that generated results.

The [support architecture](39_support_and_authority_architecture.md) separates eligible
candidates, structured record matches, model proposals and analyst judgments. It
uses the existing authority classes and pre-ranking workflow/access/policy/date/version
filters. Document records require an explicit trusted registry gate. User/model text
cannot grant access or policy authority. No registry migration is introduced.

Exact subject/predicate/kind/typed-value assertions can establish what a reviewed
eligible record says. Operational guidance cannot establish an incident; organizational
requirements require matching scope; requirements cannot establish implementation.
Conflicts and partial support are explicit. Model/manual judgments cannot carry
deterministic record-verification status. Every result still requires human review;
there is no confidence percentage, universal entailment parser or second model call.

The structured matcher remains a reusable bounded library, not an automatic scorer
of free-form production responses. Active workflows use the same contract with
model-proposed, unassessed, not-verified claims and explicit analyst review. This
limited activation follows the measured false-abstention cost and unresolved body
semantics. It improves inspectability without claiming to fix those semantics.

## Frozen held-out support experiment

[Benchmark details](38_evidence_support_benchmark.md) and
[provenance](evidence_support_v1/assessment_provenance.json) preserve 43 fresh cases,
55 records and 14 categories, frozen before outcomes. Gold was authored by the
implementation assistant; it is separate from candidate inputs, not independent
human/expert adjudication. There are 18 full-support, 14 related-but-insufficient,
5 no-eligible, 3 partial and 3 conflicting cases. Three of the 14 related cases have
empty relevant sets; total no-answer is 19, and non-full-support is 25.

All four existing rankers ran K=5 and existing eligibility once: 172 case/backend
rows, 58 existing local embeddinggemma:300m requests, zero qwen generations. No new
backend, model download, threshold fit or default migration. Exact vectors permit
offline replay; candidate modules were committed before assessment.

| Measure | Legacy | Lexical | Dense | Hybrid |
| --- | ---: | ---: | ---: | ---: |
| Mean relevant Recall@5, 35 nonempty gold sets | 1.0 | 1.0 | 1.0 | 1.0 |
| Full-support sufficient evidence@5 | 18/18 | 18/18 | 18/18 | 18/18 |
| Required-group recall, 24 cases | 1.0 | 1.0 | 1.0 | 1.0 |
| False full support | 0/25 | 0/25 | 0/25 | 0/25 |
| Correct no-answer | 19/19 | 19/19 | 19/19 | 19/19 |
| False abstention / positive loss | 1/18 | 1/18 | 1/18 | 1/18 |
| Partial / conflict handled | 3/3; 3/3 | 3/3; 3/3 | 3/3; 3/3 | 3/3; 3/3 |
| Eligibility / wrong-authority support violations | 0; 0 | 0; 0 | 0; 0 | 0; 0 |
| Median ranking ms | 0.290 | 1.291 | 24.666 | 2.264 |
| Median assessment ms | 0.098 | 0.097 | 0.101 | 0.101 |

Scope/version/access/date violations are covered by the eligibility gate and exact
replay tests. Never-eligible restricted, wrong-unit, superseded and date-decoy records
are absent even from the embedding cache. The natural-prose Juniper policy positive
is retrieved but lost by the structured matcher: 5.6% false abstention among these
18 positives. The parser and gold were not tuned after that result.

All rankers reach a ceiling on this explicit synthetic corpus, so no ranking winner
or production migration is justified. Cached embeddings and backend order confound
latency; hybrid's median is not evidence of a causal speed advantage. A separately
named any-hit diagnostic has 18/25 false support for legacy/lexical and 20/25 for
dense/hybrid. That heuristic is not current production behavior or a hallucination
measurement. Zero structured false support does not mean zero unsupported model prose.

## Product integration and compatibility

The [Inspector guide](40_analyst_evidence_inspector.md) describes the delivered UI:
actual retrieved and cited sources; trusted authority, eligibility, scope and version
provenance; bounded plain-text excerpts; Microsoft table/row/field inventory; generic
SOC/governance field inventory; model claim/gap review; and case-bound analyst judgments.
An explicit off-by-default selected-value viewer displays only one submitted field,
bound by the request fingerprint. It reports truncation and does not automatically
add those values to Inspector exports. No telemetry is silently omitted from the
underlying model context.

Request-local ContextVar capture observes the original retrieval selection. Unknown,
forbidden, altered legacy cards and ungated document records do not acquire Inspector
provenance. Capture errors become unavailable rather than inferred from citations.
The existing public analysis schemas remain unchanged; optional typed Inspector
metadata is additive only in `/ui/analyze/*` envelopes. Legacy envelopes and exports
without that metadata retain their old shape. Generic and Microsoft SOC share the
same integration; no vendor-specific support fork is added.

Governance controls are labeled model proposals/stated requirements requiring
applicability review. Guidance is not binding policy; a binding requirement is not
proof of satisfaction. SOC validators, complete-context handling, exact critical
observable checks, full post-repair validation and one-repair limit remain intact.
Governance validation remains narrower and is not advertised as SOC-equivalent.

Analyst review is session-local, tied to result/claim/eligible evidence IDs and
exportable with explicit analyst-recorded/not-verified provenance. No authenticated
approval, persistent review database or backend audit certification is implied.
JSON/Markdown exports add a versioned provenance block when available, without
automatically including original input payloads/values, source excerpts, prompts,
rejected generations or diagnostics. The existing analysis can quote telemetry and
explicit analyst notes can contain sensitive text; exports are not redacted reports.
Notes are escaped. Successful analyses are still audited once; inspection adds no
model generation or automatic action. Stale cases/results clear review/export state.

AppTest, TestClient and deterministic unit tests cover both workflows, all three UI
input paths, retrieved/cited differences, metadata trust, private-value opt-in, empty
rows, stale state, manual judgment validation, exports and diagnostic exclusion.
No browser or graphical application was opened. **USER VISUAL QA PENDING**: layout,
narrow screens, themes, long content, uploads, privacy controls and downloaded exports.

## Eight fresh end-to-end diagnostics

The [frozen suite/rubric](../evals/evidence_support_e2e/rubric.md) combines all requested
controls into eight new cases. It ran once through the actual UI route functions,
original analyzers and actual retrieval capture, with audit persistence replaced by
a counting sink. It is a candidate-only passive-inspection diagnostic: no baseline
generation comparison or unsupported-claim improvement is claimed. No historical
32-versus-32 campaign, selective rerun or extra model-based support judge was run.

[Exact results](evidence_support_e2e/results.json),
[review quotations](evidence_support_e2e/manual_review.json),
[separate measures](evidence_support_e2e/summary.json) and
[provenance](evidence_support_e2e/provenance.json) preserve every output and request
hash. Launch was clean `379853ee6040039627823ac357d7120e8390cca9`; app/dashboard
files remained unchanged until all eight finished. Runtime: Python 3.13.1, Ollama
0.40.13, qwen3:8b short CLI digest `500a1f067a9f`, temperature 0.1, no configured seed,
legacy retrieval without shadow. Microsoft context remained 8192; governance retained
its existing unset context option. Prompt retention is not independently proven by
token counters. Provenance records the digest as a short ID, not a full checksum.

All **8/8 returned**, zero withheld/errors, **8 actual model requests**, zero repairs
or transport retry requests. Each response had one counted successful audit outcome,
actual cited-source membership, captured retrieval and model-proposed/unassessed/
not-verified claims. Canonical routing ID passed **7/8**: ESE-NOTE returned VENDOR-110.
These metadata checks do not establish factual truth. Median end-to-end latency was
**103.001 s**, range **82.447–132.504 s**; no controlled latency comparison is made.

| Assistant-reviewed dimension | Present | Ambiguous | Absent |
| --- | ---: | ---: | ---: |
| Unsupported factual/inference claim | 4 | 1 | 3 |
| Unsupported authority claim | 0 | 2 | 6 |
| Positive-control information lost | 0 | 1 | 7 |
| Source applicability concern | 3 | 0 | 5 |
| Benign/uncertain false-positive concern | 2 | 3 | 3 |

Dimensions overlap, and every quote is hash-bound to the response. They are not a
composite score, statistical confidence, causal treatment comparison or independent
human adjudication. Eight returns also do not measure general false abstention.

| Case | Observed result and remaining concern |
| --- | --- |
| ESE-NET | Exact TCP endpoints preserved without invented login; unsupported C2 mapping/inference from a lone connection remains. Weak process-guidance fit. |
| ESE-AUTH | Failed operator events and different-account success/CA status retained in observations; summary and containment ambiguously join the success to the operator. Moderate-confidence identity interpretation concern. |
| ESE-NOTE | WMIC enumeration retained; no deletion-executed claim. Unsupported vendor-led potential Credential Access, wrong routing ID and authentication-guidance fit remain. The quoted nonexecution detail is omitted, so positive coverage is ambiguous. |
| ESE-DUMP | Exact LSASS MiniDump command/hash, named lab approval and unknown completion retained; no successful theft asserted. Broad Execution mapping, weak PowerShell guidance and possibly disproportionate conditional isolation remain. |
| ESE-HIRING | High employment impact, scoped quarterly bias review/approval and missing implementation retained. Missing specific frequencies is an ambiguous consistency concern despite the known quarterly cadence. |
| ESE-PUBLIC | Public/local low impact, seven-day retention and staff verification retained. Says the system adheres and maintains logs although configuration is not implementation evidence. Additional required-control wording has ambiguous authority. |
| ESE-ALLEGATION | Directive stays unverified and applicability requires checking; no daily-audit mandate or verified compliance. Regulatory wording and generic required logging leave authority/proportionality ambiguity. |
| ESE-CONFLICT | FAQ/payroll design conflict and potential material impact remain unresolved; no verified approval, deployment or wrong-unit binding-policy claim. |

The genuine authentication, dump, high-impact hiring and low-impact public positives
remain usable. This does not erase the summary event-joining issue or implementation
overstatement. The workbench makes claims inspectable and records review status; it
does not automatically abstain from these analyses or repair their semantic content.

Only after the completed run was archived, commit `91fb65c` binds the validated SOC
API response routing `alert_id` to `request.alert_id`. Both public/UI endpoints share
the correction, after full original analyzer validation and before audit/return.
Two deterministic real-analyzer tests exercise a vendor ID with one generation and
one audit, proving all other fields unchanged. No model call, parser, repair expansion
or new semantic fail-closed rule was introduced. The archived 7/8 identity result is
not rewritten, and there is no post-fix live rerun. Direct analyzer behavior and
historical artifacts remain unchanged; the fix does not validate identifiers in prose.

## Conditional SOC Policy & Governance Review

**Design only; no runnable prototype or application activation.** The scoped structured
fixture tests validate unit/access separation and requirement-versus-approval status.
They do not validate general policy-prose/action applicability. The lost prose
positive and current model overclaims leave that gate partial. A third UI workflow
would not resolve the gap. No endpoint, navigation entry or feature flag was added.

[Design contracts and fixtures](41_soc_policy_review_preview.md) are isolated under
`evals/soc_policy_design/` and documentation. Two fictional units have distinct
approval/retention policies. Draft requests accept no grants; proposal approval is
fixed to not-granted-or-verified. Wider testing of a policy reasoner requires a
separately authorized full vertical slice, trusted policy admission and frozen
prose/action applicability evaluations. It is not release-ready.

## Preservation and next work

The Sprint 4 manifest binds 261 existing protected paths and the prior blobs of six
explicitly authorized integration files. Historical manifests and official V1/V2/
V3/V3.1/V3.2, retrieval, Microsoft stress/reliability and mini-sprint identities remain
unchanged. Preservation tests resolve the original source blobs for authorized
plumbing changes; they do not weaken historical scorers or rewrite archived outcomes.
The new benchmark corpus/gold/scorer and candidate modules are separately hash-bound.

Main/origin main and peeled v2.3.0 remain
`fde00d0ca5d21eecbc6973cc784550ed453edb7a`; the annotated tag object remains
`22e5e1704940c41284d6b29e393fd51958f3ba34`. No external AI/cloud embeddings, dependency,
connector, autonomous containment, credentials, OS change, desktop/browser/headless
automation, screenshot or unrelated process action was introduced. No merge/tag/release.

## Validation and checkout compatibility

Final implementation checkpoint `91fb65cbd6337ca2243f5beb0e2b88a646d8f238`:

- Repository Windows run: **1721 passed**, one existing Starlette/httpx deprecation
  warning, 67.58 seconds. Uncached Ruff, pip check and diff check passed.
- Separate clean detached Windows worktree at the same SHA: **1721 passed**, the
  same warning, 72.77 seconds; uncached Ruff and diff check passed. It used the existing
  repository virtual environment by absolute path, without installing dependencies.
  Clean Git status was verified before and after tests. Ordinary non-forced worktree
  cleanup was attempted after checking its exact project-local path and clean status;
  Windows denied deletion of parts of the temporary tree and Git metadata directory.
  Automatic approval review then blocked recursive PowerShell cleanup with "blocked
  by policy". No alternative deletion or privilege escalation was attempted.
  Remnants are left at `evals/results/s4check/` (visible as untracked) and
  `.git/worktrees/s4check/`; the main worktree remains registered and intact. These
  are generated validation-copy remnants, not uncommitted application changes.
- [Exact implementation-SHA hosted CI](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40981739325):
  **1710 passed, 11 Windows-specific skipped**, tests and Ruff successful. The CI
  uses a fresh Linux checkout/virtual environment and the unchanged dependency file.
- Twenty-three focused API/artifact/preservation checks passed after the post-run
  routing correction. Benchmark cached replay, fresh live artifact replay, quote
  integrity and all historical preservation tests are included in the full run.

The final documentation-only closeout is pushed after this evidence. Its exact
final SHA and hosted CI result are verified separately in the handoff. No application,
test or frozen artifact change follows the full implementation validation.

Earlier UI integration testing caught five AppTest failures in the opt-in value
viewer (an unset selection); the guard and empty-row regression test were added before
the passing 1710-test integration checkpoint. That failed intermediate run is not
reported as a pass. No outstanding automated failure is concealed by the final gate.

## Maturity assessment

| Question | Assessment |
| --- | --- |
| Mini-Sprint 3.5 closed? | Yes; eight treatment trials, immutable branch, integrity checks and exact-SHA CI. |
| Retrieval-query contamination corrected? | Tested adapter/routing-ID contamination corrected; contextual notes and misleading vendor vocabulary can still affect relevance. No universal negation claim. |
| Evidence support benchmark complete? | Yes, 43 frozen cases, four rankers, exact cached replay and provenance. Synthetic/assistant-authored limitations apply. |
| Relevant but insufficient distinguished? | Yes for bounded exact assertion assessment; free-form production claims remain explicitly unassessed. |
| No-answer behavior measured? | Yes, 19/19 structured cases per ranker. Not general generative abstention. |
| False-abstention tradeoff measured? | Yes, one valid prose positive lost out of 18, for every ranker. |
| Authority and applicability enforced? | Existing metadata eligibility and exact scoped record matching enforced; general policy-prose/action applicability and body-level authority remain partial. |
| Model-proposed support distinguished from verified? | Yes; unassessed/not-verified status, explicit provenance, mandatory review and no confidence score. |
| Evidence Inspector delivered? | Yes, functional provenance/input/claim/analyst-review UI with safe exports and automated QA. Visual QA pending. |
| Active workflows integrated? | Yes; generic/Microsoft SOC and AI System Risk Review, additive UI envelopes and compatible public schemas. |
| Unsupported claim rate improved on held-out cases? | Not demonstrated. No matched generative treatment comparison; current diagnostic still finds defects. |
| Microsoft input ready for release? | No; routing metadata is corrected after the diagnostic, while semantic gaps, review and user visual QA remain. |
| SOC Policy Review prototype implemented? | No; isolated design contracts/fixtures/docs only, as the applicability gate remains partial. |
| SOC Policy Review safe for wider testing? | Design tests only. No runnable reasoning workflow is available or approved for wider testing. |
| Default retrieval migration justified? | No; all four rankers reach a synthetic ceiling and latency is cache/order-confounded. Legacy stays default. |
| Main ready for a new release? | No release recommendation from these results. Branch review, independent semantic review and visual QA remain. Main/tag unchanged. |

## Next priority

The highest-value next sprint is evidence-linked analyst correction and a separately
frozen natural-prose support/applicability evaluation, with reviewed source admission,
human adjudication, positive controls and explicit lost-obligation measurements.
Use the current Inspector to locate evidence for body-level incident/implementation
claims before considering additional prompt or automatic support enforcement. Keep
the policy workflow gated, legacy default unchanged and Microsoft release blocked
on semantic review and user visual QA. Recommendations are not authorization.

## Exact files changed from the closed mini-sprint

The following list is the Sprint 4 diff from `47f0386`; the mini-sprint owns its
separate file list in report 37. No requirements, original reference cards, prompts,
analyzers or original response schemas were changed by Sprint 4.

```text
Documentation/38_evidence_support_benchmark.md
Documentation/39_support_and_authority_architecture.md
Documentation/40_analyst_evidence_inspector.md
Documentation/41_soc_policy_review_preview.md
Documentation/42_expansion_sprint_4_report.md
Documentation/evidence_support_e2e/.gitattributes
Documentation/evidence_support_e2e/manual_review.json
Documentation/evidence_support_e2e/provenance.json
Documentation/evidence_support_e2e/results.json
Documentation/evidence_support_e2e/summary.json
Documentation/evidence_support_v1/.gitattributes
Documentation/evidence_support_v1/assessed.json
Documentation/evidence_support_v1/assessment_provenance.json
Documentation/evidence_support_v1/ranking_provenance.json
Documentation/evidence_support_v1/rankings.json
Documentation/evidence_support_v1/vectors.json
Documentation/expansion_sprint_4_preservation.json
Documentation/policy_review_design/scenarios.json
app/evidence_inspector.py
app/main.py
app/retrieval/orchestration.py
app/support_assessor.py
app/support_contracts.py
app/ui_schemas.py
dashboard/evidence_inspector.py
dashboard/exports.py
dashboard/microsoft_input.py
dashboard/workflows.py
evals/evidence_support_e2e/.gitattributes
evals/evidence_support_e2e/__init__.py
evals/evidence_support_e2e/cases.json
evals/evidence_support_e2e/freeze.json
evals/evidence_support_e2e/plan.json
evals/evidence_support_e2e/rubric.md
evals/evidence_support_e2e/runner.py
evals/evidence_support_v1/.gitattributes
evals/evidence_support_v1/__init__.py
evals/evidence_support_v1/build_suite.py
evals/evidence_support_v1/cases.json
evals/evidence_support_v1/corpus.json
evals/evidence_support_v1/freeze.json
evals/evidence_support_v1/methodology.md
evals/evidence_support_v1/plan.json
evals/evidence_support_v1/registry_current.json
evals/evidence_support_v1/runner.py
evals/soc_policy_design/__init__.py
evals/soc_policy_design/contracts.py
tests/historical_identity.py
tests/test_evidence_inspector.py
tests/test_evidence_inspector_ui.py
tests/test_evidence_support_suite.py
tests/test_grounding_preservation.py
tests/test_policy_review_design.py
tests/test_retrieval_artifacts.py
tests/test_sprint3_preservation.py
tests/test_sprint4_preservation.py
tests/test_support_assessor.py
tests/test_support_benchmark_artifacts.py
tests/test_support_e2e_artifacts.py
tests/test_support_e2e_plan.py
tests/test_ui_api.py
```
