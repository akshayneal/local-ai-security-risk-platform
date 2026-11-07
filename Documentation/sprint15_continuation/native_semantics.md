# Native semantic qualification decision

Checked **2026-11-07**, read-only, against official public Microsoft guidance.
Decision: **MORE_EVIDENCE_REQUIRED** for completion, application access,
network-protection disposition, causal association and authorization. The useful
output remains source-bound reported fields and explicit evidence questions.
No native detector or authorization comparison is qualified by this decision.

## Source identity and scope

| Reference | Displayed last update | What was inspected |
| --- | --- | --- |
| [DeviceNetworkEvents](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicenetworkevents-table) | 2026-06-22 | Public field descriptions and portal-schema caveat |
| [Network protection](https://learn.microsoft.com/en-us/defender-endpoint/network-protection#network-protection-and-the-tcp-three-way-handshake) | 2026-08-12 | TCP-layer counterexample and disposition records |
| [Schema overview](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-schema-tables) | 2026-10-28 | Table scope and built-in action-type reference |

These are mutable public pages, not an immutable sensor/version contract. Their
public text was accessible; no tenant, login or authenticated portal schema was
accessed. A displayed update date does not establish applicability to an upload.
The overview locates detailed action-type definitions in the built-in reference;
it does not supply a universal outcome ontology.

## Field-to-meaning matrix

The first reference supports the field descriptions below; all source values
remain supplied and unverified. Representation checks do not authenticate them.

| Vendor/table/field; exact value | Reported layer / positive statement | Disallowed inference or counterexample | Required corroboration |
| --- | --- | --- | --- |
| Microsoft / DeviceNetworkEvents / Timestamp; exact supplied instant | Event record / recording time | Transaction completion time | Collection context and relevant application record |
| Same / LocalIP, LocalPort, RemoteIP, RemotePort; exact same-row values | Endpoint labels / reported tuple | Higher-level data flow, final destination or HTTPS | Endpoint, proxy and application context |
| Same / Protocol; exact supplied text | Telemetry label / reported protocol | Port-derived protocol or completed exchange | Protocol-specific evidence |
| Same / InitiatingProcessId, InitiatingProcessCreationTime; exact values | Process attributes / separately reported identity fields | Causal identity from PID or name alone | Controlled device/process/time association |
| Same / ReportId; exact supplied counter | Record attribute / repeating counter | Globally unique authenticated event | Device/time context; authenticity remains separate |
| Same / ActionType; any exact label | Activity classification / supplied label | Universal success/failure meaning | Applicable portal definition and collection context |
| Same / ResultType; any exact value | Undefined here / retained value | Success or authorization | Applicable definition; absent from the public field list |
| Same / approval-like body fields; exact values | Untrusted content / source assertion | Reviewed authority or policy grant | Separately controlled current reviewed source |

## Two hypotheses and the bounded decision

**1. ConnectionSuccess establishes completed access. Rejected.** Microsoft places
DeviceNetworkEvents at the TCP layer and describes this label being recorded
before handshake completion, followed by network protection blocking the site.
Therefore the literal label cannot establish handshake completion, application
access, transferred data or a protection allow decision. This explicit
counterexample defeats the stronger predicate; string matching cannot fix it.

**2. A protection disposition record could establish a narrower reported block.
Not implemented here.** The same guidance names DeviceEvents action labels
`ExploitGuardNetworkProtectionBlocked` and `ExploitGuardNetworkProtectionAudited`.
The existing seven-table adapter excludes DeviceEvents. This workflow neither
retrieves nor associates such a record. Supplied AlertInfo/AlertEvidence rows
alone do not prove a disposition for the selected network row. Seek the relevant
record and collection context; any future association must handle device,
process, time, ambiguity and PID reuse before asserting a relationship.

No separately controlled current authority/association contract exists in this
upload path. Native semantics remain unverified, comparison remains
`not_executed`, and zero policy grants or security actions occur. An exact
reported tuple is useful observational evidence, already representable without
inventing a completion predicate. Independent human semantic review remains
PENDING (0 verified); RELEASE NO-GO.
