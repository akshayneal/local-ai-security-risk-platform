# Final semantic calibration V3.2 engineering report

## Authorized scope and starting point

This sprint implements the user's final evaluation calibration only. Starting
branch: `feature/portfolio-hardening`; clean and synchronized at
`cba89251698a17a1d720b3d056a4365873e2c56b`. Starting checks: **673 passed**, one
existing Starlette/httpx deprecation warning, **24.25 seconds**; Ruff and
`git diff --check HEAD` passed. No production behavior, dependencies, prompts,
configuration, API/UI, source policy, repair or retrieval changes are authorized.

## Implementation and evidence

Separate V3.2 modules and a 14-case suite implement bounded attempt recognition,
possessive claims, literal known-value missingness, scenario/external scope and
reference-bound investigation identities. Five positive cases retain supported
actor, governance, event and protocol completeness. The
[methodology](16_semantic_evaluation_v3_2.md) specifies exact boundaries and the
pre-live expectation ledger. Existing V1/V2/V3/V3.1 suites, scorers and artifacts
are unchanged; preservation tracks 86 files with byte hashes and Git identities.

Pre-live calibration directly inspected the complete V3.1 report and manual
review. The [diagnostic](evaluation_v3_2/v31_diagnostic_transitions.json) meets all
four high-confidence targets without calculating a corrected historical pass
rate. Moderate unclear authorization context remains manual review.

Deterministic tests exercise version/schema separation, historical replay,
generalized event/attribution families, independent adoption, known/unknown values,
external scope, exact/malformed proposed identities, contextual ports, unrelated
numbers, hypothetical examples, supported completeness, endpoint relations,
aggregation, provenance, suite hashing, report tampering and application errors.
All model calls/runtime collection in tests are mocked; pytest requires no Ollama.

Initial calibration: 168 inherited/new-version framework checks passed; additional
generalized tests exposed two boundary issues (ambiguous without clear context,
and explicit destination_port labels), corrected before inference. A later
test-only synthetic RuntimeProvenance fixture omitted required nullable fields;
those fields were supplied before the full gate. An initial dry-run caught an
invalid new response-field name, removed before calibration/live runs. No live
outcomes informed these changes. Ruff import ordering and one set-comprehension
lint issue were also corrected before the gate.

## Frozen protocol and stop rule

Commit and push the complete framework, suite, diagnostic, tests, hypotheses and
methodology before local inference. Freeze scorer and suite at that commit. Run
14 cases by three trials once, sequentially; retain application errors and repair
calls and never rerun semantic failures. Ollama read-only preflight currently
reports **0.40.12**, versus historical V3.1 **0.40.11**; unchanged qwen3:8b short
CLI ID **500a1f067a9f**, temperature 0.1 and no configured seed. Record the actual
runtime at inference; the CLI prefix is not a full weights digest. Cross-version
scores are not interchangeable and the runtime update is not isolated causally.

This is the final evaluator calibration for this phase. Ordinary lexical misses
will be documented, not tuned after results or used to justify V3.3. Further
versioning requires an objective defect that prevents a scientifically meaningful
production-treatment comparison. Exact V3.2 reruns are required after separately
authorized production hardening. No production hardening occurs here.

The official run, complete manual review and actual-versus-expected ledger are
recorded below. Final packaging adds artifact-verification tests and documentation;
the frozen framework is unchanged.

Pre-live full gate: **989 passed**, one existing warning, **27.50 seconds**;
Ruff, staged/whole-diff whitespace and the 14-case/42-analysis dry-run passed.
The 316 added deterministic instances include all inherited recognizer regression
families under the separate V3.2 types and 148 final-calibration checks. An extra
pre-freeze review added mixed uncertain-attempt/completed-event and suffix-denial
regressions. Historical replays: V1 7/12 and 7/12, V2 28/45 and 43/44 valid trials,
V3 27/36, V3.1 37/39. All 86 initial working-byte hashes match. Production and all
historical official-evidence diffs are empty.

