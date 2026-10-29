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
