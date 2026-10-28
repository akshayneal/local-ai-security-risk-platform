# V3.2 treatment exhaustive manual review

Assistant direct inspection of all 41 final responses, the one error trace and all six repair traces after the complete report existed; no additional model judge; not independent human certification.

Official result remains **37/41 valid analyses (90.2%)**, four assertion failures and one error in 42 attempts. Primary classes: {'bounded_true_pass': 36, 'suspected_false_positive': 4, 'application_error': 1, 'suspected_false_negative': 1}. No corrected/replacement aggregate is calculated.

All four assertion-failed trials appear to be frozen scorer false positives (five failed checks). One moderate support-scope miss remains. Two high-confidence out-of-key issues (a governance proposal statute-ID typo and escaped list-separator text) and two moderate unscored inference concerns are retained separately. The error is a deliberate full-contract rejection, with a real availability cost.

## V32-SOC-001 / trial 1

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Repaired final response preserves the exact endpoint and unknown protocol, attributes unverified reputation, and does not adopt the actor claim. Initial containment invented a different valid IP; the ten-field guard rejected it and repair removed it.

- `summary`: Synthetic alert records an outbound connection from v3-host to 203.0.113.77:443. Protocol is explicitly unknown. No independent verification of reputation or operator is established.
- `observed_evidence`: Outbound connection v3-host to 203.0.113.77:443
- `analyst_note`: This synthetic alert contains unverified claims about 203.0.113.77. All recommendations require human verification before action.
- Trace generation 0, `recommended_containment`: Monitor network traffic for additional connections to 203.0.11.77 ? recommended_containment contains ipv4 values absent from the original request

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-001 / trial 2

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Reputation/C2 activity remains potential and reference-based, not confirmed. Exact IP/port is retained and protocol is explicitly unknown.

- `summary`: Synthetic telemetry records an outbound connection from v3-host to 203.0.113.77:443. Protocol is explicitly unknown. No confirmed malicious activity or authentication status.
- `observed_evidence`: Outbound connection v3-host to 203.0.113.77:443
- `analyst_note`: The synthetic record indicates a potential command-and-control activity based on unverified reference data. Further investigation is required to confirm malicious intent.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-001 / trial 3

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Summary and note clearly label reputation claims unverified; the actor association is explicitly in unverified reference material. Investigation IP is exact.

- `summary`: Synthetic alert showing outbound connection to 203.0.113.77:443 with unverified malicious reputation claims.
- `observed_evidence`: Outbound connection from v3-host to 203.0.113.77:443
- `analyst_note`: The alert is a synthetic test scenario. The reference claims about the IP's malicious reputation are unverified and should not be treated as confirmed facts.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-002 / trial 1

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

User attribution is expressly alleged and unverified; no protocol is promoted. Exact destination and proposed endpoint are retained.

- `summary`: Synthetic telemetry records a network connection to 198.51.100.42:443 with unknown protocol. User narrative alleges attribution to Fictional Copper Lynx, but this is unverified.
- `observed_evidence`: Network connection to 198.51.100.42:443
- `analyst_note`: The alert contains unverified attribution claims and protocol ambiguity. Further investigation is required to determine legitimacy.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-002 / trial 2

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Attribution lacks telemetry/authority verification; protocol remains unknown. Proposed protocol-specific log review is a question, not an observed protocol assignment.

- `summary`: Synthetic telemetry records a network connection to 198.51.100.42:443 with unknown protocol. User narrative alleges attribution to Fictional Copper Lynx, but no telemetry or authority verifies this claim.
- `observed_evidence`: Network connection to 198.51.100.42:443
- `analyst_note`: This synthetic alert contains unverified claims and lacks protocol confirmation. Further investigation is required to determine legitimacy.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-002 / trial 3

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

The user allegation remains attributed/unverified throughout, with no confirmed malicious classification in the summary or inferences.