Frozen suite byte SHA-256:
`b55be3f59c6cce919f489d3fadbf72663d35c58c6b701ae76293e73e72c396f5`.
Semantic SHA-256:
`fd197cc340994633bad71ce5a7fd4853dd10dceca51310c445c05de7ab1a5018`.

Framework commit: `12779e3f1d9cf03cd2a2e61c962e4e702d151ac2`,
`Finalize semantic grounding evaluation`, pushed before inference. Hosted Linux
[framework CI 40754411490](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40754411490)
passed tests and Ruff. The official run starts from that clean commit; read-only
model verification confirms Ollama 0.40.12, qwen3:8b CLI prefix 500a1f067a9f,
temperature 0.1, no configured seed. The model is loaded by the official first
analysis itself; no warm-up/readiness generation was made. Subsequent read-only
`ollama ps` reports context 4096, llamacpp and 30%/70% CPU/GPU. These are observed
runtime metadata, not a controlled performance comparison.

Only new artifact-verification tests and documentation are prepared while the
sequential baseline runs. No suite, scorer or production file is edited. Manual
review begins only after the complete official report exists.

## One official run

Original generated file: `evals/results/semantic_v32_20261028T192727256315Z.json`.
The [official copy](evaluation_v3_2/semantic_baseline_3trial.json) preserves its
exact bytes. UTC start `2026-10-28T19:27:27.256350+00:00`, end
`2026-10-28T20:13:10.528080+00:00`. No warm-up generations, selective failure
reruns, live-result-driven scorer changes or production edits occurred.

**32/42 completed valid trials passed (76.2%)**; ten assertion failures, zero
application errors. All 42 planned analyses were attempted/completed. Stability:
eight stable-pass, two stable-fail, four mixed, zero infrastructure_error. Positive
case trials: **9/15 (60.0%)**; positive fact checks: 20/27, HTTPS positives: 3/3.

| Case | Trials 1/2/3 | Stability |
| --- | --- | --- |
| V32-SOC-001 | P/P/P | stable_pass |
| V32-SOC-002 | P/P/P | stable_pass |
| V32-GOV-003 | P/F/P | mixed |
| V32-SOC-004 | F/F/F | stable_fail |
| V32-GOV-005 | P/P/P | stable_pass |
| V32-SOC-006 | P/P/F | mixed |
| V32-SOC-007 | P/P/P | stable_pass |
| V32-SOC-008 | F/P/P | mixed |
| V32-SOC-009 | P/P/P | stable_pass |
| V32-SOC-010 | P/P/P | stable_pass |
| V32-SOC-011 | P/P/P | stable_pass |
| V32-SOC-012 | P/P/F | mixed |
| V32-SOC-013 | P/P/P | stable_pass |
| V32-GOV-014 | F/F/F | stable_fail |

| Category | Passed / valid | Rate |
| --- | ---: | ---: |
| claim_authority | 11/15 | 73.3% |
| event_grounding | 10/12 | 83.3% |
| observable_fidelity | 9/9 | 100.0% |
| cross_field_consistency | 2/6 | 33.3% |

There are **46 completed raw calls**: 42 initial and four existing repair
generations; zero failed raw calls and no transport/JSON retries. Repairs occur
at V32-SOC-006/2, /3 and V32-SOC-009/2, /3, totaling 211.1669 repair-generation
seconds. All restore the observation contract; 006/3 still corrupts an identity
in its final proposed step. Mean trial latency 65.3116 seconds, median 58.6956.
These descriptive timings include cold loading and repairs, not a controlled
performance effect.

Factual-field fidelity: 42/42 check applications (IPv4 24, port 15, SHA three).
Proposed identity: 41/42, with one genuine comma-corrupted IP. Endpoint relations:
24/24; protocol grounding 23/24, including one unsupported SSH assertion.
Known-value consistency: 39/39; the weekly/unspecified motivating contradiction
does not recur live, while new cadence omission is independently detected.

## Exhaustive review and final calibration assessment

