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

## Six completed context probes

Exact [context report](microsoft_reliability/context.json), clean launch `08edf92`,
same local model identifier/temperature, one trial per cell. All records match the
journal and the predeclared schedule. Byte measures describe different stages:

| Rows | Canonical evidence bytes | Initial user-prompt bytes | Reference bytes |
| ---: | ---: | ---: | ---: |
| 1 | 193 | 8,023 | 2,111 |
| 12 | 9,285 | 17,473 | 2,111 |
| 45 | 36,444 | 45,622 | 2,111 |

System instructions add 3,505 serialized UTF-8 bytes; the schema request adds 2,515.
Schema bytes are not claimed to be prompt tokens: format/grammar handling is a
separate provider operation. Every original row remained in canonical evidence and
the submitted prompt; no application selection occurred.

| Context | Rows | Actual initial prompt tokens | Outcome | Analyzer seconds |
| ---: | ---: | ---: | --- | ---: |
| 4096 | 1 | 2226 | Withheld after repair, endpoint check | 221.741 |
| 4096 | 12 | 3934 | Returned | 88.752 |
| 4096 | 45 | 2050 | Returned | 119.170 |
| 8192 | 1 | 2226 | Withheld after repair, endpoint check | 275.044 |
| 8192 | 12 | 3934 | Returned | 86.627 |
| 8192 | 45 | 4098 | Returned | 143.145 |

The 12-row 8192 response retains its correct alert ID and row count; 4096 invents an
ID and counts. Both retain the deletion command, and 8192 still adds unsupported
Credential Access. Both 45-row responses invent alert IDs and unsupported botnet/
compromise claims; neither a returned schema nor a larger context establishes
complete evidence representation. All four returns pass the narrow frozen checks.
No replacement semantic score is assigned to this tiny mechanics comparison.

Reported total residency rises 5,986,561,554 -> 6,599,978,515 bytes; VRAM residency
is 4,206,582,824 -> 4,190,623,498 bytes. These are snapshots, not peak memory or
isolated allocations. Latency varies with generated length, repair, loading and
unseeded sampling; the single cells do not isolate a causal speed penalty.

## Native capacity contract observations

The five separately predeclared [API probes](microsoft_reliability/context_contract.json)
completed at clean `a4fd3e2`, without response-content persistence or reruns. Short
controls return HTTP 200 at both contexts with their requested 32-token cap. Both
45-row requests with truncation/shift disabled return HTTP 400 in about 5.3 seconds.
Their exact error did not match the fixed diagnostic allowlist and remains
`other_server_error`; do not retrospectively relabel it as a captured capacity code.
The same large inputs returned under the default behavior in the six-cell experiment.
This is evidence of rejection under the protected mode, with a classification limit.

The 12-row pressure request at 4096 returns `done_reason=length`, 3934 prompt tokens
and 162 generated tokens despite a requested 1024 generation cap: exactly 4096
total. Together with the tagged server contract, this directly supports bounded
generation without context shifting. It does not certify semantic completeness.

The selected treatment will use native no-truncation/no-shift requests for Microsoft
analyses at measured context 8192, reject length-limited/incomplete results, and
withhold server-rejected requests with a safe message. This avoids treating byte
estimates as exact token counts. The 12-row input fits this capacity with output
room; the 45-row input is intentionally withheld. Generic SOC/governance and the
released demo retain their ordinary generation configuration. Unsupported runtimes
must fail closed rather than silently falling back to truncating behavior.

## Implemented complete-context boundary

`microsoft_model_context` applies only after the canonical Microsoft profile has
been validated. Each initial/repair model request uses `num_ctx=8192`,
`truncate=false`, `shift=false`, the same temperature and the same response schema.
The bridge uses the existing requests dependency against a plain loopback HTTP host,
with environment proxies and redirects disabled. It requires a server version at
least 0.40.12, whose native contract was inspected and tested. Unsupported/credentialed
or remote hosts fail before inference. Generic SOC and governance still use the
ordinary SDK options; the isolated released demo and its launcher are unchanged.

HTTP 400/413 is a rejected complete-context request, without echoing or inferring
its raw error body. A length-limited or unfinished generation is also withheld,
even if its partial JSON could parse. These failures are not retried into an
alternative truncating mode and do not trigger another policy generation. Ordinary
transport/JSON retries remain bounded at two; SOC policy repair remains exactly
one and still receives the full final validation. Both API variants return a safe
422 `complete_context_unavailable` message and the dashboard maps only the fixed
code to fixed text. Other generic error behavior is unchanged. No diagnostics are
added to ordinary analysis, exports or Activity records.

There is no estimated-token admission formula or pre-inference exact count claim.
The provider checks its rendered prompt and actual generation capacity. System,
reference, repair and format overhead travel with the actual request, so they
cannot be omitted from a client-side byte heuristic. Byte measures remain byte
measures; usage counts are retained only in explicit local metric scopes.

No rows are selected or silently discarded by this treatment. Canonical raw_log
remains exact in the original request and exports. The inventory names its projected
fields and includes a table/row entry for every source row, retaining original
values without asserting success or maliciousness. Existing prompt-only instruction
quarantine still removes matching hostile spans; that separate security behavior
does not become a context-budget selection. Returned output can still omit facts
or make semantic errors; preventing context eviction is not proof of comprehension.

The 8192 choice is an intentional Microsoft-only treatment variable, with roughly
0.61 GB additional reported residency in these observations. It gives the measured
12-row case room for output and avoids an unmeasured large context increase. The
45-row case is expected to be withheld, which counts against availability. Input
capacity remains content-dependent, not a promised fixed number of rows or bytes.
Generic/AI-risk large-input context behavior is outside this bounded treatment.
