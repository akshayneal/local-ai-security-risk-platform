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

The official run, complete manual review, actual-versus-expected ledger, final
verification, commits and hosted CI will be recorded after the pre-live gate.

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
