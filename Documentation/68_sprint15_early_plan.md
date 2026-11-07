# Early Sprint 15 prospective native observation workflow

2026-11-07. Start from finalized14B `a9af4bdc63478c63f10ee4a194d8fe07bec0886f`,
never main or older14. Branch: `feature/native-evidence-workflow-sprint15`.
14B source/tests are complete:2924fulltests,322-fileRuff,pip/diff/preservation pass;
new mini-diagnostic ran once10/10 authored cases, zero models. Original14 remains
11/12. Both frozen diagnostics must never be rerun or rescored. 14B normalpush
matches origin; exact-SHA CI is being checked without idly blocking this milestone.

## Product question and bounded success

Can a user submit supported synthetic Microsoft-format telemetry to an actual
default-off development API/UI, see useful typed observations and missing evidence,
and download faithful source-bound reports without manufacturing approved policy
or native completion semantics? Deliver this working path, not another benchmark.

One table family: selected DeviceNetworkEvents row within the existing seven-table
bounded projected JSON/CSV bundle. Reuse existing parser/normalizer. Preserve full
upload UTF8/BOM/CRLF, all original rows/fields/types, selected row index, canonical
bundle and original pointers; report selected/omitted/unsupported scope explicitly.

Public Microsoft evidence supports the table's network-observation purpose and
literal reported values. It does not establish that ConnectionSuccess means a
completed handshake, transfer, permission or successful security outcome. Preserve
ActionType/ResultType as reported labels; mark native_semantics_unverified. Keep
LocalIP/RemoteIP separate, never infer flow direction, HTTPS from443, causal joins,
ATT&CK, maliciousness, control effectiveness or institutional authorization.

## Typed native observation contract

Add a versioned native-observation report with application-derived upload ID,
original-byte hash/revision, request-bound identity, source format/profile and case
label. Currentness is submitted_snapshot_only, external currentness unchecked.
Source status is supplied_unverified, role observation_only, not a reviewed policy.
No SourceReview,approved,current,source_id or permission metadata is accepted in an
ordinary request. Never manufacture public_synthetic approved reviews from uploads.

Selected fields retain originals and original types with explicit known/absent/
invalid/unverified status. Validate aware timestamps, bounded PID/port representation
and IP shapes without relabeling endpoint roles or proving source truth. Retain
unknown fields and labels. Optional normalization must be explicit and reversible
through retained originals. No cross-row process association or synthetic comparator
dispatch: execution not_executed, association not_assessed, relationship unassessable.

Reuse v1 observation/coverage types where useful; keep frozen v1/v2 code and existing
review machinery unchanged. This unreviewed observation path is deliberately below
the eligibility boundary for an authorization comparator. It cannot attest policy.

## Actual gated integration

Add an explicit experimental ASGI composition entrypoint mounting the unchanged
`app.ai_security_api` gateway. A process-owned flag, default off, enables the new
native observation route; no request can enable it. Avoid edits to frozen main,
AI gateway, navigation definitions, model/analyzer/transport or launcher scripts.
Use a narrowly authorized conditional page addition in dashboard/streamlit_app.py,
plus new page/client modules. Do not mutate PAGE_GROUPS globally.

The experimental entrypoint can be run manually with the existing venv. Current
launcher/default APIs and released demo remain unchanged; do not retarget shortcuts
or start services during automation. Docs must explain which experimental backend
entrypoint and flag are needed. A page should guide users safely when the older
gateway lacks the route. No claim that existing launcher automatically enables it.

API requests contain bounded original source text,JSON/CSV format,selected row and
CSV case context only. Enforce outer wire and inner UTF8/canonical parser bounds,
strict scalar types, duplicate-key handling, safe fixed errors and bounded response.
Return deterministic report plus canonical JSON/escapedMarkdown; reconstruct against
exact request/snapshot before export or rendering. No raw telemetry in audit logs.

UI offers one synthetic sample, paste/uploadJSON/CSV, selectedrow, explicit Build
observations button and downloadableJSON/Markdown. Show unverified source/version/
scope, actual nonexecution, unsupported claims and missing/invalid fields in plain
language. Clear stale results when input changes, and never automatically submit on
refresh/rerun. Display source text as data, with no arbitrary model prose or HTML.

## Discriminating checks and evidence

Use existing pytest/FastAPI TestClient and Streamlit AppTest or mocked UI helpers;
no GUI/browser automation. Cover defaultoff404/pageabsence, actualclient-to-TestClient
submission/download, compatible oldroutes, request bounds/duplicates/encoding/types,
forged reviewfields, source/hash/export mutation, malformed/absent times, duplicate
rows, PID reuse, swappedlocal/remote, unknownlabel/ResultType, misleadingSeverity,
permission text, CSV preservation, multiple rows and selectedrow scope. No model or
embedding method may be called. Tests are authored software evidence, not independent
analyst/semantic validation. Do not add a new frozen diagnostic for this small slice.

Commit native contract/source/tests first; then commit integration/UI/tests. Focused
checks precede full final pytest,Ruff on trackedPython,pipcheck,diff/preservation.
Persist reproducible synthetic examples through the actual route, readable69readout,
checkpoint, source/data manifest and exact pushed-SHA CI. User visual QA stays pending.

## Preservation and remaining scope

New guard freezes final14B source/data and990raw files. Allow exactly the existing
Streamlit entrypoint product edit and the immediate14Bscope-test replay migration,
with baselinehashes, positivecompatibility and negative mutation proof. Do not alter
prior plans/keys/scorers/results/journals or v1/v2 modules. No cleanup or private
s4check inspection; all405 visible and185 ignored files are preserved.

No new dependencies/models/settings/services, no live Microsoft tenant/API, no real
incident data, no autonomous actions, no hosting or release. Model/embedding sends
remain ZERO. Human review0verified; USER VISUAL QA PENDING; RELEASE NO-GO.

Runtime lifecycle is supporting scope only. Existing300s model/frontend inactivity
timeouts, retries and unknown post-dispatch completion remain documented. Do not
extend or globally change them while building the deterministic no-model workflow.
A correct request-ID/deadline/nonretry design needs its own bounded transport study;
prefer product acceptance/polish here rather than a speculative scheduler.
