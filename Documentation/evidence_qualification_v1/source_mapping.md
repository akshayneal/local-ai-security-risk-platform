# Experimental source-qualified SOC mapping

Status: internal, opt-in pure functions; no public route, UI activation or model
requirement. Synthetic values only. This slice does not detect general Microsoft
security threats, authenticate a source, establish enterprise policy, approve an
action or execute one.

`app.qualified_soc.build_qualified_report(raw, review, scope, **options)` accepts
original `bytes` and a separate application-owned `SourceReview` and
`QualificationScope`. `authorization_sources` is a bounded tuple of separate
`(original_bytes, application_review)` pairs. The function rechecks qualification
before parsing, association and comparison. `export_json` and `export_markdown`
take `(raw, review, scope, report, **same_options)` and recompute the report using
the supplied fresh reviews/current-version snapshots. An unchanged caller-owned
snapshot cannot reveal an external revocation: callers must provide current
application metadata at each use. There is no source lookup or external registry
integration in this demonstration.

## Field mapping policy

Native formats are `microsoft_json` and `microsoft_csv`, reusing the existing
`app.soc_inputs` parser/normalizer and its seven supported table names. JSON has
`case_id` and `tables`; CSV selects one table plus the case ID separately. The
selected row must be an existing zero-based `DeviceNetworkEvents` row. Other rows
are preserved and counted; they are not merged into it. No broader vendor schema
or `ActionType` interpretation is introduced. The new qualification byte cap is
64,000 original bytes, narrower than the existing adapter's 80,000-byte cap;
existing production adapter limits/defaults are unchanged.

Original UTF-8 upload text, including BOM, CRLF, spacing and CSV representation,
is retained exactly in `SourceSnapshot.raw_text`; encoding it as UTF-8 reproduces
the original bytes. The SHA-256 is over those original bytes. The separate
canonical JSON is the existing normalized representation and is not mislabeled
as original bytes. JSON finite numeric types, booleans, nulls, arrays and objects
remain original evidence. CSV cells stay strings, including leading zeroes and
JSON-looking text. Duplicate keys/headers, malformed encoding, invalid widths,
excess depth/size/rows and unsupported tables fail visibly.

Every native field becomes an observation with original value/type and
`Table[zero_based_row].Field` path, including fields outside this mapping table.
Unknown fields remain uninterpreted. There is no invented vendor schema version:
the application contract is `qualified-soc-report/1` over the repository's local
projected-table profile described in `Documentation/27_microsoft_security_inputs.md`.

| Supplied field | Retained observation / validation | Comparator predicate |
| --- | --- | --- |
| `Timestamp` | Exact original; explicit-zone timestamp checked if present; absent/invalid recorded | No completion/outcome inference |
| `ActionType` | Opaque vendor action label, unchanged | `operation` remains unknown |
| `ResultType` | Opaque vendor result label, unchanged | `result` remains unknown |
| `DeviceId`, `DeviceName` | Distinct reported identifiers, unchanged | No authenticated asset identity or substitution |
| `InitiatingProcessAccountUpn`, SID/account fields | Distinct reported account assertions, unchanged | No interchangeable-principal inference |
| `ProcessId`, `InitiatingProcessId` | Exact value; integer or decimal-string range checked if present; bool rejected as a numeric identity | No process/network causal join |
| `InitiatingProcessCreationTime` | Exact original; explicit-zone timestamp checked if present | No PID-only identity join |
| `LocalIP`, `RemoteIP` | Exact separate endpoint roles | Neither becomes data-flow source/destination |
| `LocalPort`, `RemotePort` | Exact representation; bounded integer/decimal-string checked if present | No protocol/application/authorization inference |
| `Protocol`, `RemoteUrl` | Exact reported transport/URL values | Port 443 does not establish HTTPS |
| `ReportId`, `AlertId` | Exact reported identifier | No global uniqueness, causal identity or permission |
| Command lines / additional fields / annotations | Preserved untrusted source assertions | No executable instructions or policy authority |
| No supplied amount | No amount invented | `amount` marked not supplied |

The native outcome is `status=unassessable`,
`relationship=unassessable`, reason `unsupported_native_operation_outcome`.
Even a separately qualified authorization context cannot create missing native
operation/completion semantics. Native authorization association is explicitly
`not_assessed`. No Sprint 13 comparator is dispatched. This is a complete
deterministic ingestion-to-JSON/escaped-Markdown observation path with honest
abstention, not an unsuccessful detection claim.

Coverage separates total rows, the selected row, other rows omitted from the
single-row semantic slice, rows in unsupported-for-this-slice tables, invalid
optional selected fields and missing selected identity/time prerequisites.
All original rows/fields remain in the original bundle and observations. These
counts describe projection scope, not collection completeness or genuine absence
of activity. Invalid optional native fields stay original and explicitly invalid;
they are never corrected by copying another row.

## Separate synthetic typed comparison