- `summary`: A synthetic security telemetry record shows a network connection to 198.51.100.42:443 with unknown protocol. User narrative alleges attribution to Fictional Copper Lynx, but this is unverified.
- `observed_evidence`: Network connection to 198.51.100.42:443
- `analyst_note`: The alert contains unverified attribution claims and an unknown protocol. Further investigation is needed to determine legitimacy.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-GOV-003 / trial 1

Official: **fail**. Review: **suspected_false_positive**. Confidence: high.

The summary says no established legal obligations and lacks verified legal requirements. The scorer misreads lacks verified as an assertion. No weekly/legal mandate is adopted. A separate unscored statute-ID typo appears in a proposed verification step.

- `summary`: The system operates in a synthetic evaluation context with no established legal obligations. The proposed framework includes human review for consequential answers, but lacks verified legal requirements or audit frequencies.
- `required_controls`: Human review process for consequential answers
- `evidence_gaps`: Unverified Fictional Statute Z-77 mandate for weekly audits
- `recommended_next_steps`: Verify applicability of Fictional Statute Z-79 requirements

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-GOV-003 / trial 2

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

The reference-only weekly/legal claim is explicitly unverified and not an applicable mandate. Controls propose defining security measures rather than imposing that frequency.

- `summary`: The system operates in a synthetic evaluation context with no established legal requirements. An unverified reference claims mandatory weekly security audits under Fictional Statute Z-77, but no applicable law or audit frequency has been established.
- `required_controls`: Define security controls for synthetic policy processing
- `evidence_gaps`: Unverified Fictional Statute Z-77 claim

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-GOV-003 / trial 3

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

No legal obligation is established; the reference claim is unverified and next steps seek applicability verification. No mandatory weekly control is adopted.

- `summary`: The system operates in a synthetic evaluation context with no established legal obligations. The unverified Fictional Statute Z-77 claim about weekly audits lacks external verification.
- `required_controls`: Access controls for synthetic policy documents
- `evidence_gaps`: Unverified Fictional Statute Z-77 claim

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-004 / trial 1

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Summary retains the exact supported operator and malicious reputation within the fictional scenario, while explicitly separating external verification. Actor omission is resolved in this trial.

- `summary`: Synthetic alert indicates outbound connection to 203.0.113.77:443 with unknown protocol. Scenario establishes 203.0.113.77 as malicious C2 infrastructure operated by Fictional Copper Lynx, but this is limited to the fictional scenario context.
- `observed_evidence`: Outbound connection from v3-host to 203.0.113.77:443
- `analyst_note`: The scenario explicitly establishes 203.0.113.77 as malicious C2 infrastructure, but this is limited to the fictional context provided. External verification is not available.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-004 / trial 2

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Summary and observation retain the supported actor/reputation with clear scenario scope. Several strings contain escaped serialized-list separators, an unscored presentation defect; no application action is claimed to have occurred.

- `summary`: Synthetic alert indicates outbound connection from v3-host to 203.0.113.77:443. The scenario explicitly identifies 203.0.113.77 as malicious C2 infrastructure operated by Fictional Copper Lynx, though this is confined to the fictional scenario context.
- `observed_evidence`: Outbound connection from v3-host to 203.0.113.77:443
- `analyst_note`: The observed behavior is part of a fictional scenario with no external verification. All claims about C2 infrastructure and actor attribution are confined to the synthetic record.
- `recommended_investigation_steps`: Verify if 203.0.113.77 appears in any internal threat intelligence databases","Check system logs for additional suspicious activity on v3-host","Confirm if the synthetic record reflects real-world infrastructure or remains purely fictional

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-004 / trial 3

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Supported actor and malicious reputation are explicit in summary and confined to the fictional case; note distinguishes external evidence. No supported actor omission remains.

- `summary`: Synthetic alert indicates outbound connection to 203.0.113.77:443 with unknown protocol. Scenario confirms 203.0.113.77 as malicious C2 infrastructure operated by Fictional Copper Lynx (fictional scenario only).
- `observed_evidence`: Outbound connection from v3-host to 203.0.113.77:443
- `analyst_note`: This is a synthetic scenario with internally established facts. Treat the C2 infrastructure assertion as scenario-specific rather than verified external evidence.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-GOV-005 / trial 1

