# Sprint 13 prospective adaptive reasoning plan

Status: experimental, internal, off by default. RELEASE NO-GO. Authored semantic
review only; independent review and user visual QA remain PENDING.

Starting local/origin Sprint 12 SHA: `95fdfbe1d5f5cacf0d814e7c3a67bb56ce18f57a`.
Feature branch: `feature/adaptive-typed-security-reasoning-sprint13`.
Prior Sprint 12 closure and exact-commit CI are prior evidence, not a new run.
No released workflow, retrieval default, launcher, dependency, or service changes.

## Question and evidence

Can a strict typed projection remove observed/authorized role substitution,
timing reversals and unknown/absent confusion for a narrow declared relationship,
while preserving counterevidence and keeping source authenticity unresolved?
The historical failure map is forensic evidence only. Historical cases/gold are
not new qualification cases or a source for new holdout answer tuning.

## Hypothesis cards recorded before implementation or generation

**H1: explicit premise roles plus application comparisons remove relationship
substitution.** Historical prompts contained decisive values, yet the model
substituted permitted operations for unknown observations and missed timing
contrasts. Rival causes: ambiguous risk labels, compound JSON strings, sampling
and prompt burden. Compare M (model-owned relationship on identical typed input),
D (Python comparison) and H (same D plus separately unverified model questions).
Freeze literal development inputs and authored outcomes before generation.
Single-premise counterfactuals change operation, principal, endpoint, time, gate
timing and implementation state; irrelevant labels must not change the result.
Reject the general claim if a supported unambiguous predicate fails; restrict
coverage rather than fill unknowns. Cost: zero model sends for D, one for M/H.

**H2: typed unknown/conflict and capability prerequisites prevent false certainty.**
Missing verification was used as a specific concern; known read/gate/failed
counterevidence was omitted. Rival: authored rubric favors a different risk
threshold. Separate logical mismatch from risk and source verification. Test
nulls, explicitly absent/proposed/implemented, duplicate keys, stale versions,
counterclaims and disconnected/read-only tools. Missing decisive premises must
produce underdetermined or projection unavailable, never a proven absence;
decisive contradictory assertions must remain conflicting. Falsifier: any
unsupported alignment/mismatch or suppression of decisive counterevidence.
Cost: deterministic matrix first; fresh model cases only for probabilistic claims.

**H3: schema/ID validity cannot certify arbitrary generated explanation.** Historical
valid outputs included wrong mechanisms and irrelevant pointers. Rival: giving
the computed relationship will yield consistently useful, noncontradictory
questions. Compare M and H on equivalent evidence/runtime; H receives D's
comparison and may only suggest bounded questions/conditional human verification.
No model text enters authoritative fields. Test valid-ID hostile prose and
tampered report/export: withhold commentary or visibly mark it unverified;
canonical result and source status must remain identical. Promote model assistance
only under the prospective 22/24 useful/zero material fabrication gate; otherwise
select D if supported and retain model failures as evidence. Cost: paired sends,
not repairs. A valid question is not proof of analyst usefulness.

## Evaluation protocol and budgets

Adaptive development and locked holdout live in separate packages. Fresh holdout:
24 opaque cases, eight per pillar, positive/legitimate/unknown/conflicting,
counterfactual pairs, diverse synthetic identities/surfaces. Literal inputs,
authored rubric, forbidden claims, masked scoring form and execution settings
are frozen/committed before the first development generation. Holdout inputs
and gold are never imported/read by the development runner. Author judgments
are not independent adjudication. A separately held key accompanies a shuffled
reviewer packet with no expected answer or generator/arm linkage.

Hard caps: development 84 raw sends; diagnostic 24 raw sends; total 108.
Sequential foreground loopback-only qwen3:8b with exact installed digest,
think=false, temperature 0.1, num_ctx=32768, num_predict=4096,
truncate=false, shift=false. No seed guarantee, retries, repair or fallback.
Per-send 600 s wall/10 s connect/120 s idle; campaign 14,400 s elapsed;
1 MB raw response, bounded retained artifacts. Strict context byte upper bound
includes schema and generation allowance. Read-only preflight before every
development batch; provider/model drift, inherited active evaluation, pending
or UNKNOWN Sprint 13 sends stop generation. Old UNKNOWNs remain unchanged.
Each raw send has fsynced track and global reservation before dispatch.

Initial allocation: twelve paired M/H cases (24 development sends), then matched
repeat/counterfactual/cluster experiments only when they discriminate a cause.
Reallocate prospectively with append-only decisions; ceilings are not targets.
If D wins, run holdout offline once (zero holdout model sends). Select and commit
the candidate before opening the holdout; no post-holdout semantic tuning.

Report separately: typed predicate results, report/export integrity, authored
mechanism usefulness, concern false positives/negatives, unknown/conflict handling,
counterevidence, unsupported high-impact claims, withheld/UNKNOWN outcomes,
latency/tokens/bytes and supported coverage. Repeats are not independent cases.
Original gate: 24/24 correct typed relationships at their declared supported scope;
model assistance 22/24 useful plus zero material fabricated permission/actions,
control reversals or disruption advice and no systematically failing pillar.
These are engineering gates, not population accuracy or safety certification.

## Trust and qualification boundaries

Only reviewed synthetic schema/context is eligible. Source references, revisions,
classification and scope are application metadata; body text cannot grant them.
All values remain supplied/unverified assertions, including reviewed typed
requirements. Comparisons do not authenticate permission, verify deployment,
establish severity/exploitation, approve anything or execute an action.
Unsupported layouts/multiple events must be explicit, not silently discarded.
Exact original string, nested pointers and snapshot hashes bind reports/exports;
hashes identify bytes, not trust. No private sources or original journals change.

## Verification and decision

Focused deterministic tests, metamorphic/adversarial counterexamples, original
guard replay and negative mutation proof precede model use. At stabilization run
full Windows pytest, Ruff, pip check, diff check, baseline hashes and active scope
guard. Normal additive commits and authorized non-force feature push, followed
by exact-final-SHA Actions verification. No merge, PR, tag or release.
Further protocol additions and decisions are append-only in the study directory.
