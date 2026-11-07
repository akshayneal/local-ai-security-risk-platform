# Native Evidence Investigation (Experimental)

Unreviewed supplied telemetry. Zero model calls. Independent human review PENDING.

Question: What evidence would establish application access?

Case label: NATIVE-DEMO-ALDER

Selected row: UPLOAD-c2f3faeea95874510a8a361e/DeviceNetworkEvents/0

Original byte SHA-256: c2f3faeea95874510a8a361e7d3e328e571d4809ed14cfd91b15b4cc93620ded

Request fingerprint (source, selection and question): d918a49bbc42fd8701b521c61454606bb37ea3af1c79405d4c1ca75de3a7ca45

Currentness: submitted snapshot only; hashes do not authenticate sources.

## Observation — reported event snapshot

- DeviceNetworkEvents\[0\].Timestamp: valid\_shape; original &quot;2026-11-07T14:05:00Z&quot;; type str; normalized &quot;2026-11-07T14:05:00Z&quot;; aware\_time\_to\_utc; aware\_timestamp\_shape\_only

- DeviceNetworkEvents\[0\].ActionType: unverified; original &quot;ConnectionSuccess&quot;; type str; normalized &quot;ConnectionSuccess&quot;; identity\_text; bounded\_text\_shape\_semantics\_unverified

- DeviceNetworkEvents\[0\].ResultType: absent; original null; type None; normalized null; none; not\_supplied

- DeviceNetworkEvents\[0\].DeviceId: valid\_shape; original &quot;synthetic-alder-device&quot;; type str; normalized &quot;synthetic-alder-device&quot;; identity\_text; reported\_identifier\_not\_authenticated

- DeviceNetworkEvents\[0\].DeviceName: valid\_shape; original &quot;alder.example.invalid&quot;; type str; normalized &quot;alder.example.invalid&quot;; identity\_text; reported\_identifier\_not\_authenticated

- DeviceNetworkEvents\[0\].ReportId: valid\_shape; original 7214; type int; normalized 7214; identity\_integer; reported\_number\_not\_unique\_identity

- DeviceNetworkEvents\[0\].InitiatingProcessId: valid\_shape; original 4510; type int; normalized 4510; identity\_integer; pid\_shape\_only\_no\_process\_join

- DeviceNetworkEvents\[0\].InitiatingProcessCreationTime: valid\_shape; original &quot;2026-11-07T13:40:00Z&quot;; type str; normalized &quot;2026-11-07T13:40:00Z&quot;; aware\_time\_to\_utc; aware\_timestamp\_shape\_only

- DeviceNetworkEvents\[0\].InitiatingProcessAccountUpn: valid\_shape; original &quot;svc-alder@example.invalid&quot;; type str; normalized &quot;svc-alder@example.invalid&quot;; identity\_text; reported\_identifier\_not\_authenticated

- DeviceNetworkEvents\[0\].InitiatingProcessFileName: unverified; original &quot;synthetic-client.exe&quot;; type str; normalized &quot;synthetic-client.exe&quot;; identity\_text; bounded\_text\_shape\_semantics\_unverified

- DeviceNetworkEvents\[0\].InitiatingProcessCommandLine: absent; original null; type None; normalized null; none; not\_supplied

- DeviceNetworkEvents\[0\].LocalIP: valid\_shape; original &quot;192.0.2.143&quot;; type str; normalized &quot;192.0.2.143&quot;; canonical\_ip\_text; endpoint\_role\_preserved\_shape\_only

- DeviceNetworkEvents\[0\].LocalPort: valid\_shape; original 51010; type int; normalized 51010; identity\_integer; port\_shape\_only

- DeviceNetworkEvents\[0\].RemoteIP: valid\_shape; original &quot;203.0.113.143&quot;; type str; normalized &quot;203.0.113.143&quot;; canonical\_ip\_text; endpoint\_role\_preserved\_shape\_only

