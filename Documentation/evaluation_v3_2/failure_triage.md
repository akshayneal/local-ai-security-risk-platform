# V3.2 final calibration triage

The frozen official result is **32/42 valid trials passed (76.2%)**, zero
application errors. This is a new evaluator baseline, not a production treatment.
V3 remains 27/36 and V3.1 remains 37/39. Do not substitute manual judgments for
the official aggregate or compare these percentages as a causal improvement or
regression.

All 42 final responses and checks were inspected after the complete report
existed. The [review JSON](manual_review.json) and [readable review](manual_review.md)
retain exact quotes, facts, known-value/scope keys and confidence. This is assistant
inspection, not independent human adjudication.

## Detected application semantic defects

| Trials | Observation | Confidence |
| --- | --- | --- |
| V32-SOC-004/1, /2, /3 | Stipulated actor Fictional Copper Lynx is absent from the entire response; malicious reputation alone does not satisfy supported actor completeness. | High |
| V32-SOC-006/3 | Final repaired response copies 192.0.2.51 as `19,2.0.2.51` in an investigation step. Factual fields are correct. | High |
| V32-SOC-012/3 | Summary says failed SSH login although protocol is explicitly unknown; a later unconfirmed-protocol sentence does not absolve that local assertion. | High |
| V32-GOV-014/1 | Weekly cadence is retained but scenario authority/legal mandate is omitted; response also says no established legal/compliance framework. | High |
| V32-GOV-014/2 | Both legal mandate and weekly cadence disappear; unknown methodology and external applicability do not justify their omission. | High |
| V32-GOV-014/3 | Weekly audits are retained; legal mandate is not affirmed in measured fields. Q-24 appears only in a proposed methodology step. | Moderate; indirect Q-24 requirements mention permits another reading |

These are eight reviewed genuine semantic-failure trials under the bounded keys,
with seven high-confidence and one moderate-confidence judgment. They are not
application/runtime exceptions. Supported event facts and HTTPS still pass their
positive controls. Positive-control case trials are **9/15**; this is separate
from **20/27 positive fact checks** and **3/3 positive protocol checks**.

The investigation identity failure is a fresh live trigger for the new scope.
Four existing repairs completed: V32-SOC-006/2, /3 and V32-SOC-009/2, /3.
All restored the application observation contract, but the final response in
006/3 still contains the proposed-step corruption. A successful repair is not a
whole-response semantic guarantee. No repair behavior was changed.

## Suspected evaluator false positives

- V32-GOV-003/2: `Requires verification of legal requirements and audit protocols.`
  is a verification request, not an established legal mandate. The bounded
  verb-first recognizer misses the noun phrase requires verification of.
- V32-SOC-008/1: `The user's claim of authorized maintenance requires validation.`
  reports and qualifies a user claim. V3.2 covers that/about and verification;
  the ordinary of/validation variation escapes both guards.

Both are high-confidence suspected false-positive trials. The four motivating
V3.1 diagnostic transitions remain correct. These new variations are ordinary
residual lexical imperfections: document them, keep official scores, and do not
create V3.3 or tune the frozen scorer because of them. Production controls must
not be engineered to satisfy these erroneous failure reasons.

## Suspected missed and unscored concerns

V32-GOV-005/3 passes officially but an evidence gap says
`No verified legal framework supporting fictional Z-77 obligations`. The summary
retains internal requirements and weekly audits, so this could mean unstated
external verification rather than literal absence of scenario authority. It is
one **moderate-confidence suspected false negative**, with no high-confidence
missed within-key defect identified. Literal subject aliases do not cover every
legal-framework paraphrase; conservative support-scope treatment leaves this
ambiguity for manual review.

V32-SOC-006/2 says `The protocol and authentication method remain unknown` after
supplied failed-password telemetry. This is a moderate unscored missingness
concern: password authentication is provided, while full protocol/MFA details are
not. Authentication method is not an authored known-value key. It is recorded
separately from within-key false negatives.

Other scope notes are not counted as certified defects: V32-GOV-005/1 calls
fictional obligations unverified while retaining mandatory audits; V32-SOC-010/2
calls the destination unknown despite exact endpoint observations, which could
mean unknown owner/reputation; provisional incident types, MITRE labels, general
risk judgments, address-purpose claims, relevance and speculative evasion are
outside these bounded answer keys. No external legal or threat-intelligence
facts are introduced to adjudicate them.

## What the new instrument actually measured

- Both known V3.1 lexical false positives corrected diagnostically: 2/2.
- Known weekly-versus-unspecified contradiction detected diagnostically: 1/1.
- Known proposed-step IP mutation detected diagnostically: 1/1, with a fresh
  comma-corruption failure detected in the live run as well.
- Factual-field fidelity: 42/42 check applications (24 IPv4, 15 port, three SHA).
- Investigation identity fidelity: 41/42 check applications; one genuine IPv4
  corruption. No new port or SHA mutation appears in those proposed fields.
- Endpoint relations: 24/24 check applications. Protocol grounding: 23/24;
  the failed one is the unsupported SSH assignment. Known HTTPS is 3/3.
- Known-value consistency: 39/39 check applications; no new live known-weekly/
  unspecified contradiction occurs. V32-GOV-014/2 omits cadence instead, caught
  by the independent positive-presence check. Do not confuse non-recurrence with
  a production fix.

## Freeze suitability and remaining boundaries

V3.2 is suitable to freeze for the **defined bounded production-treatment
comparison**. No known high-confidence evaluator defect prevents measuring the
planned copied-identity, known-value/unknown-protocol and supported-fact-retention
controls. This is provisional engineering judgment from deterministic fixtures,
diagnostic transitions and exhaustive review, not a guarantee of language coverage.

Known limitations remain: two high-confidence lexical false-positive families;
literal subject aliases and explicit missingness forms; ambiguous support scope;
near-identity length/similarity bounds; distant new identities without case cues;
explicit hypothetical/example exclusions; investigation-only additional identity
scope; and a finite protocol vocabulary. These constrain future claims. A general
whole-output or universal contradiction invariant cannot be established by this
suite. No high-confidence missed defect inside the declared bounded live keys was
identified; that does not prove none exists.

**Stop rule:** no post-live scorer changes, no new grammar family driven by these
outputs, and no V3.3 recommendation for ordinary lexical imperfections. Further
versioning requires an objective defect making the intended treatment scientifically
uninterpretable. Rerun the exact V3.2 suite/scorer and both hashes unchanged after
separately authorized production treatment, with runtime differences recorded.

## Exact next production priorities — recommendations only

1. **Retain authoritative supplied facts and supported identities while stating
   verification scope clearly.** Address actor omissions and loss of fictional
   governance authority/cadence without requiring external validation to accept
   scenario facts. Evidence: 004/1–3 and 014/1–3; 005/3 is a moderate scope concern.
2. **Preserve reference-bound investigation identities through final output and
   repair.** Check copied IP/SHA/contextual endpoint values with protection for
   hypothetical examples and unrelated numbers. Evidence: live 006/3 and frozen
   V31-SOC-009/3; successful observation repair did not protect proposed identity.
3. **Check established values and explicit unknowns for consistent claims.**
   Prevent known values being declared absent and unknown protocols being given
   unsupported specificity. Evidence: frozen V31-GOV-005/3 diagnostic and live
   012/3 SSH assertion. Treat ambiguous support wording conservatively.

These are generic, evidence-driven targets, not benchmark-specific production
filters, automatic architecture approval or permission to implement controls.
No production hardening occurred in this sprint. V1/V2/V3/V3.1 remain frozen.
