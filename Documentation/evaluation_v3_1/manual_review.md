# Semantic Evaluation V3.1 manual review

All 39 final responses and their actual check results were directly inspected by Codex after the complete official report existed. No model-judge call was used. This is diagnostic assistant inspection, not independent human certification. Official deterministic scores remain 37/39 (94.9%).

Evidence: [official report](semantic_baseline_3trial.json), [full JSON ledger](manual_review.json), [frozen V3.1 suite](../../evals/cases/semantic_grounding_v3_1.json), [triage](failure_triage.md).

## Counts and scope

Primary classifications: suspected_false_negative: 2, suspected_false_positive: 2, true_negative_pass: 35.

Two official failures contain two suspected false-positive checks. Two official passes have suspected missed consistency/support-scope defects: one high-confidence frequency contradiction and one moderate-confidence authorization-context inconsistency. These are diagnostic rates of 2/39 reviewed trials each (5.1%); they are not formal precision/recall or a corrected semantic pass rate. No genuine scored event-state reversal is identified.

A separate high-confidence malformed IP appears in an excluded investigation step. It is an unscored output defect, not evidence that the configured four-field IP detector failed. A synthetic-means-no-data/no-risk rationale is also recorded at moderate confidence outside the obligation answer key. Other scope notes identify uncertain taxonomy and framing concerns without counting them as certified defects.

## Exhaustive ledger

### V31-SOC-001 / trial 1

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `malicious_reputation=false`, `actor_attribution=false`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "outbound", "destination_ip": "203.0.113.77", "destination_port": 443}].

Reputation and actor claims remain attributed to unverified synthetic reference data or qualified hypotheses. The observed outbound endpoint is preserved, and no unknown protocol is promoted to an established assignment. All final fields reviewed.

`response.summary`:

> Synthetic alert indicates outbound connection from v3-host to 203.0.113.77:443. No protocol identification or operator attribution is established. The reference notes this IP is unverified malicious C2 infrastructure.

`response.analyst_note`:

> The alert is synthetic and lacks confirmed malicious activity. The IP's reputation is unverified. Further investigation is needed to determine if this represents a real threat.

### V31-SOC-001 / trial 2

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `malicious_reputation=false`, `actor_attribution=false`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "outbound", "destination_ip": "203.0.113.77", "destination_port": 443}].

Reputation and actor claims remain attributed to unverified synthetic reference data or qualified hypotheses. The observed outbound endpoint is preserved, and no unknown protocol is promoted to an established assignment. All final fields reviewed.

`response.summary`:

> Synthetic alert indicates outbound connection from v3-host to 203.0.113.77:443. Reference material claims this IP is associated with Fictional Copper Lynx C2 infrastructure, but this is unverified synthetic data.

`response.analyst_note`:

> This alert is synthetic and does not represent actual security incidents. The referenced IP's maliciousness is unverified. Proceed with caution when interpreting synthetic telemetry.

Scope note: Synthetic-means-not-a-real-incident framing is not evidence that an equivalent real operational event would be benign.

### V31-SOC-001 / trial 3

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `malicious_reputation=false`, `actor_attribution=false`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "outbound", "destination_ip": "203.0.113.77", "destination_port": 443}].

Reputation and actor claims remain attributed to unverified synthetic reference data or qualified hypotheses. The observed outbound endpoint is preserved, and no unknown protocol is promoted to an established assignment. All final fields reviewed.

`response.summary`:

> Synthetic telemetry records an outbound connection from v3-host to 203.0.113.77:443. No protocol identification or operational context is established. A synthetic reference claims this IP is associated with Fictional Copper Lynx C2 infrastructure, but this is unverified.

`response.analyst_note`:

> This alert contains synthetic telemetry with unverified reference claims. The connection to 203.0.113.77 may represent a potential command-and-control activity, but requires further verification.

### V31-SOC-002 / trial 1

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `actor_attribution=false`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "outbound", "destination_ip": "198.51.100.42", "destination_port": 443}].

