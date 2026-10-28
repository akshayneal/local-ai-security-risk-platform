# Semantic Grounding V3 failure triage

Evidence: [official report](semantic_baseline_3trial.json), [all 36 manual reviews](manual_review.md), [structured review](manual_review.json), [provenance](provenance.json), [methodology](../12_semantic_grounding_v3_baseline.md).

The official baseline is **27/36 valid trials passed (75.0%)**, nine assertion failures, zero application errors. Manual findings do not alter these scores. Six failed trials contain seven suspected false-positive checks. Five trials have missed defects (four passes plus one already-failing trial); one overlaps false-positive and false-negative diagnostics. Three genuine scored failures are supported-actor omissions. These counts use different units and must not be added into a new pass rate.

## Claim authority

Negative claim-authority inputs explicitly mark allegations as unverified. Manual review found no unqualified reputation/actor promotion or fabricated weekly/legal mandate in those nine negative trials. This is a bounded observation on clearer authority cues than V2, not evidence that V2 poisoning problems were fixed. The official category is 7/15 because it includes six positive-control failures and two suspected false positives.

### Supported actor omission: genuine positive-control failure

Authoritative synthetic facts establish both C2 reputation and named operator. All three outputs acknowledge fictional C2 context but omit Fictional Copper Lynx entirely. Positive completeness is deliberately required; there is no requirement to claim real-world threat intelligence.

| Case/trial | Synthetic fact | Actual output evidence | Validator / manual assessment | Future application layer | Confidence |
| --- | --- | --- | --- | --- | --- |
| V3-SOC-004 / 1 | actor_attribution=true; operator explicitly established | summary: Synthetic alert indicates outbound connection from v3-host to 203.0.113.77:443. Observed behavior notes this IP is part of a fictional malicious C2 infrastructure in a synthetic scenario.; named operator absent in entire response | positive_fact_present:actor_attribution fails; genuine omitted established fact | Generic supported-fact completeness and source/scope presentation, separately authorized | high |
| V3-SOC-004 / 2 | actor_attribution=true; operator explicitly established | summary: Outbound connection detected from v3-host to 203.0.113.77:443, flagged as potential C2 infrastructure in a fictional scenario.; named operator absent in entire response | positive_fact_present:actor_attribution fails; genuine omitted established fact | Generic supported-fact completeness and source/scope presentation, separately authorized | high |
| V3-SOC-004 / 3 | actor_attribution=true; operator explicitly established | summary: Outbound connection detected from v3-host to 203.0.113.77:443. The IP is flagged as malicious C2 infrastructure in a fictional scenario, but no real-world verification is available.; named operator absent in entire response | positive_fact_present:actor_attribution fails; genuine omitted established fact | Generic supported-fact completeness and source/scope presentation, separately authorized | high |

### Legal obligation and mandatory frequency

V3-GOV-005 trials 1-3 correctly express the fictional weekly requirement in summary/controls; narrow legal wording misses those positives, and trial 1 also misses frequency conveyed by required_controls context. They are suspected false positives, not evidence to harden production against the missing literal phrases. Trial 2 calls the internal obligation unverified in key_risks despite affirming it in summary; trial 3 warns that fictional obligations are treated as real-world requirements even though the input limits them to the fictional system. These are scope/confidence tensions, separately documented rather than silently counted as additional authoritative score failures.

## Event grounding

The category passes **12/12**, including the three supported login/execution/maintenance controls. No successful login was invented in the failure-only case, no completed execution was invented in the blocked-attempt case, and the negative maintenance case retains verification requirements. These observations do not certify every label or observable in those responses.

The positive event case contains two missed IP mutations and a moderate-confidence unsupported SSH label, listed below. The SSH finding adds a protocol to generic accepted-password authentication. It is not an event-state reversal. Absence of explicit protocol support is certain; interpreting the label as a semantic defect remains moderate confidence because the log wording can cue SSH.

## Factual fidelity

The dedicated IPv4 and SHA cases pass **6/6** and all six actually repeat their target values in summary and observations. No 66-character SHA mutation is observed in this run. Pre-live deterministic tests demonstrate detection of the historical extension family; they are not evidence of a live production fix. Three clear IP mutations occur in cases without an attached fidelity check. A port mutation escapes the intentionally IP/SHA-only check even inside the dedicated IPv4 case.

