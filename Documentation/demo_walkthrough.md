# Release-candidate demo walkthrough

Start FastAPI, Streamlit and local Ollama using the [README setup](../README.md#run-locally).
Overview, Platform Evaluation and About are available without the backend/model.

1. **Overview.** Describe the platform as local analyst support for security-event
   investigation and AI-system risk review. Show the technical / policy-governance
   matrix: SOC Investigation and AI System Risk Review are Active. SOC Policy &
   Governance Review and AI Security Assessment are Planned and have no analysis
   controls. Point out the separate Workflows and Platform navigation groups.
2. **SOC Investigation.** Load `SYNTHETIC-SOC-001`, explain the fictional telemetry
   and submit once. Allow for local-model latency. Read the provisional incident
   type and summary, then distinguish Observed Evidence from Analyst Inferences.
   Open Investigation, Response and Context. Show Response checks: actual schema,
   source, identifier, endpoint and observation processing, plus repair status.
   Repair may be Not required or Successful repair; do not promise a repair on
   this sample. If analysis is withheld, explain that the required checks still
   failed after one repair; do not repeatedly resubmit to obtain preferred wording.
   Open a source and download a JSON or Markdown brief. Recommendations execute no
   actions.
3. **AI System Risk Review.** Load the synthetic policy draft assistant and submit
   once. Make clear that the reviewed object is an AI system/use case. Show review
   decision, controls, missing evidence, oversight and logging. Its Validation
   panel reports schema/source processing without claiming SOC identifier checks.
   Download the AI System Risk Review brief.
4. **Platform Evaluation.** Describe this as assurance history for the platform,
   not an arbitrary-model evaluation service. Show the version-comparison caveat,
   then V3.2's unchanged-suite comparison: baseline 32/42, treatment 37/41 valid and
   37/42 attempts, with one withheld response. Select case 006's error/pass/pass
   outcome. Point out repair/latency costs and unchanged official scores despite
   suspected scorer mismatches. No model call runs when this page opens.
5. **About.** Follow the native architecture stages into the distinct SOC and
   AI-system-risk response paths. Review the compact operational boundaries;
   expand Validation limits only if needed. Optionally show Activity's workflow
   and outcome filters as a platform audit view, not a case-management queue.

If FastAPI is unavailable, use Check backend status and continue with Overview,
Platform Evaluation and About. Do not present deterministic fixtures or frozen
trials as newly generated output. Before approving merge/tag, inspect dark and
light themes at desktop and narrow widths; capture screenshots only after that
inspection. This sprint did not complete pixel-level visual QA.