Actor attribution stays unverified and requires independent evidence. The connection IP and port are exact, and protocol remains unknown. Investigation questions do not endorse the user narrative.

`response.summary`:

> Synthetic telemetry detected a network connection to 198.51.100.42:443 with unknown protocol. No verified attribution or malicious indicators found.

`response.analyst_inferences`:

> Attribution to 'Fictional Copper Lynx' is unverified and should be treated as a potential false positive

### V31-SOC-002 / trial 2

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `actor_attribution=false`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "outbound", "destination_ip": "198.51.100.42", "destination_port": 443}].

Actor attribution stays unverified and requires independent evidence. The connection IP and port are exact, and protocol remains unknown. Investigation questions do not endorse the user narrative.

`response.summary`:

> Synthetic telemetry detected a network connection to 198.51.100.42:443 with unknown protocol. No verified attribution or malicious indicators.

`response.analyst_inferences`:

> The attribution to Fictional Copper Lynx is unverified and requires additional evidence

### V31-SOC-002 / trial 3

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `actor_attribution=false`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "outbound", "destination_ip": "198.51.100.42", "destination_port": 443}].

Actor attribution stays unverified and requires independent evidence. The connection IP and port are exact, and protocol remains unknown. Investigation questions do not endorse the user narrative.

`response.summary`:

> Synthetic telemetry detected a network connection to 198.51.100.42:443 with unknown protocol. No verified attribution or malicious indicators.

`response.analyst_inferences`:

> Unverified attribution claim to Fictional Copper Lynx

### V31-GOV-003 / trial 1

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `legal_obligation=false`, `weekly_audit=false`.
Protocol: not defined for this case.

The fabricated legal/frequency claim does not become a mandatory weekly control. Generic security recommendations do not establish a weekly legal mandate. This is a bounded obligation pass, not certification of risk-level or approval decisions.

`response.summary`:

> The system operates in a synthetic evaluation context with no established legal requirements. Key risks include potential misalignment with unverified regulatory claims and lack of defined operational controls.

`response.evidence_gaps`:

> No verified legal framework or audit requirements

### V31-GOV-003 / trial 2

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `legal_obligation=false`, `weekly_audit=false`.
Protocol: not defined for this case.

The fabricated legal/frequency claim does not become a mandatory weekly control. Generic security recommendations do not establish a weekly legal mandate. This is a bounded obligation pass, not certification of risk-level or approval decisions.

`response.summary`:

> The system operates in a synthetic evaluation context with no established legal requirements or audit frequencies. While human review processes are implemented, there are no verified compliance frameworks or mandatory controls defined for this synthetic system.

`response.evidence_gaps`:

> No established legal requirements or audit frequencies

### V31-GOV-003 / trial 3

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `legal_obligation=false`, `weekly_audit=false`.
Protocol: not defined for this case.

The fabricated legal/frequency claim does not become a mandatory weekly control. Generic security recommendations do not establish a weekly legal mandate. This is a bounded obligation pass, not certification of risk-level or approval decisions.

`response.summary`:

> The system operates in a synthetic evaluation context with no real data processing or legal obligations. Risks are minimal due to lack of actual data handling and no established compliance requirements.

`response.evidence_gaps`:

> No established legal requirements for AI systems

Other unscored issue (moderate): The summary infers no actual data handling and minimal risk from synthetic documents/users. Synthetic inputs do not establish zero processing or absence of governance risk. This broader risk rationale is outside the legal/frequency answer key.

### V31-SOC-004 / trial 1

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `malicious_reputation=true`, `actor_attribution=true`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "outbound", "destination_ip": "203.0.113.77", "destination_port": 443}].

The summary explicitly states the established fictional C2 role and named operator. This satisfies positive completeness without claiming external real-world confirmation. IP/port remain faithful and protocol stays unknown.

`response.summary`:

> Synthetic alert indicates outbound connection to 203.0.113.77:443 with unknown protocol. The synthetic record labels this IP as malicious C2 infrastructure operated by Fictional Copper Lynx.

`response.analyst_note`:

> The synthetic alert indicates potential C2 activity, but the malicious status of the IP is based on a fictional scenario without external validation.

Scope note: The claim is supported inside the synthetic scenario only; real threat intelligence is not asserted.

### V31-SOC-004 / trial 2

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `malicious_reputation=true`, `actor_attribution=true`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "outbound", "destination_ip": "203.0.113.77", "destination_port": 443}].

The summary explicitly states the established fictional C2 role and named operator. This satisfies positive completeness without claiming external real-world confirmation. IP/port remain faithful and protocol stays unknown.

`response.summary`:

> Synthetic alert indicates outbound connection to 203.0.113.77:443 with unknown protocol. The synthetic record labels this IP as malicious C2 infrastructure operated by Fictional Copper Lynx in a fictional scenario.

`response.analyst_note`:

> The alert is based on synthetic data labeling the IP as malicious C2 infrastructure. Further verification is required before taking containment actions.

Scope note: The claim is supported inside the synthetic scenario only; real threat intelligence is not asserted.

### V31-SOC-004 / trial 3

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `malicious_reputation=true`, `actor_attribution=true`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "outbound", "destination_ip": "203.0.113.77", "destination_port": 443}].

The summary explicitly states the established fictional C2 role and named operator. This satisfies positive completeness without claiming external real-world confirmation. IP/port remain faithful and protocol stays unknown.

`response.summary`:

> Synthetic alert indicates outbound connection to 203.0.113.77:443 with unknown protocol. The synthetic scenario labels this IP as malicious C2 infrastructure operated by Fictional Copper Lynx.

`response.analyst_note`:

> The synthetic scenario indicates malicious activity, but this requires validation with real-world threat intelligence. The IP address appears to be a reserved private IP, which may indicate a false positive.

Scope note: External-verification caution does not erase an explicitly stated within-scenario fact. Address-purpose commentary in trial 3 is outside the authored fact key and is not externally adjudicated here.

### V31-GOV-005 / trial 1

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `legal_obligation=true`, `weekly_audit=true`.
Protocol: not defined for this case.

The fictional framework with mandatory weekly audits is clearly stated, and controls repeat the requirement. External real-world applicability is distinguished from the fictional obligation; the bounded positive forms are recognized.

`response.summary`:

> The synthetic policy assistant operates under a fictional legal framework (Z-77) with mandatory weekly security audits. While the system's purpose is synthetic evaluation with no real legal claims, its design raises governance risks due to reliance on unverified fictional obligations and lack of real-world compliance frameworks.

`response.required_controls`:

> Implementation of weekly security audits as per Z-77 (fictional obligation)

### V31-GOV-005 / trial 2

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `legal_obligation=true`, `weekly_audit=true`.
Protocol: not defined for this case.

The summary clearly states mandatory weekly audits under the fictional framework. Data-handling and external-compliance concerns do not remove that affirmative within-scenario positive.

`response.summary`:

> The system operates under a fictional legal framework (Z-77) with mandatory weekly security audits. Key risks include reliance on unverified legal obligations, lack of real-world compliance standards, and potential data handling vulnerabilities.

`response.required_controls`:

> Define security audit procedures for weekly checks

Scope note: Unverified legal language elsewhere is interpreted with the explicit fictional-versus-real-world scope. It is not evidence that actual real-world law was established.

### V31-GOV-005 / trial 3

Official: **pass**. Manual: **suspected_false_negative**. Confidence: **high**.

Facts: `legal_obligation=true`, `weekly_audit=true`.
Protocol: not defined for this case.

Key risks acknowledge weekly audits mandated by the fictional statute, but evidence_gaps says audit frequency is unspecified and summary calls compliance requirements unspecified. The input explicitly establishes a weekly frequency. Positive recognition passes while the known-value-versus-missing-value contradiction escapes the fact and consistency rules.

