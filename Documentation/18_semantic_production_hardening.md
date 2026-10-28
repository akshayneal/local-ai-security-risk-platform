# Semantic production hardening and exact V3.2 comparison

This is the authorized final semantic/reliability treatment before a closeout
decision. It changes production enforcement and prompts, not the frozen V3.2
ruler. The baseline remains **32/42 (76.2%)**, zero application errors, eight
stable-pass, two stable-fail and four mixed cases; positive controls are 9/15.
See [baseline triage](evaluation_v3_2/failure_triage.md). Three unseeded trials
are preliminary stability observations, not statistical confidence.

## Treatment architecture

The existing request -> retrieval -> neutralized prompt -> local Ollama JSON ->
citation cleanup -> source allowlist/metadata restoration -> output policy ->
Pydantic response pipeline remains. SOC still permits one initial generation and
at most one policy repair. No public schema, endpoint, dashboard, registry,
reference pack, dependency, model configuration or audit format changes.

Production files changed: `app/observables.py`, `app/output_policy.py`,
`app/soc_analyzer.py` and `app/prompts.py`. Production imports no evaluation code.
The comparison utility is separate and does not score model outputs differently.

### Identity and endpoint enforcement

Ten analyst-facing SOC fields are protected: summary, likely incident type, MITRE
mapping, observed evidence, inferences, analyst note, investigation steps,
containment recommendations, false-positive considerations and evidence gaps.
`alert_id` and structured source metadata retain their existing handling.

Recognized IPv4, SHA-256 and CVE-style identities must match original request
values exactly, including spelling/case. Reference cards cannot authorize a new
case observable. Malformed comma/space/extra-octet IP shapes are rejected;
near-input three-component corruptions use 85% sequence similarity. Near-SHA
tokens use 56..72 hex and 90% similarity, plus any longer hex run containing the
exact supplied hash, covering appended-length mutations. No value is corrected
or silently substituted. Omission is allowed; presence/completeness is a separate
semantic property.

Endpoint checks recognize IP:port, explicitly labeled destination IP/port and
to-IP-on-port forms. Repeated pairs must occur in the original request. Clear
source/destination labels or from-IP-to-IP relationships cannot reverse supplied
roles. Machine-style destination-port assignments and explicit observed/case
destination labels preserve supplied ports. Unbound standard-port guidance,
time windows, PIDs, counts and dates remain allowed; no integer-subset policy is
introduced. Hypothetical concrete IP/hash examples must use supplied identities
or descriptive placeholders, since the deterministic guard cannot establish
that a new address is harmless from natural-language intent.

These are syntax-bounded software checks. IPv6, domains, arbitrary hash spelling,
unrecognized endpoint paraphrases and universal numerical/semantic consistency
are outside their guarantee. Numeric dotted-version ambiguity and malformed
tokens outside recognition bounds remain limitations. A token can be copied
exactly but attached to an unsupported claim; membership does not prove truth.

### Complete repair postconditions

`_validate_generation` applies the same processing and validation to generations
0 and 1. `validate_soc_output` combines the nonempty/nonblank observation
contract, ten-field identity/endpoint checks and complete Pydantic response
validation. Malformed source/citation-processing shapes yield fixed machine
violations on either generation. Source cleanup/allowlisting runs again on repair.
Any remaining violation after generation 1 raises `OutputPolicyError`, preserving
the existing generic external API error. No third policy generation exists.

The repair prompt regenerates the whole JSON using the already neutralized
original prompt, machine-only reasons, original observable lists and endpoint
pairs. It never refeeds raw failed output. It describes all output contracts and
support/protocol scope, regardless of which field originally failed. Existing
transport/JSON client retries remain separate and unchanged.

Opt-in traces retain both generations' raw/processed snapshots and policy reasons,
plus contract_accepted, contract_rejected and final_failure stages. Repair flags
describe acceptance/failure. Ordinary API calls still enable no trace, return no
trace and add no trace to audit records.

### Prompt-enforced semantic properties

