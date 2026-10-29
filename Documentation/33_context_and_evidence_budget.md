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