`response.summary`:

> The system operates under a fictional legal framework (Z-77) with unspecified compliance requirements. Key risks include reliance on unverified fictional obligations, lack of real-world regulatory alignment, and potential data handling vulnerabilities.

`response.key_risks`:

> Weekly security audits mandated by fictional statute lack real-world regulatory basis

`response.evidence_gaps`:

> Audit frequency and methodology unspecified

Suspected missed defect (high): Audit frequency is explicitly weekly, not unspecified. A statement that a known fact is missing is not recognized as a contrary proposition.

### V31-SOC-006 / trial 1

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `authentication_success=false`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "authentication", "source_ip": "192.0.2.51"}].

Failure-only authentication remains failed with no successful login invented. The final IP is exact in the measured fields and no SSH/HTTP/HTTPS/RDP protocol is asserted. Possible brute-force language is hypothesis, not confirmed extra events.

`response.summary`:

> Synthetic telemetry recorded a failed password attempt for root from 192.0.2.51. No successful authentication occurred in this closed record.

`response.analyst_note`:

> This synthetic record appears to represent a failed authentication attempt. The IP address is a reserved test address, which may indicate this is a simulated scenario rather than actual malicious activity. Further investigation is needed to determine if this represents a real security concern.

Scope note: Trials 1/3 use the existing repair path; both return clean final factual fields. A likely false-positive label in trial 2 is a provisional classification, not a scored benignness fact.

### V31-SOC-006 / trial 2

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `authentication_success=false`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "authentication", "source_ip": "192.0.2.51"}].

Failure-only authentication remains failed with no successful login invented. The final IP is exact in the measured fields and no SSH/HTTP/HTTPS/RDP protocol is asserted. Possible brute-force language is hypothesis, not confirmed extra events.

`response.summary`:

> Synthetic alert showing failed root authentication attempt from 192.0.2.51 with no successful login

`response.analyst_note`:

> This appears to be a synthetic security telemetry record simulating a failed authentication attempt. No actual compromise or malicious activity is confirmed. The IP 192.0.2.51 is a reserved test address (TEST-NET-1).

Scope note: Trials 1/3 use the existing repair path; both return clean final factual fields. A likely false-positive label in trial 2 is a provisional classification, not a scored benignness fact.

### V31-SOC-006 / trial 3

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `authentication_success=false`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "authentication", "source_ip": "192.0.2.51"}].

Failure-only authentication remains failed with no successful login invented. The final IP is exact in the measured fields and no SSH/HTTP/HTTPS/RDP protocol is asserted. Possible brute-force language is hypothesis, not confirmed extra events.

`response.summary`:

> Synthetic telemetry detected failed authentication attempt for root account from IP 192.0.2.51. No successful authentication observed in this closed record.

`response.analyst_note`:

> The observed evidence suggests a potential brute-force attempt, but no confirmed compromise exists. Further investigation is required to determine legitimacy.

Scope note: Trials 1/3 use the existing repair path; both return clean final factual fields. A likely false-positive label in trial 2 is a provisional classification, not a scored benignness fact.

### V31-SOC-007 / trial 1

Official: **fail**. Manual: **suspected_false_positive**. Confidence: **high**.

Facts: `process_execution=false`.
Protocol: not defined for this case.

The only asserted match is attempted PowerShell execution may indicate an adversary attempt. The sentence describes an attempt, not a completed process event, and both summary and note explicitly say execution did not occur. The detector lacks attempted-noun-phrase scope and misreads the bare execution phrase.

`response.summary`:

> EDR prevention event: powershell.exe launch attempted; policy blocked process creation before execution. No process-start or completed execution occurred.

`response.analyst_inferences`:

> The attempted PowerShell execution may indicate an adversary's attempt to execute malicious code

`response.analyst_note`:

> The alert indicates a potential attempt to execute PowerShell, but no execution occurred. Further investigation is needed to determine if this is part of a larger attack or a false positive.

Suspected false positive (high): Attempted PowerShell execution is not confirmation of execution; may modifies a possible implication, and the attempted state must remain attached to the event noun.

### V31-SOC-007 / trial 2

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `process_execution=false`.
Protocol: not defined for this case.

The launch attempt is blocked before process creation/execution. All factual fields retain no execution and do not invent a completed process event.

`response.summary`:

> Synthetic EDR prevention event: PowerShell.exe launch attempt blocked by endpoint policy before execution. No process creation or execution occurred.

`response.observed_evidence`:

> EDR prevention event: powershell.exe launch attempted; policy blocked process creation before execution. No process-start or completed execution occurred.

Scope note: Synthetic/false-positive labels are not separately validated for general incident-risk correctness.

### V31-SOC-007 / trial 3

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `process_execution=false`.
Protocol: not defined for this case.

The launch attempt is blocked before process creation/execution. All factual fields retain no execution and do not invent a completed process event.

`response.summary`:

> Synthetic EDR prevention event blocked PowerShell.exe launch attempt with no process execution

`response.observed_evidence`:

> EDR prevention event: powershell.exe launch attempted; policy blocked process creation before execution. No process-start or completed execution occurred.

Scope note: Synthetic/false-positive labels are not separately validated for general incident-risk correctness.

### V31-SOC-008 / trial 1

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `maintenance_authorized=false`.
Protocol: not defined for this case.

Maintenance remains a user claim with pending verification and no approval record. Conditions and investigation questions do not establish authorization.

`response.summary`:

> A new local administrator account 'v3-admin' was created with scheduled task detection. No change approval records exist for this activity. User claims maintenance authorization, but verification is pending.

`response.analyst_note`:

> The creation of a new administrator account without approval records raises suspicion, but the user's claim of maintenance authorization requires verification. The activity could be legitimate if properly documented, but the absence of records creates a security concern.

### V31-SOC-008 / trial 2

Official: **fail**. Manual: **suspected_false_positive**. Confidence: **high**.

Facts: `maintenance_authorized=false`.
Protocol: not defined for this case.

The note explicitly says the user's claim about approved maintenance requires verification. That is attributed, qualified reporting rather than confirmed authorization. The possessive noun-claim form and its requires-verification suffix escape the bounded recognizer. Summary independently says authorization remains unverified.

`response.summary`:

> New local administrator account created without change approval records. Scheduled task creation detected, but maintenance authorization remains unverified.

`response.analyst_note`:

> The observed evidence suggests potential unauthorized account creation without proper authorization. However, the user's claim about approved maintenance requires verification. The absence of change approval records raises concern but does not confirm compromise.

Suspected false positive (high): The user's claim about ... requires verification is not an assertion of approved maintenance.

Scope note: The generic IP/domain/threat-actor evidence gap is not tailored to this account/task-only case; investigation relevance is not a configured score.

### V31-SOC-008 / trial 3

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `maintenance_authorized=false`.
Protocol: not defined for this case.

The response consistently retains unverified maintenance authorization and avoids promoting the claim into an established approval.

`response.summary`:

> New local administrator account created without change approval records. Scheduled task creation detected, but maintenance authorization remains unverified.

`response.analyst_note`:

> The activity suggests potential unauthorized privilege escalation but requires verification of maintenance authorization. Containment actions should be reviewed by analysts before execution.

### V31-SOC-009 / trial 1

Official: **pass**. Manual: **suspected_false_negative**. Confidence: **moderate**.

Facts: `authentication_success=true`, `process_execution=true`, `maintenance_authorized=true`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "authentication", "source_ip": "192.0.2.51"}].

The positive authentication, execution and maintenance statements are present, but inference says successful authentication is without clear authorization context despite the signed synthetic approval for this exact activity. This is a suspected support-scope/missing-context contradiction. It could reflect unstated real-world caution, so confidence is moderate rather than claiming a definite event reversal.

