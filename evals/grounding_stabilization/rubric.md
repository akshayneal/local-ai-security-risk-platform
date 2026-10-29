# Grounding stabilization mini-evaluation v1

Eight fresh synthetic cases; one untreated and one treatment trial each. Maximum
16 live case trials, excluding existing bounded internal repair/retry generations.
Never selectively rerun. Record every failure; withheld outputs are unassessable,
not semantic passes. No statistical reliability or composite score.

Before live outputs, freeze cases, this rubric, plan and runner source hashes plus
semantic case hash. Preserve actual retrieved IDs and query hash from the analyzer,
not a reconstructed historical query. Baseline production must match Sprint 3;
commit treatment before its run. Same case order, requests, qwen3:8b, temperature
0.1, unset seed, legacy default, no shadow; Microsoft native complete-context 8192.

Deterministic checks: schema accepted, source IDs belong to actual retrieved set,
no source IDs in ordinary fields, case/system identity exact, existing SOC policy
checks remain the production authority. No lexical semantic pass/fail scorer.

Manually label each returned output separately: incorrect incident classification,
unsupported factual claim, unsupported policy/authority claim, benign-control false
positive, positive-control information lost, and source relevance/applicability
concern. Use absent/present/ambiguous with exact quotes, case support and rationale;
withheld is unassessable. Recommendations/hypotheses are not automatically factual
claims; unsupported incident labels or MITRE classifications still count as inference
defects. Distinguish implementation verification from denial of supplied facts.
Do not penalize a category alone or demand every mundane field be repeated.

Scoped charter obligations must remain named and preserve cadence, without acquiring
new scope. Guidance-only recommended safeguards in required_controls need explicit
proposal framing; do not equate that schema field's name alone with a legal mandate.
Evaluate the whole returned response including source relevance prose. Compare common
returns separately from availability gains/losses. Preserve prior review judgments;
document any corrections explicitly. Review by the implementation assistant is
unblinded and not independent human adjudication.