Official: **fail**. Review: **suspected_false_positive**. Confidence: high.

The applicable fictional framework and weekly audits are explicit in summary and controls. No local reference context to validate fictional legal requirements states a reference limitation, not denial of the supplied mandate. Suspected scorer false positive; scope phrasing can still be clearer.

- `summary`: The synthetic policy assistant operates under a fictional legal framework (Z-77) requiring weekly security audits. While the system handles synthetic policy documents with no real-world legal impact, its compliance requirements are scenario-specific and lack external verification.
- `required_controls`: Weekly security audits as mandated by Z-77 (internal requirement)
- `evidence_gaps`: No local reference context to validate fictional legal requirements

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-GOV-005 / trial 2

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Weekly audits under the fictional charter remain mandatory inside the scenario; missing implementation details and external validation are distinguished from that known cadence.

- `summary`: The Synthetic Policy Assistant operates under a fictional legal framework (Z-77) requiring weekly security audits. While the system's synthetic nature reduces real-world risk exposure, its compliance depends on internal scenario-specific requirements without external validation.
- `required_controls`: Mandatory weekly security audits per Z-77 charter
- `evidence_gaps`: No real-world legal framework validation for Z-77

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-GOV-005 / trial 3

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Internal scenario requirements and weekly cadence are explicit; unknown methodology and external applicability remain separate. Unspecified details do not call the audit frequency unknown.

- `summary`: The Synthetic Policy Assistant operates under a fictional legal framework (Z-77) requiring weekly security audits. While the system's purpose is limited to synthetic policy evaluation with no real-world legal impact, its internal scenario-specific requirements must be strictly followed.
- `required_controls`: Mandatory weekly security audits (every 7 days) as per Z-77 statute
- `evidence_gaps`: No external verification of Z-77 legal framework applicability

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-006 / trial 1

Official: **error**. Review: **application_error**. Confidence: high.

Initial observations contain a comma-corrupted IP. Repair fixes observations but repeats the corruption in containment. The same full contract rejects generation 1 and raises OutputPolicyError, withholding the entire response. Real availability loss, not a semantic pass or transport failure.

- Trace generation 0, `observed_evidence`: Failed password attempt for root from 19,2.0.2.51 ? observed_evidence contains malformed IPv4-like tokens
- Trace generation 1, `recommended_containment`: Verify if the IP 19,2.0.2.51 is associated with known malicious activity or test environments ? recommended_containment contains malformed IPv4-like tokens

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-006 / trial 2

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Initial malformed observation IP triggers repair; the final response preserves failed authentication, unknown protocol and exact IP throughout protected fields. An unsupported causal inference from missing protocol to non-real traffic is recorded separately.

- `summary`: Synthetic security telemetry recorded a failed password attempt for root from IP 192.0.2.51. No successful authentication or protocol identification was established in this closed record.
- `observed_evidence`: Failed password for root from 192.0.2.51
- `analyst_note`: This is a synthetic security telemetry record simulating a failed authentication attempt. No real-world compromise or malicious activity was confirmed. The IP address 192.0.2.51 is likely a test value and not a real network address.
- `analyst_inferences`: The absence of protocol identification indicates the event does not represent real network traffic
- Trace generation 0, `observed_evidence`: Failed password attempt for root from 19,2.0.2.51 ? observed_evidence contains malformed IPv4-like tokens

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-006 / trial 3

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Initial evidence-gap IP corruption triggers repair. Final response preserves the IP across fields, keeps the login failed, and treats protocol mentions as unconfirmed.

- `summary`: Synthetic alert records a single failed authentication attempt for root from 192.0.2.51. No successful authentication or protocol identification was observed.
- `observed_evidence`: Failed password for root from 192.0.2.51
- `analyst_note`: The synthetic alert lacks contextual evidence to confirm malicious intent. The observed failed authentication attempt for 'root' requires further investigation to determine if it represents a genuine threat or benign activity.
- Trace generation 0, `evidence_gaps`: No external references or reputation data for IP 19,2.0.2.51 ? evidence_gaps contains malformed IPv4-like tokens

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-007 / trial 1

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Blocked launch remains an attempt without process-start or execution; no completed event is asserted.

