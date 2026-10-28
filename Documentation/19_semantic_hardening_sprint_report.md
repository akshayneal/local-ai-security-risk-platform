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
