# Blank human review form

Template only. No reviewer, completed judgment or signoff is recorded.
Copy this form before use; preserve original artifacts and initial findings.

## Reviewer-supplied identity

| Field | Reviewer entry |
| --- | --- |
| Name or reviewer identifier | |
| Relevant experience / role | |
| Review date and timezone | |
| Independence declaration and relationship to implementation | |
| Prior exposure to code, expected answers or separate key | |
| Review status / items completed | |

## Artifact binding

Historical packet: `Documentation/adaptive_security_reasoning_v1/review_packet.json`

Expected unchanged packet SHA-256:
`e4d43c986d086c1d3d2d7d7fd65775eca8251b433b6b089d51f14b5f421452d1`

| Field | Reviewer entry |
| --- | --- |
| Packet review_id, if applicable | |
| Current continuation exact Git commit, if applicable | |
| Source file / case label | |
| Exact source byte SHA-256 | |
| Selected table and zero-based row | |
| Request fingerprint | |
| JSON export SHA-256 | |
| Markdown export SHA-256 | |
| Other reviewed artifact identities | |

## Initial findings, before separate key exposure

| Question | Judgment, rationale and exact source/field paths |
| --- | --- |
| What does the supplied source establish? | |
| Are source association and row/field lineage correct? | |
| Are original values/types and normalizations faithful? | |
| Are ambiguity, absent/invalid fields and unknowns explicit? | |
| Is any completion, access, causal identity or protection outcome unsupported? | |
| Is any source text misleadingly treated as policy/permission? | |
| What decisive supporting and disconfirming evidence matters? | |
| What corroborating evidence is required? | |
| Are next-investigation questions relevant and useful? | |
| Are stale/mutated inputs and downloads handled honestly? | |
| What wording or visual hierarchy could mislead a new analyst? | |
| Overall scoped judgment and limits / inability to assess | |
| Reviewer's own confidence and reason, if supplied | |

## Subsequent disclosure or amendment

| Field | Reviewer entry |
| --- | --- |
| Separate key consulted: when and which artifact | |
| Disagreement with authored expectations and evidence | |
| Dated append-only amendment, reason and prior finding reference | |
| Reviewer completion declaration | |

This record does not authenticate identity, approve a security action or certify
model/system safety. Keep unresolved disagreements and partial coverage intact.
