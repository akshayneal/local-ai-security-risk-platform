# Independent human review guide

Status: **INDEPENDENT HUMAN REVIEW PENDING (0 completed)**. This guide and the
blank record template prepare review; they contain no completed human judgments.
Implementation-author analysis, automated scoring and another coding agent are
not independent human adjudication. USER VISUAL QA remains PENDING.

Use the unchanged [Sprint 13 masked packet](../adaptive_security_reasoning_v1/review_packet.json).
Its SHA-256 is
`e4d43c986d086c1d3d2d7d7fd65775eca8251b433b6b089d51f14b5f421452d1`.
It contains 60 outputs across 36 synthetic cases: 24 model replies, 12 saved
deterministic development projections and 24 saved deterministic diagnostic
outputs. Generator, phase, linkage and authored answers remain in a separate key.
Style may reveal the generator; masking does not guarantee blindness.

## Before review

Use a separate copy of [adjudication_template.json](adjudication_template.json).
Keep the packet, original outputs, IDs, sources, hashes and separate key unchanged.
A real reviewer may fill their identity, relevant role, date and independence
declaration; leave these empty until that person supplies them. Do not enter real
incident data or confidential institutional information. Read this guide and the
packet before opening the concealed key. Record any prior key exposure honestly.

## Per-output procedure

1. Locate the `review_id`. Read the exact `original_canonical_input.raw`, reviewed
   context, scoped question and field/JSON pointers. Before judging the proposed
   answer, determine which relationship the supplied assertions support. Literal
   source assertions and review metadata do not authenticate a real permission,
   organization policy, deployed control or executed action.
2. Record your independently determined scoped verdict and rationale. Distinguish
   declared alignment, declared mismatch, underdetermined, conflicting claims,
   not applicable and projection unavailable. An unsuccessful attempt is not a
   completed action. Missing, unknown, proposed and reported implemented differ.
   If the question or schema cannot support a unique answer, explain ambiguity.
3. Identify decisive support and disconfirming evidence using exact premise IDs,
   source paths and values. Check association: same event, principal, resource,
   action, relevant time and selected tool. Matching names or IDs alone do not
   prove entailment, causation, implementation or eligibility.
4. Read `unverified_interpretation`. Assess factual fidelity, mechanism, scope,
   authority claims, implementation claims, before/after timing and result state
   separately from its verdict label. A correct label may have a wrong rationale.
   Note omitted decisive counterevidence and unsupported high-impact claims.
5. Evaluate whether suggested verification is relevant, conditional and useful.
   A recommendation does not authorize execution. Record missing evidence,
   unresolved ambiguity and disputed wording. Explain whether a claimed policy,
   approval or control is merely supplied, reviewed for eligibility, or actually
   evidenced; do not invent confirmation.
6. Record confidence in **your own review**, with a reason and unresolved limits.
   This is not a model accuracy or safety percentage. Use low/medium/high or leave
   unknown; do not infer a model confidence score.

Complete and preserve these initial judgments before opening the separate key.
Then record any disagreement with the authored rubric/gold in a separate field,
including an alternative verdict and supporting evidence. Do not change the
frozen key, original output or your initial judgment to improve agreement.
Corrections to the review itself need a dated append-only amendment and reason.

## Recording completion

Each item starts `review_status: null` with all judgments empty. Mark an item
completed only when an identifiable independent human has actually reviewed it.
Count completed records from supplied reviews; preparing 60 blank records does
not count as 60 reviews. Keep partial review, inability to assess, dissent and
prior exposure visible. A later ingest/checker should validate IDs and packet
hash and preserve the supplied human record; none is implemented by this guide.

Printable checklist: scoped verdict; decisive and disconfirming paths; source
authority; implementation state; event/outcome; timing; factual fidelity;
missing evidence; unsupported rationale; useful conditional verification;
ambiguity/disputed gold; own confidence/reason; human identity/role/date.