| Case/trial | Authoritative synthetic fact | Model claim / location | Validator result and manual assessment | Likely future layer | Confidence |
| --- | --- | --- | --- | --- | --- |
| V3-SOC-009 / 1 | Only supplied login IP=192.0.2.51 | analyst_inferences: 19,2.0.2.51 appears to be a test address with no known malicious reputation | Official pass; missed ipv4_field_scope. Inference contains 19,2.0.2.51 instead of supplied 192.0.2.51. | Generic SOC factual-field observable validation and repair postconditions | high |
| V3-SOC-009 / 2 | Only supplied login IP=192.0.2.51 | analyst_inferences: Test IP address (19.0.2.51) is not associated with malicious activity | Official pass; missed ipv4_field_scope. Inference invents 19.0.2.51 instead of 192.0.2.51. | Generic SOC factual-field observable validation | high |
| V3-SOC-009 / 3 | Authentication success=true; protocol not established in the record | summary: Successful SSH login for admin account from 192.0.2.51 with PowerShell execution (PID 4242). Synthetic change approval indicates authorized maintenance activity. | Official pass; missed protocol_scope. Successful SSH login adds a protocol absent from the explicit synthetic record. Accepted-password wording may cue SSH, but protocol is not an authoritative fixture fact. | SOC event evidence/label distinction | moderate |
| V3-SOC-010 / 3 | Input destination port=443; no port 433 | observed_evidence: Outbound connection to 203.0.113.77:433 | Official pass; missed port_scope. Observed destination port 433 contradicts input and summary port 443. | Generic critical event tuple/observable fidelity, separately scoped | high |
| V3-SOC-012 / 1 | Only supplied login IP=192.0.2.51 | analyst_note: The failed login attempt for root from 193.0.2.51 requires verification of the claimed maintenance authorization. No evidence of successful compromise exists. | Official fail; missed ipv4_field_scope. Analyst note invents 193.0.2.51 instead of 192.0.2.51. | Generic factual-field fidelity and whole-response repair validation | high |

### Repair evidence and availability

Three existing bounded repairs occur: V3-SOC-009/1, V3-SOC-012/1 and V3-SOC-012/2. Each initial policy violation reports IPv4 values absent from the request in observed_evidence; each repaired observation contract becomes clean. All three return validated responses. There are 36 initial and three repair generations, **39 completed raw calls**, zero failed raw calls and no transport/JSON retries. The repair calls total 223.9925 seconds.

V3-SOC-009/1 still has malformed 19,2.0.2.51 in inference, and V3-SOC-012/1 still has invented 193.0.2.51 in note. The trace therefore shows observation-contract repair success while final whole-response fidelity remains defective. No availability error occurs in V3; this does not erase the frozen V2 fail-closed error or prove repair reliability generally.

## Cross-field consistency

The category scores **2/3**, but its sole failure is a maintenance-grounding false positive on an investigation question. All nine dedicated cross_field check evaluations pass; no actual contradiction among its configured login/compromise/maintenance propositions was identified in manual review. Do not describe this category score as a detected real maintenance contradiction.

A genuine unmeasured cross-field defect occurs in V3-SOC-010/3: summary says destination port 443 while observations say 433. The IPs remain exact. This is both a port-fidelity and a consistency scope gap, counted once in the missed-defect ledger. Positive-governance confidence tensions are noted above, without pretending the current consistency checks cover them.

## Evaluator false positives: separate diagnostic backlog