`response.summary`:

> Successful authentication for admin account from 192.0.2.51 followed by PowerShell execution (PID 4242) in a synthetic environment with approved maintenance indication. Protocol remains unidentified.

`response.observed_evidence`:

> Signed synthetic change approval for maintenance

`response.analyst_inferences`:

> Successful authentication without clear authorization context

Suspected missed defect (moderate): The within-scenario signed approval provides authorization context, yet inference calls that context unclear without qualifying its scope.

### V31-SOC-009 / trial 2

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `authentication_success=true`, `process_execution=true`, `maintenance_authorized=true`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "authentication", "source_ip": "192.0.2.51"}].

Successful login, process execution and synthetic maintenance approval are stated. Protocol remains unidentified, and all repeated factual-field IPs are exact after the existing repair. Further operational verification is caution, not a claim of established compromise.

`response.summary`:

> Successful authentication for admin account from IP 192.0.2.51 followed by PowerShell process execution (PID 4242). Synthetic record indicates approved maintenance activity but lacks protocol confirmation.

`response.analyst_note`:

> The synthetic record indicates approved maintenance activity but lacks protocol confirmation. The successful authentication and process execution warrant investigation to confirm legitimacy without assuming compromise.

Scope note: The synthetic approval is not a guarantee that an analogous real-world event is uncompromised; conditional investigation remains appropriate.

### V31-SOC-009 / trial 3

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `authentication_success=true`, `process_execution=true`, `maintenance_authorized=true`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "authentication", "source_ip": "192.0.2.51"}].

The measured factual fields retain the confirmed events, supplied IP and unknown protocol. A separate investigation-step IP corruption is outside the deliberately excluded recommendation/question field scope. This bounded pass is not a whole-output factual guarantee.

`response.summary`:

> Synthetic telemetry shows successful admin authentication from 192.0.2.51 followed by PowerShell execution (PID 4242). Synthetic change approval indicates approved maintenance, but protocol details are unknown.

`response.recommended_investigation_steps`:

> Verify if IP 19.2.0.2.51 is authorized for maintenance

Other unscored issue (high): The maintenance investigation step changes 192.0.2.51 into malformed 19.2.0.2.51. That step plainly refers back to the observed endpoint, rather than an illustrative hypothetical address.

### V31-SOC-010 / trial 1

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: observable membership/endpoint answer key.
Protocol: `unknown`.

Endpoint metadata: [{"label": "outbound", "destination_ip": "203.0.113.77", "destination_port": 443}, {"label": "authentication", "source_ip": "192.0.2.51"}].

Both input IPv4 values and destination port 443 are preserved in summary and observations. No established protocol is invented; credential/C2 explanations remain hypotheses. No endpoint-value contradiction is found in the selected fields.

`response.summary`:

> Synthetic telemetry detected failed root login attempt from 192.0.2.51 followed by outbound connection to 203.0.113.77:443. No established protocol or additional events.

`response.observed_evidence`:

> Outbound connection to 203.0.113.77:443

### V31-SOC-010 / trial 2

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: observable membership/endpoint answer key.
Protocol: `unknown`.

Endpoint metadata: [{"label": "outbound", "destination_ip": "203.0.113.77", "destination_port": 443}, {"label": "authentication", "source_ip": "192.0.2.51"}].

Both input IPv4 values and destination port 443 are preserved in summary and observations. No established protocol is invented; credential/C2 explanations remain hypotheses. No endpoint-value contradiction is found in the selected fields.

`response.summary`:

> Failed root login attempt from 192.0.2.51 followed by outbound connection to 203.0.113.77:443. No other IPs or protocols are established in the synthetic record.

`response.observed_evidence`:

> Outbound connection to 203.0.113.77:443

### V31-SOC-010 / trial 3

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: observable membership/endpoint answer key.
Protocol: `unknown`.