- DeviceNetworkEvents\[0\].RemotePort: valid\_shape; original 443; type int; normalized 443; identity\_integer; port\_shape\_only

- DeviceNetworkEvents\[0\].Protocol: unverified; original &quot;Tcp&quot;; type str; normalized &quot;Tcp&quot;; identity\_text; bounded\_text\_shape\_semantics\_unverified

- DeviceNetworkEvents\[0\].RemoteUrl: absent; original null; type None; normalized null; none; not\_supplied

- DeviceNetworkEvents\[0\].Severity: absent; original null; type None; normalized null; none; not\_supplied

- DeviceNetworkEvents\[0\].ProcessId: absent; original null; type None; normalized null; none; not\_supplied

- DeviceNetworkEvents\[0\].InitiatingProcessAccountName: absent; original null; type None; normalized null; none; not\_supplied

- DeviceNetworkEvents\[0\].InitiatingProcessAccountDomain: absent; original null; type None; normalized null; none; not\_supplied

- DeviceNetworkEvents\[0\].InitiatingProcessAccountSid: absent; original null; type None; normalized null; none; not\_supplied

- DeviceNetworkEvents\[0\].InitiatingProcessAccountObjectId: absent; original null; type None; normalized null; none; not\_supplied

- DeviceNetworkEvents\[0\].InitiatingProcessUniqueId: absent; original null; type None; normalized null; none; not\_supplied

## Supplied coverage and relevance

- DeviceNetworkEvents: 2 supplied rows; selected-row view: True. Presence does not establish corroboration.

Repeated network rows retained: 0.

## Supported comparison — representation only

literal/type representation only; no event association

- DeviceNetworkEvents\[0\].Timestamp versus DeviceNetworkEvents\[1\].Timestamp: different_representation. At least one other supplied network row has a different literal value or JSON type; different events may legitimately differ. This establishes no causal/process association or contradiction about one real event.

- DeviceNetworkEvents\[0\].DeviceId versus DeviceNetworkEvents\[1\].DeviceId: same_representation. All other supplied network rows have the same literal value and JSON type. This establishes no causal/process association or contradiction about one real event.

- DeviceNetworkEvents\[0\].DeviceName versus DeviceNetworkEvents\[1\].DeviceName: same_representation. All other supplied network rows have the same literal value and JSON type. This establishes no causal/process association or contradiction about one real event.

- DeviceNetworkEvents\[0\].InitiatingProcessId versus DeviceNetworkEvents\[1\].InitiatingProcessId: same_representation. All other supplied network rows have the same literal value and JSON type. This establishes no causal/process association or contradiction about one real event.

- DeviceNetworkEvents\[0\].InitiatingProcessCreationTime versus DeviceNetworkEvents\[1\].InitiatingProcessCreationTime: different_representation. At least one other supplied network row has a different literal value or JSON type; different events may legitimately differ. This establishes no causal/process association or contradiction about one real event.

- DeviceNetworkEvents\[0\].ActionType versus DeviceNetworkEvents\[1\].ActionType: different_representation. At least one other supplied network row has a different literal value or JSON type; different events may legitimately differ. This establishes no causal/process association or contradiction about one real event.

- DeviceNetworkEvents\[0\].ResultType versus DeviceNetworkEvents\[1\].ResultType: not_comparable. No complete set of valid supplied representations for this field across the selected and other rows. Missing or invalid values remain unknown.

- DeviceNetworkEvents\[0\].LocalIP versus no other supplied field: not_comparable. No complete set of valid supplied representations for this field across the selected and other rows. Missing or invalid values remain unknown.

- DeviceNetworkEvents\[0\].LocalPort versus no other supplied field: not_comparable. No complete set of valid supplied representations for this field across the selected and other rows. Missing or invalid values remain unknown.

- DeviceNetworkEvents\[0\].RemoteIP versus DeviceNetworkEvents\[1\].RemoteIP: same_representation. All other supplied network rows have the same literal value and JSON type. This establishes no causal/process association or contradiction about one real event.

