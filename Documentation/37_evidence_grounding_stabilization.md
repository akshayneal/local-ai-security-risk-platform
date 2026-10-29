# Mini-Sprint 3.5: evidence grounding and authority stabilization

Start: clean `feature/microsoft-evidence-reliability` at
`73fd92cb8445ac39beab50ee13b8b47c5aa09e47`. Work uses child branch
`feature/evidence-grounding-stabilization`. This is a bounded stabilization sprint,
not Expansion Sprint 4 or a release. Terminal/repository/test/Git tools only;
**USER VISUAL QA PENDING**. No desktop/browser control is authorized or used.
The narrow query and source-metadata boundaries improve, but semantic stabilization
is partial: new factual, classification and body-level authority regressions remain.

## Predeclared experiment and treatment intent

Eight fresh synthetic cases were committed at
`4baae12cb14522a6706fe2d18d8c02d672a16ea8` before live outputs: network-only,
quoted-command/vendor-label negative, Entra authentication positive, LSASS command
positive, approved destructive-command positive, public informational guidance,
scoped fictional quarterly charter, and unverified fictional legal allegation.
The [rubric](../evals/grounding_stabilization/rubric.md), plan and runner are frozen.
Semantic case hash:
`eb919232e5428640c1d7f2d51006ddab42c4c72c2811b2ba7e7c58c2cd744028`.
Exact source hashes are in [freeze.json](../evals/grounding_stabilization/freeze.json).

Maximum eight baseline plus eight treatment case trials, one per case/phase. No
selective reruns or campaign against historical cases. Existing bounded policy repair
and transport/JSON retry remain separate; all requests/withholding are counted.
qwen3:8b, temperature 0.1, seed unset, default legacy retrieval, no shadow, existing
Microsoft complete-context 8192. Ordinary pytest needs no model or internet.

The runner intercepts the actual analyzer retrieval call to record query hash and
actual selected source IDs. It never reconstructs authorization from the obsolete
full-request query. Deterministic schema/source/identity checks remain separate
from quoted manual judgments; no composite semantic score or statistical-confidence
claim. Review is unblinded implementation-assistant review, not independent review.

The intended query boundary uses the validated original Microsoft bundle and only
table-derived event categories, excluding adapter warnings and other generated
interpretation text. Original evidence and warnings stay in model context; generic
SOC queries retain exact full-request serialization. The same query travels through
legacy, optional lexical and shadow paths. Query content supplies no access,
authority or policy grants. This does not solve negation or hostile/irrelevant terms
in original evidence, and existing optional-query truncation remains documented.

For governance, the intended authority boundary supplies structured application-owned
reference provenance separate from untrusted card content. Exact reviewed catalog
cards are local/framework guidance; arbitrary cards or self-claimed policy metadata
remain unverified. Legacy governance source relevance becomes application-owned
provenance with a trusted topic title, following the existing lexical provenance
principle. This avoids trying to prove free-form model authority claims safe through
a keyword blacklist. Source allowlisting, deduplication, titles and frameworks retain
their existing sanitation. Useful topic/provenance remains; free-form model relevance
is intentionally not a verified support explanation. No public schema change.

This mechanism must not strip or demote an explicit scoped obligation in the request.
Case-specific named authority/cadence remain separate from the authority of retrieved
guidance. Existing optional lexical policy metadata restoration remains unchanged.
Body-level legal applicability and factual entailment remain semantic limitations.

Only bounded Microsoft interpretation wording is intended beyond those mechanisms:
vendor titles and contextual mentions do not independently prove incident facts;
network connections do not establish logins; real credential-dumping observations
can support credential-access concern without authentication events. No SYSTEM_PROMPT
rewrite, new semantic fail-closed rule, endpoint parser expansion, new dependency,
retrieval default migration, registry change or live connector is authorized here.

## Preservation

[The preservation manifest](grounding_stabilization_preservation.json) binds 242
existing source/reference/documentation/evaluation paths to the starting commit.
Only `app/soc_analyzer.py`, `app/governance_analyzer.py` and `app/prompts.py` have
explicit prior-source exceptions, alongside two intended new bounded helper modules.
Original manifests, Sprint 3 artifacts, historical judgments, suites and scorers
remain checked against current Git-filtered bytes. Stable main and peeled v2.3.0
stay at `fde00d0ca5d21eecbc6973cc784550ed453edb7a`. No merge, tag or release.