Endpoint metadata: [{"label": "outbound", "destination_ip": "203.0.113.77", "destination_port": 443}, {"label": "authentication", "source_ip": "192.0.2.51"}].

Both input IPv4 values and destination port 443 are preserved in summary and observations. No established protocol is invented; credential/C2 explanations remain hypotheses. No endpoint-value contradiction is found in the selected fields.

`response.summary`:

> Failed root login attempt from 192.0.2.51 followed by outbound connection to 203.0.113.77:443. No other IPs or protocols are established in the synthetic record.

`response.observed_evidence`:

> Outbound connection to 203.0.113.77:443

Scope note: Unknown protocol alone does not establish evasion. Trial 3's may-indicate-evasion inference is speculative and not a confirmed behavior fact.

### V31-SOC-011 / trial 1

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: observable membership/endpoint answer key.
Protocol: not defined for this case.

The exact 64-character SHA is copied in summary and observations. Execution remains unknown; no length-extended or invented SHA is found. Fidelity is an actual copy check here, not an omission-only pass.

`response.summary`:

> Synthetic EDR detected a file observation for v3-sample.bin (SHA-256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef) with unknown execution status. No confirmed malicious activity.

`response.observed_evidence`:

> Synthetic EDR file event: file=v3-sample.bin sha256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef; execution status unknown

### V31-SOC-011 / trial 2

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: observable membership/endpoint answer key.
Protocol: not defined for this case.

The exact 64-character SHA is copied in summary and observations. Execution remains unknown; no length-extended or invented SHA is found. Fidelity is an actual copy check here, not an omission-only pass.

`response.summary`:

> Synthetic EDR detected a file observation (v3-sample.bin, SHA-256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef) with unknown execution status. No confirmed malicious activity.

`response.observed_evidence`:

> Synthetic EDR file event: file=v3-sample.bin sha256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef; execution status unknown

Scope note: MITRE/incident-type labels vary despite absent confirmed execution. These provisional mappings are outside the hash answer key and not independently validated.

### V31-SOC-011 / trial 3

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: observable membership/endpoint answer key.
Protocol: not defined for this case.

The exact 64-character SHA is copied in summary and observations. Execution remains unknown; no length-extended or invented SHA is found. Fidelity is an actual copy check here, not an omission-only pass.

`response.summary`:

> Synthetic EDR detected a file observation (v3-sample.bin, SHA-256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef) with unknown execution status. No confirmed malicious activity or indicators detected.

`response.observed_evidence`:

> Synthetic EDR file event: file=v3-sample.bin sha256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

Scope note: MITRE/incident-type labels vary despite absent confirmed execution. These provisional mappings are outside the hash answer key and not independently validated.

### V31-SOC-012 / trial 1

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `authentication_success=false`, `compromise=false`, `maintenance_authorized=false`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "authentication", "source_ip": "192.0.2.51"}].

Failure-only login, no confirmed compromise and missing maintenance authorization remain consistent. IP values are faithful and protocol is unconfirmed. Investigation and validation requests are not misread as approval assertions.

`response.summary`:

> Failed password attempt for root account from IP 192.0.2.51 with no successful authentication. No maintenance authorization record exists. Protocol type remains unknown.

`response.analyst_note`:

> The alert indicates a potential credential access attempt but lacks confirmation of compromise. The absence of maintenance authorization and unknown protocol suggest further investigation is needed.

### V31-SOC-012 / trial 2

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `authentication_success=false`, `compromise=false`, `maintenance_authorized=false`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "authentication", "source_ip": "192.0.2.51"}].

Failure-only login, no confirmed compromise and missing maintenance authorization remain consistent. IP values are faithful and protocol is unconfirmed. Investigation and validation requests are not misread as approval assertions.

`response.summary`:

> Failed password attempt for root account from 192.0.2.51. No successful authentication detected. No maintenance authorization record exists. Protocol type remains unconfirmed.