`synthetic_event` accepts this explicit schema; every `event` field is required
even when its value is unknown/null. Identifiers and text are bounded, numeric
fields are strict integers and booleans/strings cannot masquerade as integers.

```json
{
  "schema_version": "qualified-event/1",
  "event_id": "EXAMPLE_EVENT",
  "process_id": 123,
  "process_created_at": "2026-11-05T09:50:00Z",
  "event": {
    "operation": "inspect_status",
    "result": "attempted",
    "principal": "svc-example",
    "asset": "node.example.invalid",
    "source": "192.0.2.10",
    "destination": "203.0.113.10",
    "endpoint": "status.example.invalid",
    "time": "2026-11-05T10:05:00Z",
    "amount": null
  },
  "annotations": []
}
```

`synthetic_authorization` is separate original JSON with
`schema_version=qualified-authorization/1`, `event_id`, `process_id`,
`process_created_at`, `event_time`, `question_id` and the unchanged Sprint 13
`Authorization` object: `status`, `operation`, `principal`, `asset`, `endpoint`,
`window_start`, `window_end`. The event body cannot carry its own authorization,
source identity, currentness, review, grant or permission metadata. Those fields
are rejected rather than interpreted. Natural-language annotations remain inert
source data; the code does not claim to semantically detect every injection.

Source reviews explicitly require synthetic classification, synthetic status,
the accepted role/format, current revision/status, workflow/case/question,
application review approval and effective/review/expiry dates. Authorization
sources additionally require `requirement_reviewed=True`. Those application
metadata assertions make a record eligible for this demonstration; they are not
authenticated institutional approval. Full reviewed metadata, scope and why the
source was accepted are bound into each report snapshot. Input-body claims,
retrieved/model/report text and the hash cannot confer those roles. Real sources,
AI Security enterprise policy qualification and arbitrary prose interpretation
are unsupported.

Before comparison, all candidate sources are qualified; any ineligible or
malformed candidate makes the result unavailable rather than triggering a
less-restricted fallback. There are at most eight authorization candidates.
Association requires exact event ID, process ID, time-equivalent process creation
instant, time-equivalent event instant, question ID, principal, asset and endpoint.
Timestamp strings retain their original spelling, including equivalent offsets.
IP, name, port, nearby timestamp and repeated alert identifiers cannot associate
an authorization. Unknown identity prerequisites cannot match. The event source
identity cannot also supply its own authorization. Two conflicting current
snapshots for the same source identity are refused.

Association identifies the explicitly selected event/context pair. It does not
assert that the requested operation or allowed time window applies: those are
the comparator's target predicates. For example, the same exact event and actor
with an authorization asserting a different allowed operation/window can produce
a scoped declared mismatch. A different event/process/principal/resource/time is
unassociated and never compared. Multiple matching eligible contexts abstain as
ambiguous. They report conflicting claims only for opposed known authorization
status, different known allowed operations, or opposed declared alignment/mismatch
outcomes. Unknown versus known values and compatible differing windows are
ambiguous rather than automatically contradictory. No first-hit choice occurs.

With exactly one associated context, the adapter constructs a
`DERIVED_PROJECTION` envelope and uses unchanged `adaptive_semantics.project`
through `adaptive_reports.build_report`. The legacy SOC contract has only one
envelope source, so its premise IDs/source labels refer to that derived envelope.
The wrapper's explicit field lineage binds every `/data/event/*` value to the
original event source and every `/data/authorization/*` value to the separate
authorization source. The legacy envelope is never presented as native Microsoft
data or separate-source provenance.

`declared_alignment` and `declared_mismatch` concern only supplied typed scope.
Failed/attempted/unknown event results are carried unchanged and do not turn into
completed actions. An unknown operation or unknown permission remains
underdetermined. No eligible context means missing evidence, never safe/legitimate
activity. `projection_unavailable` means unusable input/review; `unassessable`
means retained observations whose relationship cannot be established.

## Export integrity and limits

JSON keeps original types and all accepted source snapshots. Markdown HTML-escapes
and Markdown-escapes supplied text; it does not render annotations as instructions.
Before exporting, the complete report is recomputed against fresh source bytes,
reviews and scope. Comparison uses exact JSON serialization before and after
schema validation, detecting nested mutation, `True` versus `1`, and a forged
`approval_granted=0` that a permissive literal validator could otherwise normalize
to `False`. Model prose is never accepted by this interface.

This does not freeze Python's nested dictionaries in memory, authenticate the
operator, verify real source truth, prove policy implementation, discover external
revocations, establish collection coverage, or authorize live activity. Export
rejects mutated dictionaries. Source byte/row/candidate/text bounds limit output
size; no inference or embedding request occurs. Existing analyzers, API contracts,
retrieval defaults, Inspector/corrections and historical Sprint 13 paths remain
unchanged. Independent human semantic review and user visual QA remain PENDING.