The completed once-only results and final validation are recorded below.

## Implemented deterministic boundaries

`app/soc_query.py` now supplies every original table row plus schema-derived process,
network-connection or authentication modality terms. Routing case IDs are excluded:
offline inspection showed the optional tokenizer split SOC routing IDs into `soc`,
matching checklist source IDs despite no authentication terms. This is field-level
query construction, not a stopword list or an authentication exclusion filter.
The request's case ID, full raw bundle, known indicators and adapter warnings remain
unchanged in the actual model prompt. Supplied negative mentions and vendor labels
remain query evidence; no claim of universal relevance or negation understanding.

The [offline controls](grounding_stabilization/query_controls.json) compare old full
requests with the implemented helper. All eight tested old queries returned the
authentication checklist in both backends. With factual queries, only the true
authentication control retains it in the top five in both backends. Original three
diagnostic controls score 6 → 0 against the checklist; fresh network/dump also 6 → 0,
quoted/vendor note 12 → 3, approved deletion 6 → 1, and genuine authentication 13 → 7.
Nonzero scores from actual input terms remain legitimate ranking observations,
not semantic support or abstention guarantees. Separate tests cover coded Entra and
DeviceLogonEvents without English outcome descriptions, grant injection, generic
query identity, unchanged evidence/warnings and shadow isolation.

`app/reference_authority.py` wraps legacy governance reference content with
application-owned authority/provenance. Equality with an exact current curated card,
not source ID or a self-asserted policy field, establishes local/framework guidance
classification. Arbitrary/altered cards are unverified; none acquires policy scope
from its prose. After existing allowlisting, source relevance is replaced by fixed
topic/provenance metadata, including `binding_by_retrieval=false` and unresolved
applicability. This removes useful-looking but unverifiable free-form model relevance
as an intentional tradeoff; trusted titles/topics remain. Optional lexical provenance
and trusted scoped-policy metadata handling are unchanged.

The Microsoft prompt adds a short modality/vendor-label boundary, including genuine
credential-dumping support without sign-in events and case versus vendor identity.
SYSTEM_PROMPT and generic SOC prompt bytes stay unchanged. No new semantic rejection
rule or extra repair was added. Existing full-response source, observation, endpoint,
critical-identifier and post-repair validation remains the final production guard.

Before the live treatment, all 1,657 then-collected tests passed with one existing
Starlette/httpx deprecation warning; targeted query/authority and preservation checks
also passed. Final count includes later artifact replay tests, recorded at closeout.

## Completed experiment and paired findings

Both original processes completed normally: eight baseline and eight treatment
attempts, **16 actual model calls total**, zero repairs, zero transport/JSON retries,
zero application errors, and eight returns in each phase. The final treatment was
recovered complete at the Sprint 4 handoff; no call was resumed, duplicated or rerun.
Every report record equals its journal, each canonical request hash and case order
matches, and frozen case/rubric/runner hashes are unchanged. Launch code/settings:

| Phase | Clean launch SHA | Model/configuration |
| --- | --- | --- |
| Untreated | 4baae12cb14522a6706fe2d18d8c02d672a16ea8 | qwen3:8b, short digest 500a1f067a9f, temperature 0.1, unset seed, legacy/no shadow |
| Treatment | b9b1a2447f75075d9c9b92df2f630b918bc369dc | Same model/settings; existing Microsoft complete-context 8192 unchanged |

No executing application, reference or frozen experiment source changed during
either run. Later changes are offline aggregation, tests, review and documentation.
The [comparison](grounding_stabilization/comparison.json) reproduces separate
availability/latency/machine metrics; the [manual comparison](grounding_stabilization/manual_comparison.json)
replays unchanged-rubric labels, with all eight returns common to both phases.
Separate offline aggregation source is identified in
[treatment provenance](grounding_stabilization/treatment_provenance.json); it adds
no semantic scorer or new answer key.

