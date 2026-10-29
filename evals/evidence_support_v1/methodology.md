# Evidence support v1 frozen methodology

Fresh independent synthetic corpus and queries. Four existing rankers, same K=5,
eligibility before ranking and default hybrid RRF=60. No new backend, score threshold,
post-outcome calibration or production default change. All grants come from fixture
query metadata. Source/query text cannot upgrade authority or access. Existing local
embeddinggemma produces exact cached-vector replay; no network/model in pytest.

Freeze expanded corpus, cases, registry fixture, judgments, plan, generator and runner
before candidate outputs. Gold relevant IDs mean eligible topical evidence; a related
reference need not support the claim. Required evidence groups are OR within each
group and AND across components. Empty groups deliberately represent unsupported
components. Several gold positives use alternative sources or complementary chunks.
The natural-prose positive deliberately tests coverage beyond structured assertions.

Keep raw ranking separate from support decisions. Rankers do not themselves assert
factual support. A diagnostic any-hit support heuristic may be compared explicitly;
its false-support count is not a count of generated hallucinations or production
behavior. Candidate support is evaluated separately against frozen gold judgments.
An exact record assertion establishes what that record says within its trusted scope,
not independently verified real-world truth. Unverified/self-described policy cannot
establish an organizational mandate. Requirement and implementation are distinct.

Metrics remain separate: eligible relevant Recall@5 (nonempty gold relevant set),
support-sufficient Recall@5 (gold full-support cases, all groups reached), required
group recall (nonempty groups), no-answer/partial/conflict handling, false support
(full-support decision on non-full-support gold), false abstention/positive loss
(no full-support decision on full-support gold), eligibility/authority/scope/version
violations and latency. Report denominators and category counts. No composite score,
no universal ranking superiority claim and no statistical confidence from this suite.
An abstention can be safe but still lose a valid prose answer; do not hide that cost.

Contradictions require comparable assertions with different values within eligible
current scope; never silently reconcile. A conflict may be missed if a ranker omits
a conflicting source. Report this as a candidate coverage limitation. Corpus-level
gold is not passed into the application assessor. Discovered judgment errors go into
a separate errata ledger without changing the frozen original comparison.