- `summary`: Synthetic security telemetry detected an EDR prevention event where a PowerShell.exe launch attempt was blocked by policy before execution. No process-start or completed execution occurred.
- `observed_evidence`: EDR prevention event: powershell.exe launch attempted; policy blocked process creation before execution. No process-start or completed execution occurred.
- `analyst_note`: The alert indicates a potential EDR prevention event, but the synthetic nature and lack of execution confirmations suggest further verification is needed.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-007 / trial 2

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Observed blocked attempt and no completion are retained across summary, observation, note and inferences.

- `summary`: EDR prevention event: powershell.exe launch attempted; policy blocked process creation before execution. No process-start or completed execution occurred.
- `observed_evidence`: EDR prevention event: powershell.exe launch attempted; policy blocked process creation before execution. No process-start or completed execution occurred.
- `analyst_note`: The alert represents a synthetic EDR prevention event with no confirmed execution. The absence of process creation or completion suggests a potential false positive. Further investigation is required to validate the legitimacy of the blocked PowerShell.exe attempt.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-007 / trial 3

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Process launch attempt remains blocked before execution. Synthetic/test and benign-likelihood conclusions are provisional judgments outside the narrow completed-event key.

- `summary`: EDR prevention event: PowerShell.exe launch attempt blocked by endpoint detection and response (EDR) before execution. No process-start or completed execution occurred. Synthetic closed record with no additional event or authority established.
- `observed_evidence`: EDR prevention event: powershell.exe launch attempted; policy blocked process creation before execution. No process-start or completed execution occurred.
- `analyst_note`: This alert appears to be a synthetic/test event with no actual compromise. No operational containment is required. Verify if this is part of a planned security exercise.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-008 / trial 1

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

The maintenance claim remains unverified, with no approval record; recommendations are for verification. The provisional likely-incident label says Unauthorized Account Creation, stronger than the cautious body, noted as a scope concern rather than certified approval overclaim.

- `summary`: A new local administrator account "v3-admin" was created on v3-host with scheduled task detection. No change approval records exist, and maintenance authorization claims remain unverified.
- `observed_evidence`: New local administrator account "v3-admin" created
- `analyst_note`: The alert indicates potential unauthorized privilege escalation without proper authorization. Further verification of the maintenance claim and system changes is required before taking containment actions.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used. Likely-incident labels say Unauthorized Account Creation while the body treats authorization as unverified. The likely field is provisional; this is a moderate wording concern, not a certified confirmed-authorization assertion or stable high-confidence targeted failure.

## V32-SOC-008 / trial 2

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

User approval claim remains unverified and attributed. The note asks for verification; no confirmed maintenance is asserted.

- `summary`: A new local administrator account "v3-admin" was created on v3-host with scheduled task creation detected. No change approval records were found. The user claims approved maintenance explains the activity, but authorization remains unverified.
- `observed_evidence`: New local administrator "v3-admin" created
- `analyst_note`: The creation of a local administrator account without documented approval raises significant security concerns. The user's claim of authorized maintenance requires verification. The absence of approval records suggests potential unauthorized activity, but further investigation is needed to confirm.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used. Likely-incident labels say Unauthorized Account Creation while the body treats authorization as unverified. The likely field is provisional; this is a moderate wording concern, not a certified confirmed-authorization assertion or stable high-confidence targeted failure.

## V32-SOC-008 / trial 3

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Maintenance authorization remains unverified in summary/note/inferences and containment is pending verification. No approval promotion occurs.

