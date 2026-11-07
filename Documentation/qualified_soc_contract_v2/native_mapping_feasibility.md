# Native ConnectionSuccess feasibility

Decision: **MORE_EVIDENCE_REQUIRED**. Read-only research checked 2026-11-06;
no native mapping was activated. This is a prospective study proposal, not a
qualified detector or authorization/completion contract.

## What the public references establish

The public [DeviceNetworkEvents table reference](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicenetworkevents-table)
describes connection-related telemetry and an activity-type field. Detailed
supported `ActionType` values are delegated to the Defender portal schema.
`Timestamp` describes record time. `ReportId` repeats; Microsoft specifies using
it with `DeviceName` and `Timestamp` for event identification. Initiating process
ID, creation time and account fields describe distinct reported attributes.
The [schema overview](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-schema-tables)
establishes the table's general scope, not individual action semantics.

Microsoft's [guided hunting example](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-query-builder#hunt-for-successful-connections-to-specific-ip)
uses `ConnectionSuccess` to search connection events. Its operational label does
not establish an application transaction or policy approval. More decisively,
the [network protection explanation](https://learn.microsoft.com/en-us/defender-endpoint/network-protection#network-protection-and-the-tcp-three-way-handshake)
describes a `ConnectionSuccess` event logged before a TCP handshake completes,
followed by network protection blocking the site. Therefore even a universal
claim that this label proves handshake completion is unsupported here.

The [forward-proxy investigation reference](https://learn.microsoft.com/en-us/defender-endpoint/investigate-behind-proxy)
also describes connection observations from different stack layers: an IP may
identify a proxy while additional telemetry exposes the target domain. A label
or endpoint alone cannot settle the observed layer or final destination.

Relevant public text was readable despite generic authorization banners. No
login, tenant, authenticated portal schema, real telemetry, GUI or model was
accessed. These pages are public guidance, not a version-pinned formal event
contract; no claim of authenticated portal documentation is made.

## Narrow future predicate and prerequisites

Candidate predicate: **the selected eligible source row reports an exact
`ActionType` string of `ConnectionSuccess`**. Preserve the original value and
`DeviceNetworkEvents[row].ActionType` pointer. This is a supplied vendor assertion,
already representable as an observation, not proof of a completed connection,
application operation, transferred bytes, authorized access or source truth.

Semantic enrichment beyond that literal observation needs a separately reviewed,
version-pinned action definition covering operating system/sensor version,
protocol, collection layer, proxy behavior and timing. Keep unknowns explicit.
Application-side source identity, current revision, hash, workflow/question and
review eligibility must be rechecked. Hashes do not authenticate a source.
Any cross-record process association needs explicit device/process identity and
creation time, not a PID or name alone; any permission question additionally
needs a separate applicable reviewed requirement/authorization source. Do not
substitute an event's own authorization claim.

## Counterexamples and next decision

- `ConnectionSuccess` followed by a network-protection block must not become
  completed access or a failed security control.
- Proxy IP and separately reported target domain must not become an invented
  direct connection or silently combined endpoint.
- Port 443 without explicit protocol/application evidence must not become HTTPS,
  a completed request, or transferred data.
- Reused PID, different process creation time, principal, device, event instant
  or action must not inherit another record's association or permission.
- Repeated `ReportId`, duplicate rows, absent fields and conflicting observations
  must preserve ambiguity rather than select the first apparent match.
- Missing or unknown labels must not become failure, safety, or permission; a
  self-described approval in raw content remains untrusted content.

The next full sprint should first obtain reviewable semantic evidence and freeze
these controls before testing an explicitly narrow native predicate. Until then,
native inputs remain source-bound observations with comparison not executed and
relationship unassessable. Sprint 14B introduces no native authority, completion,
permission, ATT&CK or security-risk mapping, and executes no security action.
