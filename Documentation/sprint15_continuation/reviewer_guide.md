# Human reviewer guide

**INDEPENDENT HUMAN REVIEW PENDING (0 verified). USER VISUAL QA PENDING.**
This printable guide prepares review. Agent analysis and implementation-authored
tests are not independent human adjudication. The local application does not
authenticate a reviewer or provide an enterprise approval workflow.

Use a separate copy of the [blank form](reviewer_form.md). A real reviewer fills
their identity, relevant experience, date and independence declaration. Keep
these and every judgment blank until supplied by that person. Use synthetic
examples only; do not add confidential or real incident data.

## Artifact identity

- Unchanged [Sprint 13 masked packet](../adaptive_security_reasoning_v1/review_packet.json),
  SHA-256 `e4d43c986d086c1d3d2d7d7fd65775eca8251b433b6b089d51f14b5f421452d1`.
  The existing [packet review guide](../evidence_qualification_v1/reviewer_guide.md)
  explains its 60 outputs and limitations of masking. Preserve its IDs, originals
  and separate key. Do not open the key before recording initial judgments;
  disclose prior exposure.
- Current continuation: record the exact Git commit with `git rev-parse HEAD`,
  the upload's byte SHA-256, selected row, request fingerprint and downloaded
  JSON/Markdown hashes. Use the committed synthetic
  [network sample](../../sample_data/native_evidence/network_observation.json).
  Consult the [checkpoint](checkpoint.md) and [semantic decision](native_semantics.md).
  A source tip identifies code; it is not an invented final artifact hash.

## Review procedure

1. Read exact source values and selected row before the readout. Which claims are
   literal observations, representation checks, comparisons or unsupported
   conclusions? Can you locate each decisive field without relying only on a hash?
2. Check original/normalized values and JSON types. Are absent and malformed
   values unknown? Are Local/Remote roles preserved? Does any text quietly turn
   ConnectionSuccess, a port, a PID or a familiar name into successful access?
3. Check association and ambiguity. Does selecting another row change every
   relevant path? Are duplicate rows, different process creation times and other
   supplied tables visible without becoming a causal join? Does missing material
   imply absence of an event anywhere outside the submitted bundle?
4. Assess the investigation questions. Are they justified by supplied fields or
   the stated question? Do they identify concrete missing corroboration without
   claiming a source was checked or an integration exists? Would a new analyst
   understand what to collect next?
5. Challenge authority boundaries. Does forged approval text remain inert?
   Are suggested investigations separate from authorization and executed actions?
   Is independent policy evidence still required for a permission question?
6. Check exports against source and current selection. Mutated or stale results
   should be withheld. Record misleading wording, missing counterevidence and
   UI hierarchy problems separately from whether a deterministic test passes.

For historical packet items, record an initial judgment before consulting the
separate key, then record disagreements separately. Never edit frozen gold or
earlier judgments to improve agreement. For current artifacts, review source,
unknown states, usefulness and misleading implications without inventing a
numerical safety score.

Return a completed copy of the form through the user's chosen channel, with
artifact identities and concrete supporting/disconfirming paths. Keep partial
reviews and inability to assess visible. Later corrections require a dated
append-only amendment and reason. Merely preparing forms counts as zero reviews;
no automatic review ingestion or identity verification is implemented here.
