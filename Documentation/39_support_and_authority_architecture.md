# Support and authority architecture

The reusable contract separates candidate evidence, exact structured record support,
model-proposed conclusions and analyst judgments. It preserves the four existing
authority classes. No confidence percentage, generic entailment classifier or second
model call is introduced. Legacy remains the selected backend.

`app/support_contracts.py` defines typed claim components (observation, inference,
hypothesis, recommendation, requirement, implementation or unknown), candidate/source
identities, scope/version/authority provenance, relationship, assessment origin and
verification status. Every assessment requires human review. A model/manual proposal
cannot carry deterministic record-verification status. Citation membership is not
proof of applicability or entailment.

`app/support_assessor.py` implements a deliberately conservative primitive. It checks
existing workflow/access/policy/date/currentness eligibility again before exposing
candidate IDs. Document-version records require an explicit trusted registry gate;
without it they are withheld from assessment, rather than trusting an old status
label. Query/source text cannot grant scopes. No data is passed to another model.

Within eligible sources, a bounded JSON assertion format can match exact subject,
predicate, kind and typed value. Boolean/integer/string coercion is forbidden.
Duplicate JSON fields, malformed or oversized structures provide no machine support.
Observation claims need a case-observation or inventory source type; operational
guidance cannot establish an event. Requirements need organizational-policy authority
and the applicable single/explicit scope. A policy requirement does not establish
implementation; that needs a separate implementation/case record assertion.
Recommendations can be supported as recommendations, without becoming mandates.
Inference/hypothesis/unknown components are not automatically proven by this primitive.

Complementary component matches produce partial support; disagreeing comparable
current assertions produce conflict. No silent reconciliation. Candidate omission can
still hide a conflict: the contract reports support **within eligible retrieved
candidates**, not proof of corpus completeness. Different authority/scopes are not
made equivalent by ranking or a shared word.

An exact match means that an eligible record contains that typed assertion within
its supplied scope. It does not independently verify a real incident, organization,
legal applicability or implementation. Natural-language sources without the bounded
format remain unassessed/insufficient for this primitive, even when a human can see
valid support. The held-out natural-prose positive measures that false-abstention
cost. Source assertions and metadata remain separate; self-described authority in
the JSON payload never overrides application-owned record metadata.

The frozen benchmark gold judgments never enter these modules. Its offline runner
passes only the requested claim, trusted query context and actual candidate records.
The same contract will support an additive, read-only workflow Inspector: model text
will retain explicit proposed/unassessed provenance instead of being silently
converted into structured facts. Production analysis/schema/repair contracts remain
unchanged; no semantic enforcement is activated by this component.
