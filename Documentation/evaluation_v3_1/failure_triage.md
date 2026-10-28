# Semantic Evaluation V3.1 failure triage

Evidence: [official baseline](semantic_baseline_3trial.json), [all 39 manual reviews](manual_review.md), [JSON ledger](manual_review.json), [expectation check](expectation_check.json), [calibration diagnostic](v3_diagnostic_rescore.json), [methodology](../14_semantic_evaluation_v3_1.md).

Official result: **37/39 (94.9%)**, two assertion failures and zero application errors. Both scored failures are suspected false positives under direct manual inspection. Two passing trials have missed consistency/support-scope defects, one at moderate confidence. A separate malformed IP in an excluded investigation step is a high-confidence unscored output defect. No corrected aggregate replaces official scoring.

## Confirmed application defects

| Case/trial | Authoritative scenario facts | Actual response evidence | Official result / manual assessment | Likely future layer | Confidence |
| --- | --- | --- | --- | --- | --- |
| V31-GOV-005 / 3 | Fictional statute explicitly establishes weekly audits | key_risks: Weekly security audits mandated by fictional statute lack real-world regulatory basis; evidence_gaps: Audit frequency and methodology unspecified | PASS; the frequency is known, so calling it unspecified is a factual/missingness contradiction. The method may be unspecified, but the frequency is not. | Retain established governance facts consistently across summary, controls and gaps | high |
| V31-SOC-009 / 3 | Supplied authentication IP is 192.0.2.51 | recommended_investigation_steps: Verify if IP 19.2.0.2.51 is authorized for maintenance | PASS; malformed copied referent in an excluded question field. This is not a failure of the configured four-field IP checker. | Reference-bound fidelity for proposed steps; distinguish copied evidence targets from illustrative hypothetical values | high |

### Suspected application support-scope defect

V31-SOC-009/1 states the signed maintenance approval in observations and approved maintenance in summary, yet inference says Successful authentication without clear authorization context. The scenario explicitly supplies a signed approval for this exact activity. This appears to understate established within-scenario support, but could mean unstated real-world/operator verification rather than a denial of fictional approval. It is therefore a **moderate-confidence suspected consistency miss**, not a certified authentication reversal. Future layer: explicit scope of established facts versus operational caveats.

### Other unscored rationale concern

V31-GOV-003/3 infers no actual data handling and minimal risk from the synthetic setting. The input establishes synthetic documents/users, not zero processing or automatically negligible governance risk. This is a moderate-confidence rationale concern outside the two obligation facts. Approval/risk correctness is not scored; no new risk answer key is invented retrospectively. Other taxonomy/address-purpose statements remain scope notes, not counted as certified defects.

## Evaluator false positives

| Case/trial | Authoritative fact | Response claim | Failed check | Manual assessment / future evaluator layer | Confidence |
| --- | --- | --- | --- | --- | --- |
| V31-SOC-007 / 1 | process_execution=false; launch blocked before creation | analyst_inferences: The attempted PowerShell execution may indicate an adversary's attempt to execute malicious code | fact_grounding | Attempted PowerShell execution is not confirmation of execution; may modifies a possible implication, and the attempted state must remain attached to the event noun. Future: Next versioned evaluator event-state calibration | high |
| V31-SOC-008 / 2 | maintenance_authorized=false; user claim unverified | analyst_note: The observed evidence suggests potential unauthorized account creation without proper authorization. However, the user's claim about approved maintenance requires verification. The absence of change approval records raises concern but does not confirm compromise. | fact_grounding | The user's claim about ... requires verification is not an assertion of approved maintenance. Future: Next versioned evaluator attribution and suffix-qualification calibration | high |

Both outcomes are correct executions of the frozen lexical rules, but poor semantic classifications. Attempted is not a completed execution state; the user's claim about ... requires verification is not adopted approval. No scorer is tuned after observing these results. Resolving these residual families requires another separately versioned evaluator experiment.

## Evaluator false negatives

| Case/trial | Key / actual claim | Validator result | Review | Future layer | Confidence |
| --- | --- | --- | --- | --- | --- |
| V31-GOV-005 / 3 | Audit frequency is explicitly weekly, not unspecified. A statement that a known fact is missing is not recognized as a contrary proposition. | PASS; positive presence found, contrary missingness/context phrase not modeled | Key risks acknowledge weekly audits mandated by the fictional statute, but evidence_gaps says audit frequency is unspecified and summary calls compliance requirements unspecified. The input explicitly establishes a weekly frequency. Positive recognition passes while the known-value-versus-missing-value contradiction escapes the fact and consistency rules. | Cross-field consistency and retention of established governance facts | high |
| V31-SOC-009 / 1 | The within-scenario signed approval provides authorization context, yet inference calls that context unclear without qualifying its scope. | PASS; positive presence found, contrary missingness/context phrase not modeled | The positive authentication, execution and maintenance statements are present, but inference says successful authentication is without clear authorization context despite the signed synthetic approval for this exact activity. This is a suspected support-scope/missing-context contradiction. It could reflect unstated real-world caution, so confidence is moderate rather than claiming a definite event reversal. | Support-scope communication and consistency with established evidence | moderate |

