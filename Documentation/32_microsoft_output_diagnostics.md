# Microsoft output diagnostics

Sprint starts at clean `949d4cbdc3320a2bd409702d6e26fc6e98cff1fb` on the
Sprint 2 branch. Work proceeds only on `feature/microsoft-evidence-reliability`.

`LocalDiagnosticTrace` is explicitly passed by local experiment code. It never
copies analyzer payloads. It hashes the caller identity and records generation
index, fixed validation codes and allowlisted field names, schema/source processing,
observable/endpoint/observation status, repair flags, elapsed time and final outcome.
Source status describes processing, not semantic relevance. Events are bounded at
16 and violations at 40 per event. Unknown violations become `UNCLASSIFIED`.
Raw responses, telemetry, prompts, exception messages and arbitrary stage values
are discarded. No persistence, environment enablement, API, audit or UI hook exists.
`AnalysisTrace` and `ProductTrace` retain their previous behavior.

The original MSFT-003 failed trial cannot be retrospectively diagnosed: rejected
generations were not retained. Its JSON RemoteIP/RemotePort and LocalIP/LocalPort
are absent from the legacy textual endpoint grammar. This is a deterministic
compatibility hypothesis, separate from the historical trial's unknown cause.

Predeclared reproduction: one trial of the exact synthetic MSFT-003 request with
unchanged generation/retrieval settings. No favorable-output reruns. Run after this
diagnostic implementation is committed:

```powershell
.\.venv\Scripts\python.exe -m evals.microsoft_reliability.diagnose --live
```

Only machine diagnostics are written to ignored
`evals/results/microsoft_port_diagnosis.json`. No rejected output is persisted.
Reproduction results and compatibility probes will be recorded separately.

## Controlled reproduction result

At clean diagnostic implementation `f8159d21d15699040dfd38ae2b197ae1c96e9a44`,
one unseeded trial, qwen3:8b identifier `500a1f067a9f`, Ollama 0.40.12, temperature
0.1, legacy retrieval, server-default context: withheld after 245.185 seconds.
Initial validation: `IP_SHAPE`, `observed_evidence`; schema passed. Repair:
`ENDPOINT_PAIR`, `summary`; schema and observable membership passed. Exactly one
repair; no final response. Only safe codes were retained in the ignored report.

Classification: **reproduced availability failure with known rejection stages**.
Initial malformed-identifier detection and repair endpoint rejection are established.
The final pair's actual values are deliberately unavailable, so valid-pair false
rejection versus invented relationship is inconclusive for this live trial. The
historical trial remains undiagnosable. Never label either as proven validator
false rejection from this trace alone. Deterministic structured-field probes are
the appropriate independent way to demonstrate compatibility defects.

## Deterministic compatibility probes

`tests/test_microsoft_endpoint_probes.py` isolates the unchanged legacy recognizer.
Four valid repetitions (remote IP:port, local IP:port, destination field labels,
and to-IP-on-port prose) falsely reject against supplied Microsoft JSON. Cross-row,
local-port-on-remote-IP and unrelated-IP pairs correctly reject. A JSON field/value
mutation is unrecognized and passes that narrow check, demonstrating a blind spot.
Generic text endpoint and role checks retain their previous behavior. Missing
Protocol stays absent, explicit Tcp stays exact, and protocol interpretation remains
outside this deterministic legacy recognizer. These prove format incompatibility
independently, without claiming the discarded live pair was valid.

## Structured compatibility treatment

`app/microsoft_evidence.py` recognizes only the existing Microsoft input profile,
re-parses its bounded canonical bundle, and verifies case identity. Additional
endpoint authorization comes from valid IPv4/port fields on individual
DeviceNetworkEvents rows. Local/remote roles, exact original values, optional fields
and row indices remain available; string ports such as `00443` retain their original
spelling in source/inventory while numeric relationship comparison accepts 443.
Malformed/boolean/out-of-range ports authorize no new pair. No protocol, reputation,
causality or maliciousness is inferred. Local/remote does not imply direction.

The legacy textual recognizer is unchanged. Its input authority is supplemented by
the validated row pairs, while bounded local/remote labels and JSON endpoint objects
are separately checked. A JSON projection must match one original event, so individually
valid endpoints cannot be combined from unrelated rows. Duplicate JSON endpoint keys,
role reversals, cross-row ports and invented pairs are rejected. Unrecognized prose
remains a documented grammar limitation; this is not universal relationship entailment.
Legacy explicit source/destination checks and critical-token fidelity remain active.

The same full validator runs after repair, and the repair prompt now includes the
structured pairs rather than an empty legacy extraction. Deterministic controls prove
a previously rejected valid pair now returns first-pass and that fixing observations
while introducing a bad pair in another field still fails closed after exactly one
repair. Generic SOC behavior retains its original path.

## Unchanged treatment observations

All five network-only attempts (SOC-006 three times, SOC-007, SOC-008) returned
with supplied endpoint relationships after treatment, including the three attempts
withheld in baseline. SOC-006/2 needed one repair after `IP_SHAPE` in observations;
the repaired response passed the full validator. No rejected raw value is available
to classify that initial defect more specifically. Four network responses returned
first-pass. These observations support availability for this bounded sample, not a
universal endpoint-accuracy rate. Unsupported MITRE classifications still occur in
some network responses despite correct endpoint fields. Unknown application
protocol remains unknown; hypothetical HTTPS examples are not counted as observed
protocol claims. Full semantic review lives in the separate treatment ledger.
