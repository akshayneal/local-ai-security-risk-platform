# Sprint 7 exact change inventory

All paths are development-only. No release/merge/tag/PR or stable-branch change.
Starting source: `1c4f937f2b067a4a2b0d8ac8cf5db4f552555d00`.

| Path | Purpose |
| --- | --- |
| `Documentation/45_development_launcher.md` | Canonical gateway, strict legacy Stop/Start migration and unchanged shortcut targets. |
| `Documentation/50_cross_pillar_rc_hardening_plan.md` | Pre-implementation scope, baseline, checkpoint order and pre-inference output-root configuration. |
| `Documentation/51_cross_pillar_rc_readout.md` | Implemented matrix, trust diagram, real/stub evidence, learner concepts, blockers and manual acceptance. |
| `Documentation/cross_pillar_v1/ci.json` | Preserved first exact-SHA CI failure, actual hosted counts, runtime, hash mismatch and bounded transport fix. |
| `Documentation/cross_pillar_v1/change_inventory.md` | This exact path inventory and checkpoint/preservation explanation. |
| `Documentation/cross_pillar_v1/live_readout.json` | Minimal synthetic outcome evidence, exact run/artifact hashes, deterministic metrics and implementation-authored semantic review. |
| `Documentation/sprint7_preservation.json` | Exact authorized paths, every protected base blob, 185 inherited cache hashes and scoped LF-attribute refinement. |
| `README.md` | Current three-workflow launcher guidance and truthful evidence/readiness links. |
| `dashboard/ai_security.py` | Startup guidance now names the three-workflow development launcher; no analyzer/correction/grant behavior change. |
| `evals/cross_pillar_v1/.gitattributes` | New-suite checkout policy: LF for code/plans; no text conversion for the two original CRLF frozen inputs, with CR-at-EOL recognized and exact committed-byte regression. No working input bytes changed. |
| `evals/cross_pillar_v1/__init__.py` | Inert new evaluation namespace. |
| `evals/cross_pillar_v1/cases.json` | Twelve new frozen synthetic submissions with expected facts/non-inferences and controls. |
| `evals/cross_pillar_v1/corpus.json` | Four new synthetic documents and precommitted exact-version operator-owned reviews/scopes. |
| `evals/cross_pillar_v1/freeze.json` | Literal source/case hashes and normalized application Git blobs before inference. |
| `evals/cross_pillar_v1/plan.json` | Frozen question, method, order, provider identity, runtime, limits and stopping conditions. |
| `evals/cross_pillar_v1/rubric.md` | Pre-outcome metrics/denominators and separation of deterministic versus qualitative versus independent review. |
| `evals/cross_pillar_v1/runner.py` | Exclusive sequential foreground real-provider runner through TestClient, isolated fresh workspace/audit and durable results. |
| `evals/cross_pillar_v1/transport.py` | Evaluation-only zero-retry loopback HTTP transports sharing durable per-generation budget and bounded retention. |
| `scripts/development/Development.Common.ps1` | New-launch command; exact legacy stop-only state reading; legacy readiness/start refusal without weakening ownership. |
| `scripts/development/Start-Development.ps1` | Early legacy-state refusal before child/state/reuse/automatic-stop operations. |
| `scripts/development/Test-DevelopmentGateway.ps1` | Mock-only old/new migration, strict legacy child stopping, foreign executable/identity/port refusal. |
| `scripts/development/Test-DevelopmentIdentity.ps1` | Expected current API module only; all prior identity scenarios preserved. |
| `tests/test_ai_security_evaluation.py` | Original assertions unchanged; verify/replay calls use an explicit immutable Sprint 6 source snapshot, with live backend/data hash checks and AST proof. |
| `tests/test_cross_pillar_evaluation.py` | Offline cap/deadline/transport retries/freeze/workspace tests, actual inference retry seam and Windows LF regression. |
| `tests/test_cross_pillar_smoke.py` | Three real UI/backend sample paths with stubs, original route superset contract, and fail-closed inconsistent-model regression. |
| `tests/test_development_launcher.py` | Cross-platform command/order guard and seven mocked Windows migration scenarios. |
| `tests/test_sprint5_preservation.py` | Protected-source blob comparison reads immutable end-of-Sprint-6 snapshot; original scope interval and assertions retained. |
| `tests/test_sprint6_preservation.py` | Fixed historical interval, source snapshots and original Sprint-5 AST proof snapshot; original assertions retained. |
| `tests/test_sprint7_preservation.py` | Active scope/blob/byte guards, exact inherited file sets, executable AST pinning proof and negative mutations. |