| Measurement | Untreated | Treatment |
| --- | ---: | ---: |
| Returned / scheduled | 8/8 | 8/8 |
| First-pass returned | 8 | 8 |
| Withheld / repairs / retries | 0 / 0 / 0 | 0 / 0 / 0 |
| Actual completed model calls | 8 | 8 |
| Source membership / prose-ID check failures | 0 / 0 | 0 / 0 |
| Case identity check failures | 1 | 0 |
| Median analyzer latency | 94.249 s | 117.012 s |
| Total analyzer latency | 767.571 s | 909.107 s |

Latency increased; neither sampling nor load is controlled enough to isolate the
cost of a particular treatment component. Passing machine checks do not establish
event entailment, source applicability, supported classification or policy truth.

| Manual dimension | Untreated present / ambiguous / absent | Treatment present / ambiguous / absent |
| --- | ---: | ---: |
| Incorrect incident classification (five SOC returns) | 2 / 1 / 2 | 2 / 2 / 1 |
| Unsupported factual claims (eight returns) | 5 / 3 / 0 | 3 / 4 / 1 |
| Unsupported authority/policy claims | 0 / 1 / 7 | 1 / 1 / 6 |
| Benign/negative-control false-positive concerns | 0 / 1 / 7 | 1 / 1 / 6 |
| Positive-control information lost | 0 / 1 / 7 | 0 / 0 / 8 |
| Source applicability concerns | 3 / 1 / 4 | 3 / 1 / 4 |

Dimensions overlap and are not a composite score. False-positive labels must be read
in case context, not as an estimated population error rate. Neither phase withheld
an output, so availability does not hide semantic changes. The factual-present count
falls, but ambiguities and new regressions remain; body-level authority concerns
increase. One unseeded trial per case cannot establish statistical reliability or
causal benefit of a particular change. Assistant review is not independent adjudication.

Improvements: the contextual-note case keeps its canonical case ID and explicitly
denies execution of the quoted example; authentication retains the exact same-user
two-failure/one-success sequence and loses the wrong private-IP interpretation;
LSASS intent and exact hash remain, with no unsupported Persistence inference;
the approved deletion action is now explicit in summary with its named approval
and unknown completion. EC-35/quarterly scope and low-impact public controls remain
recognizable. All legacy governance cited-source relevance is application-owned
guidance provenance with no model-authored authority/implementation assertion.

Residuals and regressions, not fixed by this sprint:

- A lone connection receives an unsupported C2 mapping after authentication noise
  is removed. Better ranking-query isolation does not prove better inference.
- Training notes still receive unsupported Initial Access mapping and supplied
  notepad command-line details are described as missing.
- Authentication's Brute Force Attempt title is stronger than the qualified body.
- Dump analysis contains stronger-than-conditional isolation advice and partly
  applicable PowerShell-specific guidance; no action was executed.
- The approved exercise's Scheduled Maintenance label and process-parent wording
  remain ambiguous; PowerShell-like source attribution is unsupported.
- Public informational governance calls minimal logging required without an
  applicable mandate. Metadata protection does not validate the body.
- The quarterly charter response claims requirements are met without implementation
  evidence. A supported obligation is not evidence of compliance.
- Unverified directive wording, formal-classification gaps, review adequacy and
  policy applicability retain ordinary ambiguity.

## Validation, checkpoints and maturity

Final local Windows gate: **1,668 passed**, one existing Starlette/httpx deprecation warning, 66.96 seconds. Uncached Ruff, pip check and diff checks passed. Thirteen targeted artifact/comparison/preservation checks also passed. Final exact-SHA hosted CI and the immutable mini-sprint closeout commit are reported in the handoff/Sprint 4 provenance, since this document cannot embed its own eventual commit hash.

The initial treatment commit's hosted tests passed (1647 passed, 11 Windows-only
skips), but hosted Ruff caught a blank line between first-party imports in a new
test. Commit `5353c23` corrected that test-only issue; final local Ruff runs use
`--no-cache`, and exact final hosted CI is verified separately. No application or
frozen evaluator change was made to accommodate CI. Earlier cached local Ruff
success is not substituted for the final hosted result.

