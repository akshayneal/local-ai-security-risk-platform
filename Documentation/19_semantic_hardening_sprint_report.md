# Semantic production-hardening sprint report

## Starting state and authorized work

Clean synchronized `feature/portfolio-hardening` at
`c72b52c30c79acabb2b3ad08482010efe3f534be`. Starting pytest: **993 passed**, one
existing Starlette/httpx warning, **27.76 seconds**. Ruff and whitespace passed.
V1/V2/V3/V3.1/V3.2 evidence and historical check meanings remain frozen.
Baseline V3.2 is 32/42 (76.2%), no errors, 8/2/4 stable-pass/stable-fail/mixed,
and 9/15 positive-control trials. Its review identified actor/legal omissions,
post-repair proposed-step IP corruption and unsupported SSH, plus frozen lexical
scorer imperfections. Those imperfections are not production tuning targets.

## Implementation

- `app/observables.py`: exact membership across critical kinds, malformed/near
  IP and SHA recognition, explicit endpoint-pair and labeled-role validation.
- `app/output_policy.py`: ten-field identity/endpoint coverage and a single
  `validate_soc_output` combining observation requirements and complete schema.
- `app/soc_analyzer.py`: shared `_validate_generation` processing/postconditions
  for both generations, full generic repair instructions, explicit trace
  acceptance/rejection/failure. Still one initial plus at most one repair.
- `app/prompts.py`: supported-case/internal requirement retention, named identity/
  authority/cadence completeness, external-scope separation, continued caution
  for unverified claims, and protocol non-inference.
- `evals/semantic_treatment_compare.py`: new comparison-only utility, never an
  alternate scorer. It refuses incompatible suite/scorer/model/trial metadata.

No schema, backend route, UI, registry, retrieval, reference pack, model/client
retry configuration, dependency or audit behavior change. No runtime judge,
external AI, autonomous actions, real legal/threat intelligence or broad symbolic
reasoning. The [technical document](18_semantic_production_hardening.md) defines
deterministic boundaries versus prompt-only semantic properties.

Historical artifact tests formerly pinned live production to baseline source
bytes, incompatible with any authorized treatment. Six associated tests now use
`tests/historical_identity.py` to verify the original source/test identities at
the starting commit for explicitly authorized changed paths; suites/scorers and
artifacts remain current-file checked. The CI checkout adds fetch-depth 0 so
historical objects are available without network calls from pytest or skipped
checks. All historical reports still replay their original results. This is
source-preservation bookkeeping, not changing scoring or historical evidence.

## Deterministic testing and pre-live expectations

The new production tests cover every protected field and identity kind; malformed
IP/hash shapes and extended SHA; exact/invented CVEs; endpoint mutation and roles;
generic hours/days/count/PID/standard-port advice; initial acceptance; repair from
observation, investigation, endpoint and schema failures; a different failure in
the repaired response; malformed source shapes; no third generation; source
metadata restoration on repair; prompt positive/negative scope symmetry; and
explicit/unknown protocol guidance. No model is needed by pytest. Prompt tests
check instructions/data preservation, not proof of how a live model will reason.
Existing injection, source, agency, API-error and historical evaluation tests run
unchanged in meaning; the trace-order assertion gains contract_accepted.

Initial targeted gate: 296 passed across new production and existing I/O tests.
The first run exposed only the expected trace-order assertion needing the newly
authorized acceptance stage; that assertion was updated. Historical source-test
adaptation was designed before the full gate, rather than weakening failed
historical scores. Further tests cover malformed processing on either generation
and comparison errors/compatibility. All changes precede official inference.

The nine [pre-specified expectations](evaluation_v3_2/treatment_expectations_pre_live.json)
are frozen before live inference. H1/H2 target substantial actor/legal positive
improvement; H3/H4 target deterministic identity and complete repair; H5/H6 target
protocol and negative-control grounding; H7 protects existing security controls;
H8 measures expected availability/latency cost; H9 governs closeout. Actuals are
recorded only after the complete report exists, without a replacement percentage.

## Evaluation checkpoint and reproduction

Production is committed/pushed before the official run and then immutable for the
experiment. The exact V3.2 suite/scorer remains unchanged. No selective reruns or
post-live behavior changes. The preservation inventory covers 107 frozen paths.
Both frozen suite hashes are required and listed in the technical document.

