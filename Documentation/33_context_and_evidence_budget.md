# Context and evidence accountability

Installed Ollama Python SDK: 0.6.2. Local server observed: 0.40.12. Its ChatResponse
exposes prompt_eval_count, eval_count and load/prompt/generation/total durations.
The server's `/api/ps` reports active context_length and model/VRAM residency.
These snapshots do not prove per-request allocation or uninterrupted residency.
[Official API documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
describes usage counts/durations and options.num_ctx; installed behavior is checked
locally rather than assuming every documented field is always present.

`local_model_metrics()` is an explicit development/evaluation context. Production
does not enable it. Counts are allowlisted nonnegative integers or null, with
system/user/schema byte sizes, elapsed time, generation-limit status and attempt
status. No prompt, response, arbitrary metadata or exception message is retained.
There is no ordinary UI/audit exposure. Model return values are unchanged. JSON
failure messages now omit the previous raw rejected-content preview.

Context overrides are deliberately bounded to 4096 or 8192 in this experiment;
unsupported settings fail before inference. With no scope/override, the previous
temperature-only options remain exact. The stable demo configuration is unchanged.
Actual `prompt_eval_count` is not byte count, estimated token count, evidence
completeness or proof all input survived truncation. Missing metrics remain null.
Retries and SOC policy-repair generations are reported separately by the runner.

The frozen fresh-experiment plan declares six context probes: one network row,
12 process rows and 45 process rows, one trial each at 4096 and 8192. Full canonical
evidence, initial prompt size, reference overhead, system/schema overhead, processed
tokens, generation tokens, residency and latency are separately retained. No
pre-inference exact tokenizer is available. Measurements and selected production
policy follow after the complete untreated baseline and controlled probes.

## Provider behavior investigation

The installed SDK's `Client.chat` signature and ChatRequest fields do not expose
`truncate` or `shift`. The matching server release does: see tagged
[request types](https://github.com/ollama/ollama/blob/v0.40.12/api/types.go),
[chat routing](https://github.com/ollama/ollama/blob/v0.40.12/server/routes.go), and
[llama-server adapter](https://github.com/ollama/ollama/blob/v0.40.12/llm/llama_server.go).
Its default oversized-prompt path preserves a prefix and suffix while discarding
intervening tokens to approximately half the context. Generation can also shift
context. This explains a plausible mechanism for the observed 2050-token count at
context 4096; the count alone does not identify which rows or instructions survived.

A separate five-call API contract plan is committed under `evals/context_contract/`
before results. It tests `truncate=false`, `shift=false` at both measured contexts,
including input overflow and generation-capacity pressure. Only fixed statuses,
allowlisted numeric usage and residency are saved. No raw generated text is saved.
These mechanics probes do not replace the original six quality/context cells.
The outcome will determine whether native fail-closed capacity controls are a
better supported treatment than an approximate byte/token budget. No production
transport or setting is changed merely because source inspection suggests support.
