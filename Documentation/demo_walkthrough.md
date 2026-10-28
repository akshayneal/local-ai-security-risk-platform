# Five-minute local demo walkthrough

Start Ollama with `qwen3:8b` available, then FastAPI and Streamlit using the
[product setup commands](20_analyst_product_experience.md#run-and-explore).
Evaluation Lab and About can be explored without either backend service.

1. **SOC sample.** Open SOC Investigation, select `SYNTHETIC-SOC-001` and press
   Load sample. Point out that this is fictional telemetry using documentation
   addresses. Submit once and allow for local inference latency. Read the summary,
   then contrast supplied observations with model inferences. Open Investigation
   and Response recommendations; no actions are executed.
2. **Trust & Integrity.** Show the panel alongside the analysis. Explain schema,
   source, bounded identity/endpoint and nonempty-observation checks. Repair may
   be Not required or Successful repair; do not promise a repair on this sample.
   Open What these checks mean. A passed contract does not prove every claim.
   If the application withholds a result, explain the fixed fail-closed message;
   do not resubmit repeatedly to chase preferred wording. Download a JSON analysis
   or Markdown brief. Source expanders show retrieved context, not verified truth.
3. **Governance sample.** Switch to Governance Review, load the synthetic policy
   draft assistant, and submit once. Show risk/decision, controls, missing evidence
   and oversight. Its panel claims schema/source checks only; semantics and final
   approval require a reviewer. Download the governance brief.
4. **Evaluation Lab.** Explain the prominent cross-version caveat. Open V3.2
   same-suite comparison: 32/42 to 37/41 valid passes, with one unavailable result
   in 42 attempts. Show the error/pass/pass case 006 and latency/repair costs.
   Official scores retain suspected scorer mismatches. No evaluation runs here.
   Optionally show Activity's two workflow/outcome filters and hidden error details.
5. **Architecture and limits.** Open About. Follow local retrieval/quarantine/model
   processing into the different SOC/governance paths. Finish with the trust
   principle: model proposal, bounded application checks, human decision. Mention
   finite identity grammar, residual ambiguity, three unseeded trials, no live
   threat verification and no statistical safety guarantee.

If FastAPI is unavailable, use Check backend status to show the safe message,
then continue with Evaluation Lab and About. Never present deterministic fixtures
or frozen historical trials as a newly generated analysis. Final screenshots,
recorded demo and release packaging are reserved for release polish.
