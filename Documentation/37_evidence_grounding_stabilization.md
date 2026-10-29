# Mini-Sprint 3.5: evidence grounding and authority stabilization

Start: clean `feature/microsoft-evidence-reliability` at
`73fd92cb8445ac39beab50ee13b8b47c5aa09e47`. Work uses child branch
`feature/evidence-grounding-stabilization`. This is a bounded stabilization sprint,
not Expansion Sprint 4 or a release. Terminal/repository/test/Git tools only;
**USER VISUAL QA PENDING**. No desktop/browser control is authorized or used.

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

Results and final validation will be recorded after the two once-only phases.