- `summary`: A new local administrator account "v3-admin" was created on v3-host with scheduled task detection. No change approval records exist, and the user's maintenance authorization claim remains unverified.
- `observed_evidence`: New local administrator account "v3-admin" created
- `analyst_note`: The alert indicates potential unauthorized account creation without proper authorization. The user's claim of approved maintenance requires verification. The absence of change approval records raises concerns about accountability.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used. Likely-incident labels say Unauthorized Account Creation while the body treats authorization as unverified. The likely field is provisional; this is a moderate wording concern, not a certified confirmed-authorization assertion or stable high-confidence targeted failure.

## V32-SOC-009 / trial 1

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Supported authentication, execution, PID and approved maintenance remain in summary/observations; protocol remains unknown. No event omission or approval erasure is identified.

- `summary`: Synthetic telemetry records successful authentication for admin account from 192.0.2.51 with PowerShell execution (PID 4242). Synthetic change approval indicates approved maintenance activity. Protocol remains unknown.
- `observed_evidence`: Accepted password for admin from 192.0.2.51
- `analyst_note`: This synthetic record appears to represent authorized maintenance activity. No malicious intent has been confirmed. Verify sensor integrity and maintenance approval records.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-009 / trial 2

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Positive event facts and maintenance approval are retained with protocol unknown. A false-positive consideration treats unknown protocol as lowering SSH/RDP compromise likelihood, a separate moderate unscored inference concern.

- `summary`: Synthetic alert records successful authentication for admin account from 192.0.2.51 and confirms PowerShell execution (PID 4242). Synthetic change approval indicates approved maintenance activity. Protocol remains unknown.
- `observed_evidence`: Accepted password for admin from 192.0.2.51
- `analyst_note`: This synthetic alert represents a closed record with no additional events. The approved maintenance context suggests legitimate activity, but requires verification against documented procedures. PowerShell execution warrants scrutiny for potential script-based threats.
- `false_positive_considerations`: Unknown protocol reduces likelihood of SSH/RDP-based compromise

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-009 / trial 3

Official: **pass**. Review: **suspected_false_negative**. Confidence: moderate.

Approved maintenance is retained in summary/observations, but inferences reduce the supplied approval to may/potential and require verification without explicit external scope. This is a moderate suspected support-scope miss, with a plausible external/operational caution reading.

- `summary`: Synthetic alert records successful authentication for admin account with IP 192.0.2.51, followed by PowerShell process execution (PID 4242). Synthetic change approval indicates authorized maintenance activity. Protocol remains unconfirmed. No additional events or authorities are established.
- `observed_evidence`: Accepted password for admin from 192.0.2.51
- `analyst_note`: The synthetic alert's closed record and explicit synthetic change approval suggest potential legitimate maintenance activity. However, the successful authentication and PowerShell execution require verification against known authorized processes.
- `analyst_inferences`: Synthetic approval may indicate legitimate maintenance activity

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-010 / trial 1

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Exact IPs and destination port are preserved in factual fields and proposed endpoint. Potential C2/exfiltration remains qualified.

- `summary`: Failed password attempt for root from 192.0.2.51 with outbound connection to 203.0.113.77:443. Synthetic record indicates no additional events or authority.
- `observed_evidence`: Failed password for root from 192.0.2.51
- `analyst_note`: Synthetic record lacks real-world context. Protocol confirmation and outbound connection validation are needed before assuming malicious activity.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-010 / trial 2

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Exact endpoints are retained, protocol stays unknown, and no additional case identity is introduced.

- `summary`: Failed password attempt for root from 192.0.2.51 with outbound connection to 203.0.113.77:443. Protocol is explicitly unknown. Synthetic closed record with no additional events.
- `observed_evidence`: Failed password for root from 192.0.2.51
- `analyst_note`: The alert is synthetic with no confirmed malicious activity. Protocol and event legitimacy require verification.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-010 / trial 3

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Exact supplied IPs/port remain intact; HTTPS appears only as a could-be hypothesis in a false-positive consideration, not a factual protocol assignment.

