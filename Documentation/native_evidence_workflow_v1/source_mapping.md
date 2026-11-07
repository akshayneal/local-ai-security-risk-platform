# Experimental unreviewed native observation profile

Version: `native-observation-report/1`, profile
`microsoft-projected-native-observation/1`. Status: experimental, off by default.
The uploaded row is **supplied, unverified observation data**. This path does not
qualify a permission/policy source or run an authorization comparator. It does
not manufacture an approved `SourceReview` for an upload.

## Public-source basis and narrow decision

The [Microsoft DeviceNetworkEvents reference](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicenetworkevents-table)
describes connection-related telemetry and separately reported fields. It directs
users to the portal schema for supported ActionType details. Its public field
table alone does not establish a universal interpretation of each activity label.
The [network protection explanation](https://learn.microsoft.com/en-us/defender-endpoint/network-protection#network-protection-and-the-tcp-three-way-handshake)
provides a counterexample to treating ConnectionSuccess as completed handshake or
access. The earlier [14B feasibility memo](../qualified_soc_contract_v2/native_mapping_feasibility.md)
records the checked sources and remaining portal/version/protocol/collection gaps.

Decision: **MORE_EVIDENCE_REQUIRED** for native completion/authorization semantics.
The useful supported statement is that the selected uploaded
`DeviceNetworkEvents` row supplies its literal fields, including its ActionType.
`reported_event_class=supplied_DeviceNetworkEvents_row` names the supplied table
shape, not authenticated real activity. Every accepted label remains unverified;
there is no success-label allowlist or semantic translation.

## Input, identity and currentness

`NativeObservationRequest` permits only original `source_text`, JSON/CSV
`source_format`, strict zero-based `row_index` (0–49), the fixed CSV table name
`DeviceNetworkEvents` and CSV case label. CSV requires a nonblank case label;
JSON rejects alternate CSV case context, taking its case label only from the
bundle. Review, approved/current, source identity, permission and all other extra
request fields are forbidden. An ordinary caller cannot select an authority role.

Original UTF-8 bytes are limited to **64,000**, including BOM. Original text keeps
BOM, CRLF, whitespace and CSV representation; UTF-8 encoding it reproduces the
original upload. Existing seven-table parser/normalizer limits remain unchanged:
at most 50 rows/table, 100 total rows, bounded fields/depth/values/string lengths
and canonical representation. Duplicate JSON keys, CSV headers, row-width errors,
unsupported tables and malformed input fail with fixed codes. Optional malformed
selected field shapes remain retained observations with explicit invalid status.

`source_sha256` hashes the exact original bytes. `source_revision=sha256:<hash>`
and `upload_id` are application-derived content locators, not vendor identity,
authentication, anonymity or institutional authority. The request fingerprint
also binds format, row selection and CSV context, so identical bytes with a
different selected row keep the upload ID but acquire a different report binding.
`row_identity` is an upload/row locator, not an authenticated unique vendor event.

Currentness is `submitted_snapshot_only`, with external currentness `unchecked`.
No wall-clock timestamp, external source revision or approval is invented. The
source role is `observation_only`, review status `not_reviewed`, and case label
status `supplied_unverified`. There is no registry/current-review lookup here.

## Typed shapes and preserved originals

All original rows/fields/types remain in `original_bundle`, the separate existing
canonical representation and table/row/field observations. Selected field entries
retain original value/type and exact pointer; absent fields have an expected path
and no invented original pointer. Unknown fields are retained as unverified data.

| Field family | Shape/normalization | Semantic boundary |
| --- | --- | --- |
| Timestamp, process creation time | Explicit-zone instant; UTC normalization alongside exact original; malformed, absent or UTC-overflow states explicit | Not event/source authenticity or completion |
| PID fields | Strict integer or decimal string within bounded PID range; original leading zeros preserved | No cross-row/process association; PID reuse remains distinct rows |
| Local/remote ports | Integer or decimal string 0–65535; bool/float rejected as numeric shapes | No HTTPS/application inference from 443 |
| LocalIP, RemoteIP | IPv4/IPv6 text shape with explicit canonical text | Keep local/remote roles; no data-flow source/destination inference |
| Device/account identifiers | Bounded nonblank text shape; spelling unchanged | Not authenticated principal/device identity |
| ReportId | Bounded reported integer shape | Not a unique event identity |
| ActionType | Literal bounded string retained, status unverified | No operation, handshake, transfer, permission or threat inference |
| ResultType, Severity, Protocol, URLs, command text, unknown fields | Original supplied values, unverified and uninterpreted | No universal result/success, risk level, execution or authority |

`valid_shape` means only that a value matches this application's documented
representation. It never verifies truth. CSV cells remain exact strings;
JSON-looking cells are not re-decoded as authority metadata. Explicit normalized
numeric values do not replace their original CSV strings or JSON types.

Coverage separates total rows, one selected row, other rows omitted from the
single-row typed view, rows in other tables unsupported by this view, duplicate
network-row representations, invalid/absent selected shapes and unknown fields.
Every original row remains retained. These counts do not prove collection
completeness or that absent activity did not occur. Duplicate detection uses
type-sensitive canonical representation, keeping `True` distinct from `1`.

Source-body approved/permission/source-ID/currentness-like keys are retained and
listed as untrusted authority paths. Natural-language instructions and source
claims remain inert data. This key flag is not a general semantic injection
detector; no source text is elevated to instructions or review metadata.

## Report and response integrity

Every report fixes execution to `not_executed`, comparator invocations to zero,
association to `not_assessed`, relationship to `unassessable`, and reason to
`native_semantics_unverified`. Approval is false and no action is executed. The
unsupported predicates explicitly include connection/transfer completion,
permission/policy, causal association, HTTPS inference, compromise/intent,
technique mapping and control effectiveness.

`build_report(request)` creates this deterministic snapshot.
`export_json(request, report)` and `export_markdown(request, report)` reconstruct
it from the exact request. Type-sensitive canonical serialization is compared
before and after schema validation, rejecting altered raw/normalized values,
hashes, revisions, selection, execution/authority flags and `True == 1` mutations.
Markdown escapes supplied HTML/Markdown text and flattens source line breaks
without modifying the preserved original JSON field.

`build_response(request)` returns `NativeObservationEnvelope(report, json_export,
markdown_export)`. `validate_response(request, envelope_or_dict)` reconstructs
and checks all three together, protecting client display and downloads against
stale inputs or altered exports. The complete encoded response has a conservative
**4,000,000-byte** cap. No model, filesystem access, network request, qualification
grant or security action occurs in these functions.

The synthetic example is
`sample_data/native_evidence/network_observation.json`. It intentionally contains
two rows with a reused PID and different creation instants, one familiar literal
action label and one unknown future label. None is promoted to completed access
or authorization. User visual QA and independent human semantic review remain
PENDING; RELEASE NO-GO.