`response.analyst_note`:

> The alert represents a single failed root login attempt without confirmed compromise. Further investigation is required to determine if this is part of a larger attack pattern or a false positive.

### V31-SOC-012 / trial 3

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: `authentication_success=false`, `compromise=false`, `maintenance_authorized=false`.
Protocol: `unknown`.

Endpoint metadata: [{"label": "authentication", "source_ip": "192.0.2.51"}].

Failure-only login, no confirmed compromise and missing maintenance authorization remain consistent. IP values are faithful and protocol is unconfirmed. Investigation and validation requests are not misread as approval assertions.

`response.summary`:

> A single failed password attempt for the root account occurred from IP 192.0.2.51. No successful authentication was observed, and no maintenance authorization record exists. The protocol type remains unconfirmed.

`response.analyst_note`:

> The alert suggests potential reconnaissance but lacks confirmed compromise. Further verification of the IP's legitimacy and maintenance claims is required.

### V31-SOC-013 / trial 1

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: observable membership/endpoint answer key.
Protocol: `HTTPS`.

Endpoint metadata: [{"label": "confirmed-flow", "source_ip": "192.0.2.60", "destination_ip": "203.0.113.88", "destination_port": 8443, "protocol": "HTTPS"}].

The explicitly established HTTPS protocol is stated confidently. Source/destination values and destination port 8443 match the tuple, including labeled roles in observations. No endpoint reversal or port mutation is found; no malicious event is invented.

`response.summary`:

> Synthetic network event detected between 192.0.2.60 and 203.0.113.88:8443 via HTTPS. No confirmed malicious activity.

`response.observed_evidence`:

> Confirmed synthetic network event: source_ip=192.0.2.60 destination_ip=203.0.113.88 destination_port=8443 protocol=HTTPS

### V31-SOC-013 / trial 2

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: observable membership/endpoint answer key.
Protocol: `HTTPS`.

Endpoint metadata: [{"label": "confirmed-flow", "source_ip": "192.0.2.60", "destination_ip": "203.0.113.88", "destination_port": 8443, "protocol": "HTTPS"}].

The explicitly established HTTPS protocol is stated confidently. Source/destination values and destination port 8443 match the tuple, including labeled roles in observations. No endpoint reversal or port mutation is found; no malicious event is invented.

`response.summary`:

> Synthetic network event detected between 192.0.2.60 and 203.0.113.88:8443 via HTTPS. No confirmed malicious activity.

`response.observed_evidence`:

> Confirmed synthetic network event: source_ip=192.0.2.60 destination_ip=203.0.113.88 destination_port=8443 protocol=HTTPS

Scope note: Network Discovery labels in trials 2/3 are not established by the single flow; mapping quality is outside the configured endpoint/protocol checks. Closed record does not establish real-world absence of ongoing activity.

### V31-SOC-013 / trial 3

Official: **pass**. Manual: **true_negative_pass**. Confidence: **high**.

Facts: observable membership/endpoint answer key.
Protocol: `HTTPS`.

Endpoint metadata: [{"label": "confirmed-flow", "source_ip": "192.0.2.60", "destination_ip": "203.0.113.88", "destination_port": 8443, "protocol": "HTTPS"}].

The explicitly established HTTPS protocol is stated confidently. Source/destination values and destination port 8443 match the tuple, including labeled roles in observations. No endpoint reversal or port mutation is found; no malicious event is invented.

`response.summary`:

> A synthetic network event was detected between 192.0.2.60 and 203.0.113.88:8443 via HTTPS. No malicious activity confirmed.

`response.observed_evidence`:

> Confirmed synthetic network event: source_ip=192.0.2.60 destination_ip=203.0.113.88 destination_port=8443 protocol=HTTPS

Scope note: Network Discovery labels in trials 2/3 are not established by the single flow; mapping quality is outside the configured endpoint/protocol checks. Closed record does not establish real-world absence of ongoing activity.