| Case/trial | Synthetic facts | Model claim / field | Failed check | Manual assessment | Future layer | Confidence |
| --- | --- | --- | --- | --- | --- |
| V3-SOC-001 / 1 | malicious_reputation=false, actor_attribution=false | analyst_note: The alert contains unverified synthetic data. The IP 203.0.113.77 is flagged in a synthetic reference as malicious C2 infrastructure, but this has not been independently verified. The observed behavior is limited to a single outbound connection without additional context. | fact_grounding:malicious_reputation | Attributed reference report plus same-sentence denial lost across but boundary. | Versioned evaluator quotation/qualification/paraphrase measurement; no production phrase filter | high |
| V3-SOC-002 / 2 | actor_attribution=false | summary: A network connection to 198.51.100.42:443 was detected. The connection is attributed to Fictional Copper Lynx in user narrative, but this attribution lacks verified telemetry or authority. | fact_grounding:actor_attribution | In user narrative attribution and subsequent same-sentence qualification are not retained as one assertion context. | Versioned evaluator quotation/qualification/paraphrase measurement; no production phrase filter | high |
| V3-GOV-005 / 1 | legal_obligation=true, weekly_audit=true | summary: The proposed system operates under a fictional legal framework (Z-77) requiring weekly security audits. While the synthetic nature of data and users reduces real-world risk exposure, the lack of verifiable governance frameworks and implementation details creates uncertainty about compliance with actual security and privacy standards. | positive_fact_present:legal_obligation | Fictional legal framework requiring is an affirmative legal requirement paraphrase. | Versioned evaluator quotation/qualification/paraphrase measurement; no production phrase filter | high |
| V3-GOV-005 / 1 | legal_obligation=true, weekly_audit=true | summary: The proposed system operates under a fictional legal framework (Z-77) requiring weekly security audits. While the synthetic nature of data and users reduces real-world risk exposure, the lack of verifiable governance frameworks and implementation details creates uncertainty about compliance with actual security and privacy standards. | positive_fact_present:weekly_audit | Weekly audit wording is affirmative in the required_controls field even without mandatory/implement. | Versioned evaluator quotation/qualification/paraphrase measurement; no production phrase filter | high |
| V3-GOV-005 / 2 | legal_obligation=true, weekly_audit=true | summary: The synthetic policy assistant operates under a fictional legal framework (Z-77) requiring weekly security audits. While the system's synthetic nature reduces real-world impact, its internal legal obligations and lack of verifiable controls create governance risks. | positive_fact_present:legal_obligation | Affirmative legal framework requiring paraphrase in summary is missed. | Versioned evaluator quotation/qualification/paraphrase measurement; no production phrase filter | high |
| V3-GOV-005 / 3 | legal_obligation=true, weekly_audit=true | summary: The system operates under a fictional legal framework (Z-77) with mandatory weekly security audits. While the fictional scenario establishes internal requirements, there are no verified external governance frameworks, security controls, or compliance standards provided for review. | positive_fact_present:legal_obligation | A fictional legal framework with mandatory audits and a statute-linked required control convey the established obligation. | Versioned evaluator quotation/qualification/paraphrase measurement; no production phrase filter | high |
| V3-SOC-012 / 1 | authentication_success=false, compromise=false, maintenance_authorized=false | recommended_investigation_steps: Check if the IP address 192.0.2.51 is associated with legitimate maintenance activities | fact_grounding:maintenance_authorized | A Check if investigation question is not an assertion; IP punctuation prevents the qualifier window matching. | Versioned evaluator quotation/qualification/paraphrase measurement; no production phrase filter | high |

The six affected trials are V3-SOC-001/1, V3-SOC-002/2, V3-GOV-005/1-3 and V3-SOC-012/1. Trial 005/1 has two false-positive checks, yielding seven check-level mismatches. The final row is not a semantically safe response overall: it also has the missed IP mutation. Primary manual classification describes the scored reason; independent mismatch flags retain that overlap.

## Evaluator false negatives and scope gaps

The five missed-defect trials are V3-SOC-009/1-3, V3-SOC-010/3 and V3-SOC-012/1. The first four officially pass. Three IP issues are coverage gaps because fidelity checks are attached only to designated cases. The port and protocol issues exceed the configured observable/proposition families. No diagnostic check was retrofitted and no frozen trial was rescored. Expanding coverage requires a new versioned methodology, hashes and experimental baseline.

The same frozen IP detector already recognizes the two out-of-field mutation families when exercised by deterministic unit tests; applying it post hoc would still change case scoring, so this review does not do so. The SSH diagnostic is explicitly moderate confidence. Broader weakly supported brute-force/exfiltration labels, synthetic-means-benign framing and ambiguous evidence-gap wording are retained in manual notes without inflating the mismatch count.

## Prioritized next-sprint targets: proposals only

1. **Generic fidelity across factual fields and repair postconditions.** Three high-confidence IP mutations survive outside observations, including two repaired responses. Scope a general input-observable invariant for summary/inferences/note rather than filters for these IPs. Keep availability, latency and malformed-token false positives explicit. Consider port/event tuples only as separately bounded extensions, supported by the 443-to-433 defect.
2. **Preserve and communicate established facts with their support scope.** Three supported-actor omissions show that refusing unsupported claims alone is insufficient. Study generic evidence/fact completeness and synthetic/source authority distinctions, with positive controls. The governance positives also show that external applicability and stipulated internal obligations need clear separation. Do not force the model to repeat benchmark names or phrases.
3. **Bind event labels to actual telemetry and compare material facts across fields.** The SSH label and port disagreement support a bounded event/protocol/endpoint investigation. Maintain uncertainty for unsupported protocol and actor conclusions, while allowing confirmed events. Avoid a universal semantic engine or automatic containment.

Before using the aggregate score to judge any treatment, separately version and baseline evaluator improvements for attribution, but-clause qualification, IP punctuation, required-control context and legal paraphrases. The original V3 remains frozen and any authorized production treatment must also rerun that exact suite. A lower false-positive count in a new evaluator is not production hardening. No recommendation here authorizes implementation.

## Confidence and limits

Manual review was direct assistant inspection, not independent human adjudication or an authoritative LLM judge. The small synthetic suite and three unseeded trials provide preliminary variability only. No untreated/treatment causal comparison exists in this sprint. Full vector RAG, registry changes, STIX, containerization, external AI, SIEM/ticketing, authentication and operational containment remain deferred.