## Checkpoint identities

- Scope/preservation: `c35fb2672e247a7a341d09791b0d2b5ba0412367`.
- Evaluation freeze before inference: `f1a86c7f70efd03239c69eea0fc6f0903414bef0`.
- Gateway/migration and experiment application identity: `587570e549992fc16d3621d7790f6e324e8c43a1`.
- Live baseline/readout: `1cb869f3983fe36f71ac0cc9418b8940f80df4cc`.
- Historical replay, LF and observed failure regressions: `a01137bd24054d2ab332e40f350b792d62f416f4`.
- Final RC documentation follows in ordinary additive history. Exact ordered
  final commits and final
  pushed SHA/CI URL are in the handoff; a tracked document cannot contain its
  own final commit identity.

## Preservation and scope refinement

The 405 original untracked files and 185 expressly authorized ignored caches stay
outside Git and are never executed/imported, moved or changed. All 13 inherited
Northstar files and installed AGENTS bytes are checked read-only. All prior frozen
cases/scorers/official results, original analyzers/prompts/schema contracts,
app/main.py, app/version.py, dependencies, environment, release demo and shortcut
installers are unchanged. The two prior preservation test edits pin historical
endpoints/snapshots; AST comparisons reject any other executable assertion change.
Current protection moves to the new active manifest rather than broadening prior
allowlists.

Two explicit scope refinements were needed. The first is the new suite-local
`.gitattributes`: literal evaluation SHA-256 requires LF even on a fresh Windows
checkout. The new manifest lists this exact path with a reason before its creation.
The first checkout-attribute regression passed locally but CI exposed an additional
transport problem: cases/corpus were originally frozen with CRLF while Git had
stored LF. Preserve their original pre-inference bytes with `-text -eol`; normal
trailing-space/blank-EOF/space-before-tab checks remain enabled, with CR-at-EOL
recognized for those exact two files. A committed-byte regression failed first,
then passed after exact-path restaging. No case value, body/review, rubric,
judgment, freeze hash, working input byte or model output changed. The Git diff
records restoration of literal frozen bytes, not a changed evaluation question.
The second is `tests/test_ai_security_evaluation.py`: full validation exposed a
Sprint 6 implementation binding on the explicitly authorized UI guidance text.
The active manifest was tightened for that exact test before editing. Its calls
now use an immutable `1c4f937` source snapshot, while current backend and frozen
input hashes are checked first. All original assertions/scorer/results remain;
a new AST proof limits changes to those call sites, and corrupt snapshot bytes
still fail the unchanged verifier. No frozen input, rubric, inference runner,
production analyzer or ignore rule changed.
The ignored output-root configuration was recorded before inference and does not
change any case, provider/runtime setting or budget. No optional holdout or extra
live case is authorized/run. Semantic failures are retained, without post-outcome
prompt tuning or selective replay.


## Hosted byte-transport follow-up

First final-package push `b4dc3d0346eed990aaefa050643d01ea8b842b16` failed
[CI 41132567084](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/41132567084):
1955 passed, one failed, 38 skipped, Ruff skipped. Evidence is retained in ci.json.
`a59f7943d4ca1bbff6dc7e3aa1ef3be9be533886` added the preservation policy/regression; Git initially retained its old
index blobs, caught by the regression before another push. `14ae2557902979cc43767edbedf8638b6624c238` recorded the
original frozen CRLF input bytes through exact-path restaging and explicit
CR-at-EOL handling. There was no history rewrite, dependency update or extra
model run. A final additive documentation/verification checkpoint follows; its
exact SHA and exact-commit CI result are in the handoff.