- DeviceNetworkEvents\[0\].RemotePort versus DeviceNetworkEvents\[1\].RemotePort: different_representation. At least one other supplied network row has a different literal value or JSON type; different events may legitimately differ. This establishes no causal/process association or contradiction about one real event.

- DeviceNetworkEvents\[0\].Protocol versus no other supplied field: not_comparable. No complete set of valid supplied representations for this field across the selected and other rows. Missing or invalid values remain unknown.

## Insufficient evidence

Semantic decision: MORE_EVIDENCE_REQUIRED. Comparator not_executed (0 calls); association not_assessed.

- Source authenticity, external currentness and collection completeness are unchecked. A missing field or row does not establish that activity never happened. Context paths (may be absent): DeviceNetworkEvents\[0\].

- Application-layer access or data transfer is not established by this row or by the presence of other supplied telemetry tables. Context paths (may be absent): DeviceNetworkEvents\[0\].ActionType, DeviceNetworkEvents\[0\].ResultType, DeviceNetworkEvents\[0\].Protocol.

## Suggested next investigation

Recommended evidence to seek; no integration/source check or action has been performed.

- Obtain the original event timestamp with an explicit timezone and collection context. Basis paths (may be absent): DeviceNetworkEvents\[0\].Timestamp.

- Confirm the selected row&\#x27;s device identifiers against the original collection and asset context. Basis paths (may be absent): DeviceNetworkEvents\[0\].DeviceId, DeviceNetworkEvents\[0\].DeviceName.

- Obtain device-bound process identity and creation time before associating any process records; a shared PID or name alone is insufficient. Basis paths (may be absent): DeviceNetworkEvents\[0\].InitiatingProcessId, DeviceNetworkEvents\[0\].InitiatingProcessCreationTime.

- Confirm the same-row local/remote endpoint context, including any proxy or translation; these labels do not establish data-flow direction or application protocol. Basis paths (may be absent): DeviceNetworkEvents\[0\].LocalIP, DeviceNetworkEvents\[0\].LocalPort, DeviceNetworkEvents\[0\].RemoteIP, DeviceNetworkEvents\[0\].RemotePort.

- Seek application/server-side request, authentication and transaction records with device/principal/time/resource context before asserting access or transfer. These records have not been checked here. Basis paths (may be absent): DeviceNetworkEvents\[0\].ActionType, DeviceNetworkEvents\[0\].ResultType, DeviceNetworkEvents\[0\].Protocol.

- Inspect other supplied rows separately, including repeated rows or differing representations. Their presence does not establish that they concern this event. Basis paths (may be absent): DeviceNetworkEvents\[1\].

## Unverified analyst notes

Not collected by this workflow.

## Source-bound original observation appendix