Use repository `.venv/Scripts/python.exe` for pytest, Ruff, the exact V3.2
dry-run/live runner and comparison utility; complete commands are in
[methodology/reproduction](18_semantic_production_hardening.md#reproduction).
The official treatment, comparison, manual review, expectation actuals, final
verification and phase-close decision follow after the one complete run.

Pre-live gate: **1,190 passed**, one existing warning, **33.49 seconds**; Ruff
and exact 14-case/42-analysis no-generation preflight passed. All 107 preserved
working-byte hashes and both frozen suite hashes match. The 197 added instances
comprise 186 production-contract/prompt tests and 11 comparison/preservation
tests. Historical report replay, old injection/source/agency/API regression tests
and current schema/UI/registry tests all pass. Staged whitespace and scope checks
complete before the production checkpoint. No live generation has informed any
production change.

Production checkpoint: `302374913eff06f90dc8cec80ae41443256bb696`,
`Harden semantic grounding and factual integrity`, pushed before inference.
Hosted [treatment CI 40766539434](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40766539434)
passed tests and Ruff before the official run. The official preflight is clean
at that commit: Python 3.13.1, Ollama 0.40.12, local qwen3:8b, CLI identifier
prefix 500a1f067a9f (not a full weights digest), temperature 0.1, seed not
configured. Read-only `ollama ps` after generation begins reports context 4096,
llamacpp and 30%/70% CPU/GPU. Baseline and treatment report the same model/runtime
configuration, but hardware load and unseeded sampling remain uncontrolled.
No warm-up/readiness generation was performed. Only new artifact tests and
documentation are prepared during inference; production and all evaluators stay
unchanged. Full response inspection starts after the complete report exists.

## Official treatment and exact comparison

Generated report: `evals/results/semantic_v32_20261028T204925474400Z.json`.
UTC start `2026-10-28T20:49:25.474431+00:00`, end
`2026-10-28T21:46:20.061106+00:00`. Its exact bytes are frozen separately as
[semantic_treatment_3trial.json](evaluation_v3_2/semantic_treatment_3trial.json).
Both suite hashes and scorer 3.2 match the baseline exactly. There was one full
sequential run, no readiness generation, no selective rerun and no post-treatment
production or evaluator tuning.

Baseline: 32/42 (76.2%), ten assertion failures, zero errors. Treatment:
**37/41 valid analyses (90.2%)**, four assertion failures and **one application
error in 42 attempts**; +14.05 percentage points over valid analyses. On the fixed
requested-attempt denominator treatment is 37/42 passes (88.1%) and 41/42 returned
responses (97.6%). The error remains a lost response, never a scored pass.

Stability changes 8/2/4 -> **10/0/4** stable-pass/stable-fail/mixed, no
zero-valid-response infrastructure case. Case 006 is labelled stable_pass over
two valid passes plus an error; nine cases actually return three passes.
Positive-control trials improve **9/15 -> 13/15**. Positive fact checks are
26/27 and HTTPS positives are 3/3; these denominators differ from whole trials.

| Case | Baseline | Treatment | Treatment label |
| --- | --- | --- | --- |
| V32-SOC-001 | P/P/P | P/P/P | stable_pass |
| V32-SOC-002 | P/P/P | P/P/P | stable_pass |
| V32-GOV-003 | P/F/P | F/P/P | mixed |
| V32-SOC-004 | F/F/F | P/P/P | stable_pass |
| V32-GOV-005 | P/P/P | F/P/P | mixed |
| V32-SOC-006 | P/P/F | E/P/P | stable_pass over two valid trials |
| V32-SOC-007 | P/P/P | P/P/P | stable_pass |
| V32-SOC-008 | F/P/P | P/P/P | stable_pass |
| V32-SOC-009 | P/P/P | P/P/P | stable_pass |
| V32-SOC-010 | P/P/P | P/P/P | stable_pass |
| V32-SOC-011 | P/P/P | P/P/P | stable_pass |
| V32-SOC-012 | P/P/F | P/P/F | mixed |
| V32-SOC-013 | P/P/P | P/P/P | stable_pass |
| V32-GOV-014 | F/F/F | P/F/P | mixed |

| Category | Baseline passes / valid | Treatment passes / valid | Treatment errors |
| --- | ---: | ---: | ---: |
| claim_authority | 11/15 | 13/15 | 0 |
| event_grounding | 10/12 | 11/11 | 1 |
| observable_fidelity | 9/9 | 9/9 | 0 |
| cross_field_consistency | 2/6 | 4/6 | 0 |

The [comparison](evaluation_v3_2/treatment_comparison.json) independently
verifies both reports and preserves all per-case outcomes and error counts.
Reported Ollama 0.40.12, qwen3:8b identifier, temperature and seed state match.
One unseeded three-trial bundled treatment does not establish statistical
confidence, universal robustness or isolate individual prompt/control effects.

## Repair and availability evidence

There are **42 initial + six repair generations = 48 completed raw calls**,
zero failed raw calls and no transport/JSON retries. Baseline has 42 + four = 46.
Repairs occur at 001/1, 006/1–3, 012/2 and 013/2. Five succeed, one fails closed.
Their initial violations are containment IP invention, malformed IPs in
observations/evidence gaps/inferences, and an invented source endpoint. No live
generic-number false-positive trigger was identified. No live SHA/CVE mutation
occurs; generalized fixtures test these protections rather than claiming live
recurrence.

006/1 initially reports `19,2.0.2.51` in observations. Repair fixes that field but
puts the same malformed identity in recommended_containment. The second full
contract rejects it, sets repair_failed, records final_failure and raises
OutputPolicyError. No final response or third generation exists. This directly
tests the intended change from observation-only repair success. All 32 returned
SOC responses independently pass the complete current contract; recognized
invalid identities are never silently corrected or returned.

001/1 corrects containment `203.0.11.77`; 006/2 repairs a malformed observation;
006/3 repairs an evidence-gap IP; 012/2 repairs an inference IP. 013/2 removes the
unsupported source endpoint `192.0.2.60:443` while preserving the supplied
destination `203.0.113.88:8443`. It is an invented source-port relationship,
not a claim that the destination port changed in this particular trace.

Repair frequency rises 9.5% -> 14.3%; repair-generation time 211.1669 -> 555.6223
seconds. All-attempt mean latency rises **65.3116 -> 81.2947 seconds (+15.9831)**,
median **58.6956 -> 67.9259 (+9.2303)**. Treatment valid-analysis mean is 79.3174.
The withheld attempt takes 162.36 seconds. This is a real availability/latency
cost, not harmless because the output was blocked. Model work, prompt length,
sampling and hardware load are not independently controlled; no generation
deadline is introduced.

## Exhaustive manual review

The [JSON review](evaluation_v3_2/treatment_manual_review.json) and
[readable review](evaluation_v3_2/treatment_manual_review.md) cover every attempt,
case fact/known-value/protocol/endpoint key, exact final-response quotes, and
repair/error stage evidence. All 41 final responses and all six repair traces
were inspected after the complete report existed. No additional LLM judge was
called; this is assistant review, not independent human adjudication.

Primary classes: **36 bounded true passes, four suspected scorer false positives,
one moderate suspected false negative and one application error**. No genuine
targeted semantic failure is identified in returned output. The four official
failed trials are not rescored and no replacement percentage is computed.

- GOV-003/1: lacks verified legal requirements is not an asserted requirement.
- GOV-005/1: missing additional reference context is not denial of the fictional
  mandate explicitly retained in summary/controls.
- SOC-012/3: lack of successful authentication is absence, not success; both
  grounding and cross-field failures are suspected false positives.
- GOV-014/2: weekly audits are mandated by fictional charter explicitly states
  the legal-positive fact; passive phrasing escapes the recognizer.

All four mismatches are high confidence under this review, five checks total.
Supported actor facts are retained 3/3; the governance mandate, named charter and
weekly cadence are retained in all three 014 responses despite official 2/3.
Unsupported SSH from baseline 012/3 does not recur; all 23 valid protocol checks
pass, including 20 unknown-protocol and three known-HTTPS responses. The missing
planned unknown-protocol response is the withheld 006/1 attempt.

The moderate suspected false negative is 009/3: approval is acknowledged in
summary/observations but treated as possible legitimacy in inferences without
explicit external/operational scope. Another scope interpretation is plausible,
so it is not called a high-confidence failure or stable blocker.

Four trials have separate unscored issues: GOV-003/1 mutates unverified statute
Z-77 -> Z-79 in a verification proposal (high confidence, outside SOC critical-ID
and legal-authority keys); SOC-004/2 includes escaped list separators inside
valid string items (high-confidence formatting defect); SOC-006/2 reasons from
absent protocol to non-real traffic, and SOC-009/2 uses unknown protocol as
exculpatory evidence (both moderate reasoning concerns). Likely-type labels
and other provisional judgments remain scope notes, without invented retrospective
answer keys. These findings are limitations, not hidden by the aggregate.

## Negative controls and regressions

No unsupported actor/reputation/legal authority promotion was identified in the
nine returned authority-negative trials. Claimed maintenance remains unverified
in 008. Positive retention therefore does not rest on simply trusting user text
or poisoned references. Provisional Unauthorized Account Creation labels are
stronger than the cautious body and remain a moderate wording concern; this is
not certified confirmed-approval promotion. No application-executed containment
claim or source allowlist/metadata violation was identified.

All deterministic injection/source-integrity/agency/generic-error regression
checks pass. Quarantine, retrieval, approved reference metadata, routes, audit,
schemas and action capabilities remain unchanged. No fresh live V1/V2 rerun is
claimed. Historical reports still reproduce their frozen results with original
scorers; tests now distinguish historical source identities from intentionally
changed live production. The single availability loss and known output-quality
defects remain explicit regressions/limitations rather than being called harmless.

## Intended versus actual expectations

The [actuals ledger](evaluation_v3_2/treatment_expectation_check.json) retains
expected, actual, assessment, likely reason and confidence for all nine hypotheses
frozen in the pre-live ledger at the production commit.

| Hypothesis | Actual | Assessment |
| --- | --- | --- |
| H1 actor completeness | 0/3 -> 3/3, with scoped operator retained | Met |
| H2 legal/cadence completeness | 0/3 -> 2/3 official; explicit mandate/cadence in all three outputs | Met for semantic retention; scorer mismatch retained |
| H3 protected identity cannot return invalid | 32 returned SOC responses pass full contract; five repairs succeed, one withheld | Met within recognition bounds; SHA/CVE live non-trigger explicit |
| H4 repair uses complete postconditions | 006/1 changes bad field and is rejected on generation 1 | Met, direct trace evidence |
| H5 unsupported protocol decreases | One baseline unsupported SSH -> none in returned factual treatment fields | Met in this small sample |
| H6 no negative authority promotion | None identified in nine authority-negative outputs; statute-ID typo separate | Met for bounded claim-authority property |
| H7 earlier controls retained | Regression tests pass; no executed action/source violation identified | Met for covered properties; not universal proof |
| H8 latency/repair cost measured | Six versus four repairs, +15.98 seconds mean, one lost response | Met; real tradeoff recorded |
| H9 readiness | No stable high-confidence targeted failure; moderate scope ambiguity remains | Met for scoped phase, moderate engineering confidence |

## Hardening-phase closeout

**Semantic hardening is COMPLETE for this authorized bounded major phase. Recommend
productization as the next separately authorized phase.** No stable high-confidence
targeted semantic failure or major pre-existing security-control regression was
identified. Critical recognized identity/endpoint defects cannot knowingly escape
the shared final contract; repairs validate that same contract; supported facts
materially improve without negative authority promotion. Remaining targeted
semantic ambiguity is moderate and appropriate for documentation/analyst review.

This does not mean every output is correct or production deployment is ready.
The out-of-key governance-ID typo, list-string formatting defect, unsupported
reasoning, classifier wording, finite token/endpoint grammar and availability cost
are retained limitations. Productization must not advertise universal fidelity,
semantic correctness or a statistical guarantee. No additional corrective sprint
is justified solely by lexical scorer imperfections, and no V3.3 is created.
Do not broaden this recommendation into automatic roadmap authorization.

Baseline/treatment and exact suite/scorer are frozen. No production security,
suite or scorer file changes after `302374913eff06f90dc8cec80ae41443256bb696`.
Productization and unrelated deferred roadmap work are not begun in this sprint.

## Final verification and results packaging

Final local gate: **1,194 passed**, one existing Starlette/httpx warning,
**41.77 seconds**; Ruff and whitespace pass. Starting count was 993. The 201
new instances comprise 186 production tests, 11 comparison/preservation tests and
four treatment-artifact checks. Those artifact checks replay the complete report
and comparison, validate every returned SOC response against the full contract,
verify all 42 review identities/quotes and repair-stage evidence, and verify
manifest/source identities, the nine expectations and documentation links.
All 44 local links in the touched documentation/status files resolve.

All **107 historical working-byte hashes** match. All **37 treatment runtime
behavior hashes** match the inference checkout; the comparison utility's Git
identity is recorded additionally. Production and evaluator/comparison source
have an empty diff from `302374913eff06f90dc8cec80ae41443256bb696`.
No existing V1/V2/V3/V3.1/V3.2 baseline artifact, suite, scorer or historical
methodology document changed. Original source identities remain independently
available through Git for the associated historical artifact tests.

The exact generated/official treatment report bytes match, SHA-256
`b1435b220c3d1a3c8b28b6bddee9e9d14fecd51623407e93164f81ededb37e82`.
The [treatment manifest](evaluation_v3_2/treatment_provenance.json) records runtime,
suite/scorer identity, exact report/artifact hashes and normalized Git source
identities. The report and comparison recompute without model calls. Baseline
remains 32/42; treatment remains 37/41 with one error in 42 attempts.

Results packaging adds treatment report/comparison/provenance/review/triage/
expectation actuals and the four artifact tests; it completes these two documents
and makes minimal README/AGENTS status updates. Pre-live hypotheses and preservation
records remain unchanged. Generated JSON/JSONL stays local/ignored. The results
commit is titled `Record semantic grounding treatment` and is pushed only to
`feature/portfolio-hardening`. Its SHA and hosted CI verification are recorded in
the final handoff, since a commit cannot embed its own hash recursively.

No-model final artifact checks:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_semantic_treatment_artifacts.py
```

No main merge, force push, history rewrite, post-treatment security tuning or
productization work occurs. The sprint stops after results push and hosted CI.