There are **2/39 reviewed trials with suspected false-positive failures (5.1%)**, and **2/39 with suspected missed within-key defects (5.1%)**, one of those moderate confidence. These are sampled assistant-review diagnostics, not formal precision/recall, independent ground truth, or an adjusted success rate. The high-confidence investigation-step IP defect is reported separately because that field was deliberately excluded from observable scanning.

## Calibration improvements compared with V3 manual-review classes

- Non-official same-output diagnostic: 7/7 known high-confidence false-positive checks resolved; 4/4 eligible high-confidence IP/port misses detected; 3/3 supported-actor omissions remain failures. No replacement V3 aggregate is published.
- Historical SSH is not adjudicated retroactively: V3 lacked an explicit protocol fact. V3.1 uses an explicit unknown key and a known-HTTPS positive control.
- Fresh authority category: 15/15 passes, with no identified authority-promotion defect in its nine negative trials; both authority positive controls state their supported facts. This does not prove universal attribution accuracy.
- Fresh positive controls: 12/12 passes. Actor omissions do not recur, but completeness is not weakened; diagnostics and generic-entity tests retain the failure class.
- Every applicable SOC case has the required four-field token coverage. New IP/port mutations do not recur in those fields, so live sensitivity is not inferred from their absence. A mutation recurs in an excluded investigation step.
- Three explicit HTTPS endpoint trials preserve source/destination roles, port 8443 and known protocol. Unknown-protocol cases retain uncertainty in measured fields.

The V3.1 94.9% and V3 75.0% are not directly interchangeable. Case text, fact metadata, checks, inventory and sampled outputs differ. Production is unchanged, so no product-hardening improvement is claimed.

## Remaining semantic-evaluation blind spots

1. Attempted event noun phrases and possessive noun-claim constructions can still look assertive. Local modifiers and uncertainty scopes remain incomplete.
2. A value can be affirmed in one field while another says it is unspecified or lacks context; positive recognition is not universal consistency.
3. Questions/recommendations can copy an observed identity incorrectly even though most such text should not be scanned indiscriminately for novel hypothetical values.
4. Taxonomy, source/entity roles in arbitrary prose, event counts/order, data-handling assumptions, address-purpose explanations and real-versus-synthetic scope are not general truth checks.
5. Endpoint roles/pairs and port syntax are bounded. Protocols are measured only where explicit metadata exists. Unknown tuple members are not required or generally adjudicated.
6. Token checks permit omission, miss corruption outside defined shapes/similarity bands and do not establish arbitrary semantic entailment. Three unseeded trials provide preliminary variability, not statistical confidence.

## Repair and availability

There are **39 initial generations and three existing repairs: 42 completed raw calls**, zero failed raw calls, zero transport/JSON retries and zero application errors. Repairs occur at V31-SOC-006/1, V31-SOC-006/3 and V31-SOC-009/2. All restore the observation contract and have clean final measured factual fields. Repair-generation time totals **170.8521 seconds**. This does not prove future repair availability or whole-output fidelity; the separate investigation-step mutation remains.

## Recommended production-hardening targets: not implemented

1. **Reference-bound observable fidelity in proposed steps**, with whole-output/repair postconditions scoped to actual copied evidence identities. V31-SOC-009/3 provides direct high-confidence evidence of a malformed target in a question. Preserve legitimate hypothetical examples and avoid an indiscriminate recommendation scanner. Historical diagnostic IP failures remain supporting evidence, not newly observed four-field failures.
2. **Retain established facts consistently when stating missing information.** V31-GOV-005/3 acknowledges weekly audits and then says frequency is unspecified. A general known-fact-versus-gap boundary is better supported here than forcing benchmark phrases or changing legal conclusions.
3. **Communicate support scope explicitly.** V31-SOC-009/1 suggests missing authorization context despite a signed synthetic approval, with moderate confidence; V31-GOV-003/3 overextends synthetic context into a low-risk/no-data rationale. Separate established scenario facts, external applicability and remaining operational questions. This priority is less certain than the first two and needs a bounded diagnostic design before any control.

No new live supported-actor omission, measured-field IP/SHA/port mutation or unsupported protocol addition is observed; do not manufacture a production failure or declare the historical weakness fixed. Follow-up actor/protocol hardening remains a hypothesis supported by historical/calibration evidence, not a new V3.1 failure count.

Measurement work should first version residual attempt/claim and missingness families, preserving this V3.1 score and all older artifacts. Any production treatment requires separate authorization and an exact V3.1 rerun. Nothing in this backlog authorizes implementation.