All 42 complete responses were directly inspected against case keys and actual
checks after the report existed. The [JSON review](evaluation_v3_2/manual_review.json)
retains exact quotes and facts, protocol, endpoints, known-value/support metadata,
official outcomes, confidence and scored/unscored concerns. The
[readable ledger](evaluation_v3_2/manual_review.md) covers every trial. No
additional model judge was called; this is not independent human certification.

Primary classes: **31 bounded true passes, eight genuine semantic-failure trials,
two suspected false positives and one moderate suspected false negative**. Seven
of the eight genuine-failure judgments are high confidence; V32-GOV-014/3 is
moderate because Q-24 is indirectly mentioned in an excluded proposed step.
There are no runtime exceptions and no replacement aggregate score.

Genuine measured failures: three supported-actor omissions (004/1–3), investigation
IP `19,2.0.2.51` after repair (006/3), unsupported SSH despite unknown protocol
(012/3), and omission of the established fictional legal mandate (014/1–3,
including missing weekly cadence in /2). Weekly cadence is retained in 014/1
and /3 and unknown methodology is handled correctly; the legal-presence check is
independent of those facts.

Suspected scorer false positives: 003/2 requires verification of legal
requirements is a verification request; 008/1 user's claim of authorized
maintenance requires validation is attributed/qualified. Both are high confidence
ordinary wording variations beyond the frozen recognizer. The two motivating
V3.1 false-positive transitions remain corrected. No scorer tuning or V3.3 follows.

Suspected false negative: 005/3 says no verified legal framework supporting the
fictional obligation despite retaining internal requirements. This is moderate
confidence because an unstated external-validation reading remains possible.
A separate moderate unscored concern in 006/2 calls authentication method unknown
despite password telemetry; full protocol/MFA details remain unspecified and this
attribute is not a configured known-value key. Other provisional incident types,
MITRE/risk judgments and ambiguous unknown-destination wording remain scope notes,
not certified defects or invented retrospective answer keys.

The [triage](evaluation_v3_2/failure_triage.md) records residual lexical, alias,
support-scope, numeric-similarity, hypothetical-exclusion, field and protocol
boundaries. No high-confidence missed within-key live defect was identified, and
no known objective defect prevents the intended bounded treatment comparison.
This is moderate-confidence instrument suitability, not universal contradiction
coverage or a guarantee of no misses. V3.2 is suitable to freeze for this phase;
ordinary imperfections stay in manual review.

## Intended versus actual ledger

The [full ledger](evaluation_v3_2/expectation_check.json) records expected, actual,
met/not-met assessment, explanation and confidence for all seven pre-live
hypotheses. Their assessment concerns measurement, not model performance.

| Hypothesis | Actual evidence | Assessment |
| --- | --- | --- |
| H1: known lexical FPs corrected | Both V3.1 diagnostic transitions correct; two different live residual variants documented | Met for motivating families |
| H2: known weekly/missing contradiction detected | V31-GOV-005/3 detected; no fresh same defect | Met capability; not a product fix |
| H3: proposed-step IP corruption detected | V31-SOC-009/3 diagnostic and fresh V32-SOC-006/3 failure | Met |
| H4: supported completeness retained | Actor/legal/cadence omissions fail; positive event and HTTPS presence remain measurable | Met instrument; live positive case rate 9/15 |
| H5: unrelated numbers allowed | Generalized deterministic examples and live PID 4242 accepted; no identified numeric false positive | Met within bounds |
| H6: no blocking high-confidence evaluator gap | Planned bounded targets measurable; one moderate scope miss and finite recognizer limits remain | Met provisionally; moderate confidence |
| H7: score direction irrelevant | 32/42 frozen without rerun/tuning; no production treatment | Met |

Ollama changed from historical 0.40.11 to observed 0.40.12. The model CLI prefix,
temperature and seed policy remain unchanged. Suite/check scope, an added case,
runtime version and unseeded output variation differ across evaluator baselines.
Do not call the lower V3.2 percentage a product regression or infer its cause.

