# Microsoft app-level stress baseline

This family is independent of frozen V1/V2/V3/V3.1/V3.2 semantic evaluations.
It combines the eight synthetic SOC bundles in `sample_data/microsoft` with six
AI-system cases in `evals/microsoft_stress/ai_risk_cases.json`. These are scenarios
for learning and engineering review; Azure OpenAI/Graph/Logic Apps in case text do
not cause external calls or grant the application action authority.

SOC categories: authentication uncertainty, telemetry injection, protocol uncertainty,
vendor conflict, legitimate maintenance, multistage evidence, identity ambiguity,
and a strong suspicious positive control. AI risk categories: SharePoint resume
screening, read-only SOC copilot, identity action agent, third-party extension data
egress, read-only FAQ positive control and contradictory oversight/automatic action.

No-model preflight validates requests, reproduces canonical vendor evidence exactly,
and verifies the known instruction canary is quarantined in the prompt-only copy.
The live command runs **one unseeded trial per selected case**, through the existing
SOC or governance analyzer and configured retrieval. It records exact cases, suite
hash, application SHA/dirty state, model/host/temperature/seed, backend, latency,
result/error and repair flags. It does not call routes or write normal audit logs.
Transport retries and one SOC policy repair remain part of existing application
behavior; one trial is not necessarily one inference generation.

Deterministic checks cover source allowlisting, IDs outside ordinary prose, injection
canary absence, recognized critical token membership and nonempty SOC observations.
They do not prove semantic support, protocol correctness, severity independence,
conditional containment or meaningful false-positive/evidence-gap reasoning. Each
case carries manual review criteria for these properties; no giant regex scorer or
replacement historical reliability percentage was created.

```powershell
.\.venv\Scripts\python.exe -m evals.microsoft_stress.runner --output evals/results/microsoft_preflight.json
.\.venv\Scripts\python.exe -m evals.microsoft_stress.runner --live --case MSFT-003-port-443-unknown --case MSAI-005-faq --output evals/results/microsoft_live.json
```

Live is explicit and optional. At most the 14 defined cases can be selected once per
invocation; duplicate/unknown selections are rejected. Use a fresh output filename
and do not overwrite an official baseline. A single trial informs manual triage,
not a reliability claim or authorization for further production hardening.
