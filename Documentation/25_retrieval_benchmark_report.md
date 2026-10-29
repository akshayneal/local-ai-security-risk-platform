# Retrieval benchmark (expansion sprint 1)

Independent retrieval evaluation v1, not a model-output or historical semantic
evaluation. Fixed corpus: 74 records = 26 existing curated cards plus 48 synthetic
records (36 versioned document chunks and 12 distractor notes). Fixed cases: 48,
all K=5: exact identifiers 8, semantic paraphrase 8, workflow 6, authority 6,
version/validity 6, access 6, poison/noise 4, positive controls 4.

All synthetic policies, vulnerabilities and requirements are fictional exercises.
The current/obsolete audit-retention pair shares document identity with distinct
content versions. Similar wrong CVEs/controls/tasks remain eligible distractors;
they are not artificially security-filtered to make ranking easy. Access, scope,
authority, date and workflow constraints use the common deterministic filter.

Judgments list required IDs, graded relevant/acceptable IDs and forbidden IDs.
Recall@5 uses all positive judgments, required recall is separate, MRR is first
positive reciprocal rank, NDCG@5 uses graded gain `2^grade-1`. Every case currently
has at least one positive; this suite does not measure unanswerable-query abstention.
Scores use authored keys, never an LLM. Narrow judgments can miss other useful
evidence; no enterprise generalization or statistical confidence is claimed.

Candidate filtering violations are counted separately: access, stale/failed/version,
workflow, authority/policy scope, applicability, validity, source type, and explicit
forbidden judgments. The control wraps the original keyword/tag ranking with the
same new eligibility layer as candidates. Thus security results establish the new
common layer, not retrospective ACL capability in the released application.

One poison case deliberately admits unverified material and expects that record;
retrieval does not detect arbitrary malicious instructions or establish truth.
Other policy-authority queries must exclude it. No benchmark-only production filter
or semantic-judgment oracle is implemented.

## Lexical checkpoint

The tracked `retrieval_evaluation/lexical_checkpoint.json` records full rankings,
scores, metadata, metrics, source/fixture hashes, runtime provenance and timings.
Both candidates use exactly the same cases. Lexical improves first-hit ranking
without improving aggregate recall; all eight violation counters are zero for both.
Final four-candidate results and architecture decision are added after the local
dense/hybrid experiment. Generation model calls and historical suite reruns: zero.