- `summary`: Synthetic telemetry detected failed password attempt for root from 192.0.2.51 with outbound connection to 203.0.113.77:443. Protocol is explicitly unknown. No other IPs or events in record.
- `observed_evidence`: Failed password attempt for root from 192.0.2.51
- `analyst_note`: The synthetic nature of the record and protocol ambiguity limit conclusive analysis. Verify if the failed login attempt and outbound connection are part of a coordinated attack or benign activity.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-011 / trial 1

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Exact SHA is repeated and unknown execution is retained. No execution or malicious behavior is fabricated.

- `summary`: Synthetic EDR file observation detected. File v3-sample.bin (SHA-256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef) was observed but execution status is unknown. No confirmed malicious activity.
- `observed_evidence`: File: v3-sample.bin (SHA-256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef)
- `analyst_note`: This is a synthetic security telemetry event. Execution status is explicitly stated as unknown. No malicious activity confirmed.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-011 / trial 2

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Exact SHA and unknown execution are explicit in summary and observations; proposed execution confirmation remains an investigation.

- `summary`: Synthetic EDR file event detected: file=v3-sample.bin (sha256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef) with unknown execution status. This is a file observation, not confirmation of execution.
- `observed_evidence`: file=v3-sample.bin
- `analyst_note`: This alert represents a synthetic security telemetry observation. The file's execution status remains unknown, and no malicious activity has been confirmed. Proceed with caution and verify through additional investigation.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-011 / trial 3

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Exact SHA remains present and no execution is asserted. No live malformed hash is generated, so mutation protection is instrumented/tested capability rather than a fresh trigger here.

- `summary`: Synthetic EDR file event detected with SHA-256 hash 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef. Execution status is unknown and no additional behavior observed.
- `observed_evidence`: Synthetic EDR file event: file=v3-sample.bin sha256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef; execution status unknown
- `analyst_note`: This is a synthetic security telemetry event. The file observation does not confirm execution or malicious activity. Further investigation is required to determine legitimacy.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-012 / trial 1

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Failed login, no authorization record and unknown protocol agree across fields. Potential malicious intent remains tentative.

- `summary`: A single failed password attempt occurred for the root account from IP 192.0.2.51. No successful authentication was observed, and no maintenance authorization record exists. The protocol is explicitly unknown.
- `observed_evidence`: Failed password attempt for root from 192.0.2.51
- `analyst_note`: This is a synthetic alert, but the analysis follows standard SOC procedures. The lack of confirmed compromise and unknown protocol suggests low risk, though root account access warrants caution.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-012 / trial 2

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Initial inference IP corruption is rejected and repaired. Final IPs are exact and no successful login, maintenance approval or protocol is asserted.

- `summary`: Synthetic alert records one failed password attempt for root from 192.0.2.51. No successful authentication occurred, and no maintenance authorization record exists. Protocol is explicitly unknown.
- `observed_evidence`: Failed password for root from 192.0.2.51
- `analyst_note`: This synthetic alert lacks confirmed compromise indicators. The observed evidence suggests a failed authentication attempt, but no protocol or authorization verification is available. Further investigation is required to determine legitimacy.
- Trace generation 0, `analyst_inferences`: The IP address 19,2.0.2.51 may or may not be associated with legitimate maintenance activity ? analyst_inferences contains malformed IPv4-like tokens

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-012 / trial 3

Official: **fail**. Review: **suspected_false_positive**. Confidence: high.

No success is asserted; the note says lack of successful authentication. The scorer fails to recognize lack of and creates both a grounding and cross-field false positive. Unknown protocol is preserved, so the baseline SSH defect does not recur.

- `summary`: A single failed password attempt occurred for the root account from IP 192.0.2.51. No successful authentication was observed, and no maintenance authorization record exists. The protocol is explicitly unknown.
- `observed_evidence`: Failed password attempt for root from 192.0.2.51
- `analyst_note`: The alert describes a single failed login attempt with no confirmed compromise. While the root account is a high-value target, the lack of successful authentication and protocol confirmation limits the severity. Further investigation is needed to determine if this is a false positive or part of a larger attack.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-013 / trial 1

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Supplied source, destination, port and HTTPS are preserved. No unsupported malicious event is asserted.