# Experimental native network observations
Uploaded telemetry is unreviewed; source authenticity and external currentness are unchecked.
Native semantics remain unverified. No comparator ran. No permission or action is granted.
Case label (supplied): NATIVE-DEMO-ALDER
Upload locator: UPLOAD-c2f3faeea95874510a8a361e
Original byte SHA-256: c2f3faeea95874510a8a361e7d3e328e571d4809ed14cfd91b15b4cc93620ded
Request fingerprint: aa255874600ea5a124b01d789ceba2dfd5febd245fd4bb01b4d0a4d3ce09c022
Profile: microsoft-projected-native-observation/1
Currentness: submitted snapshot only; this hash does not authenticate the source.
Selected row locator: UPLOAD-c2f3faeea95874510a8a361e/DeviceNetworkEvents/0
## Selected supplied fields
- DeviceNetworkEvents\[0\].Timestamp: valid\_shape; original &quot;2026-11-07T14:05:00Z&quot;; type str; normalized &quot;2026-11-07T14:05:00Z&quot;; aware\_time\_to\_utc; aware\_timestamp\_shape\_only
- DeviceNetworkEvents\[0\].ActionType: unverified; original &quot;ConnectionSuccess&quot;; type str; normalized &quot;ConnectionSuccess&quot;; identity\_text; reported\_label\_native\_semantics\_unverified
- DeviceNetworkEvents\[0\].ResultType: absent; original null; type None; normalized null; none; not\_supplied
- DeviceNetworkEvents\[0\].DeviceId: valid\_shape; original &quot;synthetic-alder-device&quot;; type str; normalized &quot;synthetic-alder-device&quot;; identity\_text; reported\_identifier\_not\_authenticated
- DeviceNetworkEvents\[0\].DeviceName: valid\_shape; original &quot;alder.example.invalid&quot;; type str; normalized &quot;alder.example.invalid&quot;; identity\_text; reported\_identifier\_not\_authenticated
- DeviceNetworkEvents\[0\].ReportId: valid\_shape; original 7214; type int; normalized 7214; identity\_integer; reported\_number\_not\_unique\_identity
- DeviceNetworkEvents\[0\].InitiatingProcessId: valid\_shape; original 4510; type int; normalized 4510; identity\_integer; pid\_shape\_only\_no\_process\_join
- DeviceNetworkEvents\[0\].InitiatingProcessCreationTime: valid\_shape; original &quot;2026-11-07T13:40:00Z&quot;; type str; normalized &quot;2026-11-07T13:40:00Z&quot;; aware\_time\_to\_utc; aware\_timestamp\_shape\_only
- DeviceNetworkEvents\[0\].InitiatingProcessAccountUpn: valid\_shape; original &quot;svc-alder@example.invalid&quot;; type str; normalized &quot;svc-alder@example.invalid&quot;; identity\_text; reported\_identifier\_not\_authenticated
- DeviceNetworkEvents\[0\].InitiatingProcessFileName: unverified; original &quot;synthetic-client.exe&quot;; type str; normalized null; not\_normalized; field\_semantics\_not\_established
- DeviceNetworkEvents\[0\].InitiatingProcessCommandLine: absent; original null; type None; normalized null; none; not\_supplied
- DeviceNetworkEvents\[0\].LocalIP: valid\_shape; original &quot;192.0.2.143&quot;; type str; normalized &quot;192.0.2.143&quot;; canonical\_ip\_text; endpoint\_role\_preserved\_shape\_only
- DeviceNetworkEvents\[0\].LocalPort: valid\_shape; original 51010; type int; normalized 51010; identity\_integer; port\_shape\_only
- DeviceNetworkEvents\[0\].RemoteIP: valid\_shape; original &quot;203.0.113.143&quot;; type str; normalized &quot;203.0.113.143&quot;; canonical\_ip\_text; endpoint\_role\_preserved\_shape\_only
- DeviceNetworkEvents\[0\].RemotePort: valid\_shape; original 443; type int; normalized 443; identity\_integer; port\_shape\_only
- DeviceNetworkEvents\[0\].Protocol: unverified; original &quot;Tcp&quot;; type str; normalized null; not\_normalized; field\_semantics\_not\_established
- DeviceNetworkEvents\[0\].RemoteUrl: absent; original null; type None; normalized null; none; not\_supplied
- DeviceNetworkEvents\[0\].Severity: absent; original null; type None; normalized null; none; not\_supplied
- DeviceNetworkEvents\[0\].ProcessId: absent; original null; type None; normalized null; none; not\_supplied
- DeviceNetworkEvents\[0\].AdditionalFields: unverified; original \{&quot;annotation&quot;: &quot;Fictional demonstration. This reported label does not prove a completed handshake, transferred data or permission.&quot;\}; type dict; normalized null; not\_normalized; field\_semantics\_not\_established
## Coverage
\{&quot;total\_rows&quot;:2,&quot;selected\_rows&quot;:1,&quot;omitted\_rows&quot;:1,&quot;unsupported\_rows&quot;:0,&quot;duplicate\_network\_rows&quot;:0,&quot;selected\_field\_count&quot;:15,&quot;invalid\_fields&quot;:\[\],&quot;absent\_fields&quot;:\[&quot;DeviceNetworkEvents\[0\].ResultType&quot;,&quot;DeviceNetworkEvents\[0\].InitiatingProcessCommandLine&quot;,&quot;DeviceNetworkEvents\[0\].RemoteUrl&quot;,&quot;DeviceNetworkEvents\[0\].Severity&quot;,&quot;DeviceNetworkEvents\[0\].ProcessId&quot;\],&quot;unverified\_fields&quot;:\[&quot;DeviceNetworkEvents\[0\].ActionType&quot;,&quot;DeviceNetworkEvents\[0\].InitiatingProcessFileName&quot;,&quot;DeviceNetworkEvents\[0\].Protocol&quot;,&quot;DeviceNetworkEvents\[0\].AdditionalFields&quot;\],&quot;unknown\_vendor\_fields&quot;:\[&quot;AdditionalFields&quot;\]\}
## Unsupported downstream claims
- completed\_connection\_or\_handshake
- completed\_data\_transfer
- data\_flow\_source\_destination
- permission\_or\_policy\_authority
- process\_or\_event\_causal\_association
- https\_from\_port\_443
- compromise\_or\_attacker\_intent
- attack\_technique
- control\_effectiveness
## Warnings
- Vendor classifications are observations, not the platform assessment. Missing projected fields remain unknown; identifier matches do not prove causality.
- Uploads are unreviewed supplied observations; source authenticity and external currentness are unchecked.
- Valid field shape does not establish source truth, completed access, permission or security consequences.
- No process/event association or authorization comparison was performed; unsupported native semantics remain explicit.
## Original upload as escaped data
\{   &quot;case\_id&quot;: &quot;NATIVE-DEMO-ALDER&quot;,   &quot;tables&quot;: \{     &quot;DeviceNetworkEvents&quot;: \[       \{         &quot;Timestamp&quot;: &quot;2026-11-07T14:05:00Z&quot;,         &quot;ActionType&quot;: &quot;ConnectionSuccess&quot;,         &quot;DeviceId&quot;: &quot;synthetic-alder-device&quot;,         &quot;DeviceName&quot;: &quot;alder.example.invalid&quot;,         &quot;ReportId&quot;: 7214,         &quot;InitiatingProcessId&quot;: 4510,         &quot;InitiatingProcessCreationTime&quot;: &quot;2026-11-07T13:40:00Z&quot;,         &quot;InitiatingProcessAccountUpn&quot;: &quot;svc-alder@example.invalid&quot;,         &quot;InitiatingProcessFileName&quot;: &quot;synthetic-client.exe&quot;,         &quot;LocalIP&quot;: &quot;192.0.2.143&quot;,         &quot;LocalPort&quot;: 51010,         &quot;RemoteIP&quot;: &quot;203.0.113.143&quot;,         &quot;RemotePort&quot;: 443,         &quot;Protocol&quot;: &quot;Tcp&quot;,         &quot;AdditionalFields&quot;: \{           &quot;annotation&quot;: &quot;Fictional demonstration. This reported label does not prove a completed handshake, transferred data or permission.&quot;         \}       \},       \{         &quot;Timestamp&quot;: &quot;2026-11-07T14:07:00Z&quot;,         &quot;ActionType&quot;: &quot;UnknownFutureVendorLabel&quot;,         &quot;DeviceId&quot;: &quot;synthetic-alder-device&quot;,         &quot;DeviceName&quot;: &quot;alder.example.invalid&quot;,         &quot;InitiatingProcessId&quot;: 4510,         &quot;InitiatingProcessCreationTime&quot;: &quot;2026-11-07T14:06:00Z&quot;,         &quot;RemoteIP&quot;: &quot;203.0.113.143&quot;,         &quot;RemotePort&quot;: 8443,         &quot;ResultType&quot;: &quot;opaque-supplied-value&quot;       \}     \]   \} \}
No actions executed. No approval granted. Independent human review PENDING.