| Checkpoint | Work |
| --- | --- |
| 4baae12 | Fresh suite/rubric/plan/runner freeze before outputs |
| 75afea1 | Narrow source authorization and 242-path preservation |
| 4ce84ca | Complete untouched baseline and pre-treatment review |
| 7b81356 | Microsoft evidence-only query boundary and backend controls |
| b9b1a24 | Governance authority/provenance and bounded Microsoft interpretation |
| 1a93124 | Offline paired accounting and first regression preservation |
| 5353c23 | Hosted test-import grouping correction |
| 9c8f288 | Checkpointed treatment review through credential-dumping control |

| Maturity question | Assessment |
| --- | --- |
| Microsoft retrieval contamination corrected? | Yes for tested adapter/routing-ID contamination; no universal relevance/negation claim. |
| Authentication positives preserved? | Yes, in legacy/lexical/coded-table tests and the live same-user authentication control. |
| Unverified guidance authority protected? | Application-owned source metadata and framing; body-level mandatory-control claims remain possible and regress here. |
| Supported organizational requirements preserved? | EC-35 quarterly obligation remains scoped; the separate already-met claim is unsupported. |
| Factual inference overclaiming reduced? | Fewer present labels in this tiny paired sample, with new C2/compliance regressions and more ambiguity; not broadly resolved. |
| Positive-control losses? | No identified treatment loss; baseline destructive-action coverage ambiguity improves. |
| Any regressions? | Yes: C2 classification, unsupported logging requirement and charter-compliance claim; all retained. |
| Ready for full held-out support/abstention experiment? | Yes as separately authorized research with source/claim provenance and positive controls; no default activation justified. |
| Microsoft feature release-ready? | No: semantic defects, independent review and user visual QA remain outstanding. |

No Computer Use, browser/headless automation, screenshots or graphical interaction
was invoked in Mini-Sprint 3.5. No external AI calls, new dependency, registry change,
new workflow, default retrieval migration, connector, demo infrastructure change or
automatic containment was introduced. Main/v2.3.0 remain unchanged. No merge/tag/release.

Next major scope: the separately authorized Sprint 4 held-out relevance/support
experiment, conservative provenance-aware assessment and an analyst Evidence Inspector;
do not label model-proposed support as verified. Recommend GPT-6.1 Sol, high reasoning
effort for the engineering work, as judgment informed by
[model selection](https://developers.openai.com/api/docs/guides/model-selection) and
[reasoning-effort guidance](https://developers.openai.com/api/docs/guides/deployment-checklist).
This recommendation does not change the application's local qwen model.

## Exact files changed

```text
Documentation/37_evidence_grounding_stabilization.md
Documentation/grounding_stabilization/.gitattributes
Documentation/grounding_stabilization/baseline.json
Documentation/grounding_stabilization/baseline_manual_review.json
Documentation/grounding_stabilization/baseline_provenance.json
Documentation/grounding_stabilization/comparison.json
Documentation/grounding_stabilization/manual_comparison.json
Documentation/grounding_stabilization/query_controls.json
Documentation/grounding_stabilization/treatment.json
Documentation/grounding_stabilization/treatment_manual_review.json
Documentation/grounding_stabilization/treatment_provenance.json
Documentation/grounding_stabilization_preservation.json
app/governance_analyzer.py
app/prompts.py
app/reference_authority.py
app/soc_analyzer.py
app/soc_query.py
evals/grounding_stabilization/.gitattributes
evals/grounding_stabilization/__init__.py
evals/grounding_stabilization/cases.json
evals/grounding_stabilization/comparison.py
evals/grounding_stabilization/freeze.json
evals/grounding_stabilization/plan.json
evals/grounding_stabilization/rubric.md
evals/grounding_stabilization/runner.py
tests/test_grounding_artifacts.py
tests/test_grounding_comparison.py
tests/test_grounding_mini_evaluation.py
tests/test_grounding_preservation.py
tests/test_grounding_queries.py
tests/test_guidance_authority.py
tests/test_retrieval_artifacts.py
```
