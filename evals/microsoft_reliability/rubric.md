# Frozen v1 review rubric

Cases, truth conditions and scorer are committed before viewing fresh model results.
Each case declares supported facts, unsupported claims, known unknowns, admissible
alternatives and deterministic contracts. Each attempt, including errors, is kept.
One trial is diagnostic; three unseeded trials describe only preliminary stability.

Machine coverage is a lexical **review flag**, not semantic entailment: any token
in each declared group must occur in summary or observed evidence (governance:
summary/risks/controls). Missing groups require manual review. A negated command
can match, a faithful paraphrase can miss. Do not reclassify these flags as truth.
Do not require repetition of mundane fields or prescribe Low/Approved categories.

For every returned response, separately label material omission, unsupported factual
claims, unsupported authority/policy claims, disproportionate severity/overclaiming,
and source applicability as present/absent/ambiguous. Record exact response quotes,
case support, rationale and confidence. Hypotheses/recommendations are not automatically
facts: examine whether they are explicitly bounded, relevant and proportionate.
Credential-theft mapping without evidence is an unsupported inference even when
phrased as possible if presented as the incident characterization. Proposing a
conditional check for credentials alone need not be an unsupported factual claim.
Deletion commands establish recorded attempts, not success, ransomware or theft.
Public read-only systems can have accuracy/availability risks; invented sensitive
data or employment impact is unsupported. Read-only HR systems retain privacy risk.
Meaningful affirmative approval differs from auto-send unless vetoed. Keep scoped
organizational requirements and known retention distinct from external verification.
Framework relevance does not prove applicability or establish mandatory obligations.

Withheld responses count against availability. Their semantic properties are
unassessable, never passes. Separate quality among returned responses from attempt
denominators. First-pass validity requires an accepted generation 0; repair rate
counts requests attempting generation 1; post-repair validity uses repairs as its
denominator. Transport/JSON retries are separate from policy repairs. Report each
metric separately and per-case repeat outcomes; no opaque overall score.

Freeze suite byte hashes (LF source bytes), semantic case hash, plan/rubric/scorer
hashes and commit before baseline. Before/after comparisons require exact identity,
trial schedule, settings and case requests. Production changes must not change the
truth conditions or scorer. Manually record ambiguities without scorer tuning.
Review by this implementation assistant is not independent human adjudication.