Shared/SOC/governance guidance distinguishes unverified allegations, facts
explicitly established within the supplied record or applicable internal/scenario
requirements, and external verification. Supported named identities, event facts,
approvals, requirements, named authority and supplied cadence should be retained
within their scope. External verification gaps must not erase supplied support.
Known cadence and unknown methodology are separate. Unverified reference-only
reputation/actor/legal claims must remain attributed and qualified; embedded
instructions never become authority.

SOC guidance forbids inferring protocol from password-event wording or familiar
ports. Explicit known protocols may be retained; unknown, negated and illustrative
protocol mentions do not establish use. No protocol ontology or semantic regex
judge is implemented. Legal applicability, authority, actor support, missingness
paraphrases, event entailment and broader consistency remain prompt-guided and
manually reviewed, rather than falsely claimed deterministic guarantees.

## Preservation and experiment protocol

[Preservation](evaluation_v3_2/semantic_hardening_preservation.json) records 107
unchanged historical/evaluator/unrelated-production paths plus original identities
for the four authorized production files and six associated artifact tests.
Frozen suites, scorers, official baseline artifacts and historical methodology
remain unchanged. Associated artifact tests now verify changed source identities
at the pre-treatment commit; other files remain checked against current bytes.
CI fetches full Git history so these checks never silently skip source evidence.
No scorer semantics or historical score changes.

Frozen suite byte SHA-256:
`b55be3f59c6cce919f489d3fadbf72663d35c58c6b701ae76293e73e72c396f5`.
Semantic SHA-256:
`fd197cc340994633bad71ce5a7fd4853dd10dceca51310c445c05de7ab1a5018`.

The [nine pre-live hypotheses](evaluation_v3_2/treatment_expectations_pre_live.json)
are committed before inference: supported actor/legal improvements; protected
identities repaired or withheld; identical full repair contract; less unsupported
protocol; no negative-control overclaiming; intact injection/source/agency controls;
measured repair/latency cost; and no stable high-confidence targeted blocker.

Commit/push production before one sequential 14-case, three-trial run using the
exact frozen runner and scorer. Record actual Ollama/model identifier, temperature
0.1 and seed state. No warm-up generation, failure rerun, evaluator recalibration
or post-treatment production tuning. After the complete report exists, inspect
every final response, including negative controls, without a replacement official
percentage. Application errors remain separate from semantic failures.

## Reproduction

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
git diff --check HEAD
.\.venv\Scripts\python.exe -m evals.semantic_runner_v32 --trials 3 --dry-run
ollama --version
ollama ls
.\.venv\Scripts\python.exe -m evals.semantic_runner_v32 --trials 3
.\.venv\Scripts\python.exe -m evals.semantic_treatment_compare Documentation/evaluation_v3_2/semantic_baseline_3trial.json Documentation/evaluation_v3_2/semantic_treatment_3trial.json --output evals/results/new_treatment_comparison.json
```

Generated JSON/JSONL remains ignored. Official treatment evidence uses distinct
filenames; the baseline is never overwritten. The comparison verifies both
reports, suite/scorer/trial/model configuration identity, categories, positive
controls, per-case transitions, application errors, repairs and latency. One
bundled unseeded comparison cannot isolate each control's causal effect.

## Availability and closeout criteria

A stronger guard can trigger more repair, increase latency or deliberately return
a generic error after failed repair. That is a real availability cost, not a pass
or harmless omission. Do not seek 100%. Recommend closing this phase only if
there is no stable high-confidence targeted failure, protected corruption cannot
knowingly leave the complete contract, positives materially improve without
negative overclaiming, and earlier controls remain intact. Ordinary moderate/low
semantic ambiguity belongs in documentation/manual review. A stable material
high-confidence blocker justifies at most one tightly scoped corrective sprint;
otherwise recommend productization without starting it here.

The [engineering report](19_semantic_hardening_sprint_report.md) records the final
gate, committed treatment, official results, exhaustive review and closeout
decision after the single run.