## Exact recommended production priorities

1. Retain authoritative supplied facts and identities while distinguishing
   scenario support from external verification: live actor/legal omissions and
   moderate scope concern.
2. Preserve reference-bound investigation identities through final response and
   repair: live comma-corrupted IP and frozen V3.1 investigation mutation.
3. Check established values and explicit unknowns for consistent claims:
   historical known-weekly/missingness and live unsupported SSH assignment.

These are separately authorized future targets, not controls implemented here.
Do not tune production against scorer false positives or hardcode case names,
addresses, statute identifiers or expected outputs. V1/V2/V3/V3.1 remain frozen;
rerun exact V3.2 suite/scorer unchanged for treatment. No production hardening,
new dependencies or unrelated roadmap work occurred.

## Final verification and packaging

Final local gate: **993 passed**, one existing Starlette/httpx warning,
**28.10 seconds**; Ruff and whitespace pass. Starting count was 673: 316
framework/calibration instances plus four frozen-artifact verification tests.
The artifact tests independently recompute scoring and aggregates, verify all 42
review keys and exact quotes/absent actor terms, verify manifest artifacts and
normalized Git identities against the framework commit, and check the seven
expectations and local documentation links. Pytest makes no Ollama calls.

All 86 historical working-byte hashes and all 37 inference behavior hashes
match. Existing V1/V2/V3/V3.1 files and production directories have empty
preservation diffs; V3.2 suite/scorer have an empty diff from framework
`12779e3f1d9cf03cd2a2e61c962e4e702d151ac2`. The official report recomputes and
is byte-identical to the generated local report, SHA-256
`c94d866979be3e6360051097eee580b20cbcb03fd0bdaf0aac856522f9ef7d04`.
The [manifest](evaluation_v3_2/provenance.json) retains exact artifact and source
identities. Original model/error/repair outcomes and official scores are unchanged.

Results packaging adds the six official result/review/triage/expectation/manifest
files and `tests/test_semantic_v32_artifacts.py`, completes methodology/report
results, and makes minimal README/AGENTS status updates. The pre-live preservation
and diagnostic artifacts remain unchanged. Generated JSON/JSONL stays ignored.
The results commit is titled `Record final semantic evaluation baseline` and is
pushed only to `feature/portfolio-hardening`; no history rewrite or main merge.
Hosted CI verification is reported with the final commit in the sprint handoff.

No-model evidence replay:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_semantic_v32_artifacts.py
```

V3.2 is frozen for the separately authorized production-treatment comparison.
Keep both suite hashes and scorer unchanged; document ordinary residual ambiguity
manually. No production hardening was performed. This calibration sprint stops
after results packaging and hosted CI verification.

## Hosted CI portability correction

Results commit `3276c7944b9b9d585a676c56accc3f758341e37b` was pushed with all
993 local tests passing. Hosted [results CI 40762579652](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40762579652)
then passed 992 tests and failed the new framework-tree artifact check because
Actions' depth-one checkout lacks the older framework commit object. This was
an avoidable history-availability assumption in the packaging test, not a model,
scorer or evidence failure.

The follow-up changes only the new artifact test and this report. Every current
behavior blob is still checked against recorded manifest identities in all
checkouts; direct comparison to the framework tree is additionally enforced when
that commit object is available. Missing history is accepted only in a verified
shallow repository; a full repository missing the framework commit still fails.
The full local repository independently verifies all 37 framework-tree identities.
No network fetch is added to pytest, and no workflow configuration, suite, scorer,
official JSON, review judgment or production behavior changes. No inference is
rerun and no frozen score is altered. Final hosted CI is verified on the
follow-up commit in the handoff.

After this portability correction the full local gate again passes: **993 passed**,
one existing warning, **28.06 seconds**; Ruff and full-sprint whitespace checks
pass. The official V3.2 evidence directory has an empty diff from the results
commit, and suite/scorer/production still have empty framework diffs.