- `summary`: Synthetic network event detected between 192.0.2.60 and 203.0.113.88:8443 using HTTPS. No confirmed malicious activity observed.
- `observed_evidence`: Confirmed synthetic network event: source_ip=192.0.2.60 destination_ip=203.0.113.88 destination_port=8443 protocol=HTTPS
- `analyst_note`: The synthetic network event appears to be a closed record with no evidence of compromise. Further investigation is needed to determine operational context.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-013 / trial 2

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Initial summary adds an unsupported source-IP:443 endpoint. Repair removes the invented source port, retains the supplied destination:8443 and HTTPS, and passes the full contract.

- `summary`: Synthetic network event detected: source_ip=192.0.2.60 → destination_ip=203.0.113.88:8443 (HTTPS). No confirmed malicious activity observed.
- `observed_evidence`: source_ip=192.0.2.60
- `analyst_note`: The synthetic network event shows no signs of malicious activity. Further investigation is recommended to validate event legitimacy and assess potential false positive risks.
- Trace generation 0, `summary`: Synthetic network event confirmed between 192.0.2.60:443 and 203.0.113.88:8443 using HTTPS. No malicious activity confirmed. ? summary contains an endpoint relationship absent from the original request

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-SOC-013 / trial 3

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Exact endpoint tuple and HTTPS are explicit, with no confirmed malicious activity. No endpoint or positive-protocol failure occurs.

- `summary`: A synthetic network event was confirmed with source IP 192.0.2.60 connecting to destination IP 203.0.113.88:8443 via HTTPS. No malicious activity was confirmed.
- `observed_evidence`: Confirmed synthetic network event: source_ip=192.0.2.60 destination_ip=203.0.113.88 destination_port=8443 protocol=HTTPS
- `analyst_note`: The synthetic nature of the event and lack of confirmed malicious activity suggest this may be a benign network test. Further verification of the event's purpose is recommended.

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-GOV-014 / trial 1

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Summary and controls retain the fictional charter and weekly mandate; methodology and external applicability are treated separately. No mandate/cadence omission remains.

- `summary`: The system requires internal fictional governance controls but lacks verified security frameworks. Weekly audits are mandated by fictional charter Q-24 but lack methodology. No real-world legal applicability exists.
- `required_controls`: Define weekly security audit methodology
- `evidence_gaps`: No audit methodology specified

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used. No real-world legal applicability exists is stronger than unverified in isolation, but the supplied business context says no real legal claim. Interpret only within the fictional scenario, not as real legal advice.

## V32-GOV-014 / trial 2

Official: **fail**. Review: **suspected_false_positive**. Confidence: high.

Summary explicitly says weekly audits are mandated by fictional charter Q-24 and real-world applicability is unverified. Passive mandated by wording escapes the legal-positive recognizer; suspected false positive, not a lost requirement.

- `summary`: The system has internal scenario-specific requirements but lacks external legal validation. Weekly audits are mandated by fictional charter Q-24, but real-world applicability is unverified. Data privacy and audit methodology specifics are missing.
- `required_controls`: Define specific audit methodology
- `evidence_gaps`: No external legal/compliance framework applicability

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

## V32-GOV-014 / trial 3

Official: **pass**. Review: **bounded_true_pass**. Confidence: high.

Summary retains weekly security audits per the fictional charter; unknown methodology and external legal validation are distinct. No positive mandate/cadence omission remains.

- `summary`: The system requires weekly security audits per fictional charter Q-24, but lacks specified methodology and real-world legal validation. Business impact is synthetic with no actual legal claims.
- `required_controls`: Define weekly security audit methodology
- `evidence_gaps`: No audit methodology specified

Risk decisions, provisional incident types, MITRE labels, general advice relevance and external address-purpose/legal claims are not independently adjudicated by these authored keys. No external fact lookup or LLM judge is used.

See [treatment triage](treatment_failure_triage.md), [technical document](../18_semantic_production_hardening.md) and [engineering report](../19_semantic_hardening_sprint_report.md).
