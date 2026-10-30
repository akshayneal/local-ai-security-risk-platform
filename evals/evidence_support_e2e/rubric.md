# Fresh end-to-end inspection diagnostic

Eight new cases, one candidate trial each, maximum eight scheduled calls here (within
Sprint 4's maximum 24). Existing bounded SOC repair/transport retries remain counted
separately. No selective reruns. qwen3:8b, temperature 0.1, unset seed, legacy default,
no shadow; Microsoft native complete-context 8192 unchanged. Freeze before output.

This is a direct call through the UI API route functions with audit persistence
replaced by a counting sink. No HTTP/browser server, UI automation or extra generation
is required. It exercises the original analyzer and additive actual-retrieval capture.
No baseline generation comparison is required: prompts/analyzers and generation
behavior remain byte-identical to the closed mini-sprint. Do not claim reduced
unsupported-claim rate from this passive integration or reuse archived outcomes as
fresh held-out trials.

Record every returned/withheld case, exact request hash, actual model requests,
repair status, latency, source selection/citation, source authority, inventory and
claim support provenance. Deterministically verify source membership, canonical
identity, one audit outcome, unassessed/not-verified model claims, and retained
workflow metadata. These checks do not score semantic truth.

Manual dimensions: unsupported factual/inference claim, unsupported policy/authority
claim, material positive-control information lost, source applicability concern,
benign/uncertain-control false positive. Label absent/present/ambiguous; withheld
outputs unassessable. Quote exact fields with rationale/confidence. Preserve supported
facts, scoped authority, cadence and supplied approvals without inventing completion,
compliance, protocol or maliciousness. Distinguish recommendation/hypothesis from
incident characterization. Review every output including strong positives. No
category-only answer key or composite score; assistant review is not independent
human adjudication and single trials do not establish statistical reliability.
