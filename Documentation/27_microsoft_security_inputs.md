# Local Microsoft Security input profile

All examples are synthetic. This adapter accepts projected rows, not a complete
vendor schema. It makes no Azure connection and needs no Microsoft credentials.
The existing SOC analyzer, output policy, one-repair limit and API are reused.

## Schema references

Official Microsoft Learn pages checked **2026-10-29** (field tables were readable;
the pages also display a generic authorization banner). No documentation text was
copied. Unknown row fields are retained as evidence; unsupported table names cause
an explicit rejection rather than silent loss.

- [Advanced hunting tables](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-schema-tables)
- [AlertInfo](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-alertinfo-table)
- [AlertEvidence](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-alertevidence-table)
- [DeviceProcessEvents](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-deviceprocessevents-table)
- [DeviceNetworkEvents](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicenetworkevents-table)
- [DeviceLogonEvents](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicelogonevents-table)
- [SigninLogs](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/signinlogs)
- [SecurityIncident](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/securityincident)

## Analyst practice

`AlertInfo` describes alerts; `AlertEvidence` associates entities using `AlertId`.
The preview records exact matches, including multiple alerts and unmatched evidence.
An absent entity row is an evidence gap. Repeated rows remain in the raw evidence.

`DeviceProcessEvents` supplies command/process context. Compare device, process ID
and process creation time with initiating-process fields in `DeviceNetworkEvents`.
A matching name or nearby timestamp alone does not prove a causal relationship.
Process IDs can be reused. A network port alone does not establish an application
protocol. Keep raw `Protocol`, URL, ports and initiating-process context distinct.

`DeviceLogonEvents` adds device authentication context. `SigninLogs` supports
identity investigation: authentication details, results, device state and
Conditional Access are useful observations, not proof of legitimacy or compromise.
`SecurityIncident` supplies incident aggregation and vendor status/classification.
Disagreeing severities remain separate table/row observations; neither dictates the
platform assessment. The adapter does not interpret maliciousness.

Original concise KQL projections to export locally (choose suitable time bounds):

```kusto
AlertInfo
| where Timestamp > ago(1d)
| project Timestamp, AlertId, Title, Severity, Category, ServiceSource
| join kind=leftouter (
    AlertEvidence | project AlertId, EntityType, EvidenceRole, DeviceName, AccountUpn
  ) on AlertId
```

The joined projection is useful for learning. For the app bundle, export the
original tables separately to retain their field names and table provenance.

```kusto
DeviceNetworkEvents
| where Timestamp > ago(1d)
| project Timestamp, DeviceId, DeviceName, RemoteIP, RemotePort, Protocol,
          RemoteUrl, InitiatingProcessId, InitiatingProcessCreationTime
```

```kusto
SigninLogs
| where TimeGenerated > ago(1d)
| project TimeGenerated, UserPrincipalName, IPAddress, ResultType,
          AuthenticationRequirement, AuthenticationDetails,
          ConditionalAccessStatus, CorrelationId
```

## Input and preservation contract

JSON: `{"case_id":"SYN-001","tables":{"AlertInfo":[{"AlertId":"A"}]}}`.
Paste or upload UTF-8 JSON. CSV is one table per upload with explicit table selection
and case ID. CSV cells remain strings (including leading zeros and multiline
commands); dynamic JSON-looking cells are not implicitly reinterpreted. JSON dynamic
objects/arrays retain their supplied types. BOM and Windows CRLF are supported.
Duplicate JSON keys/CSV headers and inconsistent CSV row widths are rejected.

Limits: 80,000 bytes uploaded **and** compact canonical UTF-8; 7 known tables;
50 rows/table; 100 total rows; 64 fields/object; 128 characters/field name;
4,096 characters/string; nesting depth 8 (root depth zero); 5,000 values/containers.
At least one row and a nonblank case ID of at most 256 characters are required.
Projected optional vendor fields may be absent. Nonfinite numbers are rejected.
Checks happen before inference; JSON nesting is also bounded before decoding.

`NormalizedSocCase` contains the unchanged canonical `SocAlertRequest`, row counts,
entities, warnings, exact AlertId links and table/zero-based-row/field/value
observations. Canonical raw JSON sorts object keys and preserves row order,
duplicates and values. Byte formatting is normalized, not original file bytes.
Entity summaries are bounded to the existing label limit; indicator lists are
stably deduplicated and bounded to 100 entries of 1,024 characters. Values omitted
from previews remain in raw evidence. GUIDs, commands, hashes and ports are not
corrected or relabeled as malicious.

The existing prompt-only instruction quarantine still applies. The original
canonical request remains intact for provenance and deterministic output checks;
high-confidence instruction-like text can be removed from the model-facing copy.
This preserves the existing security boundary, not a guarantee against all injection.

Eight bundled cases cover MFA/CA uncertainty, command injection, unknown protocol on
443, severity disagreement, maintenance, multistage evidence, identity ambiguity and
a strong suspicious sequence. Example IPs/domains/identities are synthetic and do
not establish real reputation. No exam simulator or live integration is included.
