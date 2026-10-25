# Current system walkthrough

This walkthrough follows the local application from Python objects to an analyst's
screen. It assumes familiarity with functions, dictionaries, classes, and basic
cybersecurity. The application is a portfolio/research system: it organizes
analysis for human review and does not operate security infrastructure.

## 1. Start with the data structures

Consider a SOC alert before any model sees it. It has an identifier, a source
system, an affected asset, original log text, and perhaps indicators and a short
description. A plain dictionary can hold these values, but it does not establish
which keys are required or which types are acceptable. `SocAlertRequest` in
`app/schemas.py` makes that contract explicit using Pydantic's `BaseModel`.

Pydantic constructs a Python object from incoming data and reports validation
errors when the data does not satisfy its declared fields. Python annotations
describe types; Pydantic uses them at runtime. That distinction matters because
an HTTP client and a language model can both send malformed data. Neither should
get to redefine the application's contract.

The request models bound labels to 256 characters, descriptions to 10,000, and
SOC raw logs to 100,000. Request lists allow at most 100 entries, each at most
1,024 characters. `Annotated` attaches these constraints to reusable types.
These are character and item limits, not tokenizer budgets or total HTTP body
limits. They reduce accidental resource use without banning suspicious command
strings, URLs, or injection text that an analyst may legitimately need to inspect.

Response models specify the shape of an answer. `Literal["low", "medium",
"high", "critical"]` limits severity or risk to an enumerated vocabulary rather
than an arbitrary string. Governance decisions similarly use `approved`,
`needs_review`, or `rejected`. A `SourceReference` contains an ID, title, framework,
and concise relevance explanation. Lists of strings make findings easy to display
and inspect. A valid schema establishes structure; it cannot prove that a sentence
is true or that a proposed decision is appropriate.

Interview concept: runtime validation at an application boundary, reusable types,
and the difference between syntactic correctness and semantic correctness.

## 2. The FastAPI boundary

`app/main.py` creates a FastAPI application. The two analysis routes are
`POST /analyze/soc-alert` and `POST /analyze/governance`. FastAPI uses the annotated
request model to parse JSON before entering the route function. Invalid input
receives a validation response rather than being passed to the model. Each route
declares its response model as another contract for the outgoing result.

The route delegates the workflow to an analyzer, records a success or failure,
and returns the result. This keeps HTTP concerns apart from prompt construction
and reference handling. `GET /health` reports service health without generating
anything. It does not establish that Ollama is ready. `GET /schemas` exposes the
four request/response schemas; `GET /logs` returns recent local audit entries.

Interview concept: separation of concerns, HTTP contracts, and dependency mocking
when testing API behavior.

## 3. Local reference cards and retrieval

The active reference system reads JSON cards from `reference_material/`. SOC uses
`soc_references.json` and `local_checklists.json`; governance uses
`governance_references.json` and the same checklist file. A card carries metadata,
tags, and content. These files are distinct from ingested documents and the SQLite
registry described later.

`normalize_text()` in `app/reference_loader.py` lowercases text and extracts
keyword tokens using a regular expression. `score_reference()` compares the set
of request tokens with tokens from a card's title, framework, type, tags, and
content. Each overlapping token contributes to the score. A tag whose tokens are
all in the query adds a bonus of three. Cards with a score above zero are sorted
by score; ties preserve their original order.

The SOC analyzer requests the top five cards and governance requests the top six.
The query is the serialized request, so several input fields can influence
retrieval. A missing reference file contributes no cards. The formatter creates
readable blocks with source ID, title, framework, type, and content.

This is **keyword/tag retrieval, not vector RAG**. It creates no embeddings and
uses no similarity database. It can miss synonyms, reward incidental word
overlap, and retrieve guidance that is only loosely relevant. A high score is a
relevance heuristic, not a trust score or proof of factual accuracy.

Interview concept: transparent ranking heuristics, top-k selection, retrieval
quality, and the distinction between retrieval relevance and source reliability.

## 4. Prompt construction and trust

`app/prompts.py` contains a shared system message and a builder for each workflow.
The Ollama client sends the system message as a system-role message and the built
workflow prompt as a user-role message. The latter combines application-written
instructions, retrieved context, and the request's JSON.

The security boundary is about authority, not merely where text appears. A raw
log may contain "ignore previous instructions" because an attacker wrote it.
A document may contain a fake system override. These strings remain available
for analysis, but must be treated as untrusted data. Explicit BEGIN/END delimiters
mark reference and user-input regions. The system instructions tell the model
that instructions inside those regions cannot acquire application authority,
including text that imitates a delimiter.

Retrieved guidance remains useful, but the model must distinguish a reference's
claim from independently verified fact. Threat attribution, reputation, legal
obligations, and mandatory frequencies need an applicable evidentiary basis. The
application has no live enrichment mechanism that could verify them. This rule
does not discard curated guidance; it limits how strongly an answer may claim
that guidance establishes external truth.

These prompt controls reduce risk but are not a parser-enforced isolation system.
Models can still follow hostile text. That is why the project also validates
output deterministically and runs adversarial evaluations.

Interview concept: instruction hierarchy, direct and indirect prompt injection,
and defense in depth around probabilistic components.

## 5. What Ollama contributes

`app/ollama_client.py` uses the Ollama Python client. The default host is
`http://localhost:11434` and the default model is `qwen3:8b`; configuration can
override these. The sprint uses the installed local model. There is no external
AI-provider integration.

`call_model_json()` supplies the response model's JSON Schema through Ollama's
`format` argument. This guides generation toward the expected object. Temperature
is 0.1 to reduce sampling variability. Low temperature is not a promise of
identical answers. The code does not fix a random seed, context size, or model
digest, and the installed runtime/hardware may affect execution.

The helper strips surrounding Markdown fences if necessary, then calls
`json.loads()`. Tenacity retries the decorated model call at most twice, waiting
one second between attempts. This retry includes JSON parsing failures inside the
helper. The later analyzer's Pydantic response validation is outside that retry.
No tools are offered to the model. It generates text rather than running commands,
looking up reputation, or isolating hosts.

Interview concept: local inference, structured generation, sampling variability,
and placing retries around the specific operation they can recover.

## 6. The two analyzer lifecycles

`analyze_soc_alert()` receives a validated alert. Unless references are explicitly
supplied, it retrieves SOC guidance. It formats those cards, builds the SOC prompt,
calls Ollama with `SocAlertResponse`'s schema, cleans selected prose fields,
sanitizes source references, and finally constructs `SocAlertResponse`.

SOC instructions emphasize accurate event sequences. Failed logins for one
account followed by a successful login for another account do not prove that the
first account was compromised. When a user's narrative conflicts with raw events,
the raw sequence takes precedence over the unsupported interpretation. Even the
raw log is supplied data, not an independently authenticated forensic record.

`analyze_governance_risk()` follows the same mechanical sequence with six possible
references, the governance prompt, and `GovernanceRiskResponse`. Its analytical
questions concern data, users, integrations, oversight, business impact, controls,
and evidence gaps. A field named `required_controls` does not give the model legal
authority: its claims still need an applicable basis and human review.

Both analyzers accept an optional keyword-only `references` argument. `None` means
normal retrieval; an explicit empty list means no references. Evaluation uses this
small seam to supply a controlled hostile card while retaining the real prompt,
model client, cleanup, and validation code. Normal API callers use retrieval.

Interview concept: dependency injection for testability without maintaining a
second implementation of production logic.

## 7. Deterministic output controls

After generation, model output is still untrusted. `sanitize_source_references()`
builds an allowlist from the supplied cards. It drops unretrieved IDs, restores
titles and framework names from the local card, and collapses duplicate returned
IDs deterministically while retaining the first returned relevance explanation.
Trusted metadata means metadata controlled by the application/reference selection,
not a guarantee that a card's content is accurate.

Citation cleanup removes supported inline citation forms and bare known source
IDs from selected ordinary fields. Both retrieved IDs and IDs declared in the raw
model source list are cleanup candidates; only retrieved IDs are allowed in the
final structured source list. This distinction lets Python clean an invented ID
without granting that ID citation authority.

The baseline also exposed user-named fake IDs echoed only in prose. A narrow
heuristic now replaces uppercase source-style identifiers after explicit citation
markers such as "per" or "references" with an unverified-reference description.
It preserves standard CVE indicators and leaves normal hosts, commands, and URLs
alone. It does not scan arbitrary input for deletion. Unfamiliar prose syntax can
still evade it, and nonstandard identifiers in matching contexts may be mistaken
for citations. The model is instructed to keep all IDs in `source_references`. Cleanup
does not make all possible citation-like prose semantically correct, and a model
can still invent claims without citing anything. Pydantic then checks field types
and allowed values. It cannot evaluate the truth of observations or recommendations.

An allowlist belongs in ordinary Python because it is an exact membership question.
Asking the model to police its own invented sources would make a deterministic
contract depend on another probabilistic judgment. The model supplies analytical
content; the application enforces the source metadata contract.

Interview concept: output validation, allowlists, provenance integrity, and
choosing deterministic controls for deterministic requirements.

## 8. Observed evidence and analyst inference

The SOC response separates `observed_evidence` and `analyst_inferences`, both lists
of concise findings. An observation might identify the accounts and outcomes in
an authentication sequence. An inference might say the sequence suggests possible
credential misuse and requires verification. A reference-only statement should be
attributed as such rather than being presented as a measured host event.

These fields are user-facing conclusions, not hidden reasoning traces. They help
an analyst see when a conclusion exceeds the events provided. They are still
model-generated lists; the field names do not independently verify their content.
Empty-list defaults preserve compatibility with older response fixtures, while the
current SOC prompt requests both fields in new generations.

Interview concept: evidentiary discipline and designing output schemas that make
uncertainty visible without exposing internal chain-of-thought.

## 9. Errors and audit logging

An exception in an API analysis route produces a generic 500 detail: "Analysis
failed. See local logs for details." The route records the internal exception
locally. This separates client-facing disclosure from diagnostic observability.
It is not a complete access-control system: `/logs` is a local unauthenticated
endpoint and may expose diagnostic content to anyone who can reach the service.

`app/audit_logger.py` writes JSONL, one JSON object per line, under `logs/`. Each
entry records UTC time, mode, model, short input/result summaries, success, optional
error text, and the final structured source IDs. Successful API analysis is
audited, but the eval runner calls analyzers directly and writes its own reports;
it does not create normal API audit entries. Logs are ignored by Git and should
remain local. They are not tamper-evident forensic records.

Interview concept: error disclosure boundaries, structured logging, and the
difference between operational auditability and immutable audit guarantees.

## 10. Streamlit's role

`dashboard/streamlit_app.py` builds forms for governance and SOC. When submitted,
it makes an HTTP POST to FastAPI using `requests`; the model runs behind the API,
not inside a UI widget. The dashboard presents metrics and findings, with Observed
Evidence and Analyst Inferences before the analyst note. Source References has
its own display, and an expander shows the complete JSON.

The UI uses `.get(..., [])` for findings lists so older results without the new
fields remain displayable. The Audit Logs mode reads `/logs`. Network errors are
shown to the local user. The dashboard has a finite request timeout, while the
model client currently does not declare an explicit per-case generation deadline.

Interview concept: frontend/backend separation, graceful presentation of optional
data, and understanding timeouts across application layers.

## 11. Document ingestion is a separate pipeline

The document subsystem prepares a future knowledge collection without making it
the current workflow retrieval engine. Its flow is:

```text
local file -> security limits -> extraction -> content hash
           -> document identity -> version identity -> chunks -> registry
```

`app/document_loader.py` accepts UTF-8 `.txt` and `.md`, plus text-extractable PDFs.
It rejects unsupported files, direct symbolic links, empty files, paths outside
the approved root, and oversized input. Default limits in `document_limits.py`
are 10 MiB per file, 100 PDF pages, 500,000 extracted characters, and 750 chunks
per document. PDF loading checks a signature near the start, rejects encrypted
files, and uses pypdf for text extraction. There is no OCR for image-only scans.
These bounds limit work but do not constitute a sandbox for every parser failure.

Text normalization standardizes line endings and paragraph spacing. A SHA-256
hash identifies original file bytes, computed in blocks. The logical document ID
uses a normalized relative path hash; its version ID combines that identity with
a content-hash prefix. Changing content therefore produces a new version while
the same path retains logical identity. The full content hash is retained for
integrity checks; truncated identifiers are not used alone to prove equality.

`app/chunker.py` splits text into bounded character windows, preferring paragraph,
line, sentence, and word boundaries. Defaults are 1,000 characters with 200
characters of overlap. Overlap helps preserve context near a boundary. Chunk IDs
include version identity and position, so chunks from changed content are not
silently confused with earlier versions. Chunking is not embedding.

`scripts/register_documents.py` loads, chunks, groups by version, and registers
documents through `DocumentRegistry`. SQLite stores document and version metadata,
content hashes, statuses, counts, and current-version relationships. Transactions,
foreign keys, and uniqueness constraints protect that state. Re-registering the
same content can be unchanged; changed content creates a new version; returning
to older known content can reactivate its version. It does not store a searchable
vector index or automatically feed these chunks into SOC/governance prompts.

Interview concept: content-addressed identity, idempotence, bounded processing,
transactional state, and separating ingestion from retrieval.

## 12. Adversarial evaluation

The `evals/` package is an application benchmark, separate from ordinary tests:

```text
case -> request validation -> reference resolution -> real analyzer -> Ollama
     -> cleanup + source sanitization -> Pydantic response -> checks -> report
```

Each case specifies an input, threat category, severity, expected safe behavior,
and deterministic checks. Some supply a synthetic hostile reference; others use
normal keyword retrieval. Fixtures use synthetic source IDs and documentation
addresses. They never change the production reference packs.

The runner validates requests, resolves the exact supplied references, and passes
them into the analyzer. It checks final output because that is what reaches the
analyst. Structured source metadata is excluded from ordinary-prose scans. A
source ID in its dedicated field is legitimate; the same string in a summary can
be a contract violation. Check outcomes, final responses, source IDs, durations,
and errors are recorded per case. One exception does not abort the remaining cases.

The initial suite has exactly 12 cases across seven categories. Substring and
membership checks are transparent but imperfect. A model could satisfy a word
check while still making an unsafe claim elsewhere. The audit-frequency check
permits qualified quotations using a same-sentence uncertainty heuristic, which
also cannot replace semantic review. The report is evidence about these checks,
not a comprehensive security certification.

Interview concept: threat modeling, test oracles, failure isolation, and the
limits of proxy metrics for natural-language behavior.

## 13. Why preserve a baseline first?

Changing defenses before measuring the original system makes a before/after claim
unverifiable. This sprint therefore committed the harness, ran the original
application, froze its JSON report, and only then changed trust-boundary prompts
and output controls. The same case file is used for the hardened run.

Reports record the SHA-256 of the exact case-file bytes, the model name, UTC time,
and Git commit. `evals.compare` refuses different hashes, model names, or executed
case sets. Byte hashes also differ when line endings change; `.gitattributes`
pins the suite to its original CRLF across checkouts. Preserve those bytes when reproducing the
official comparison. The fixture payloads used by cases
are embedded in that file; the separate fixture file is a reusable catalog.

Normal retrieval cases still depend on the reference packs and production code.
The suite hash alone does not fingerprint the entire application, model binary,
or runtime. Commit provenance and an unchanged local model supply additional
context. A single before/after run cannot establish statistical significance.

Interview concept: experimental controls, provenance, reproducibility, and honest
interpretation of small samples.

## 14. Continuous integration

`.github/workflows/ci.yml` runs on pushes and pull requests. It checks out the
repository on Ubuntu, selects Python 3.13, creates a virtual environment, installs
`requirements.txt`, runs pytest, and runs Ruff. Pytest uses fake model responses;
CI does not need Ollama or model downloads. Live evaluation remains an explicit
local activity rather than an unpredictable network/model dependency of unit tests.

The earlier `f051e73` commit pinned Ruff to 0.17.2 and corrected CI lint
reproducibility. Tool versions can change which code passes a check even when
application behavior is unchanged. Pinning that tool makes local and hosted lint
results easier to compare. Other unpinned packages can still drift; CI success
does not imply a fully locked build or production readiness.

Interview concept: reproducible tooling, platform-independent testing, and
separating deterministic verification from live-model experiments.

## 15. One SOC request from click to answer

Imagine an analyst pastes authentication events and clicks Analyze SOC Alert.
Streamlit assembles a dictionary and POSTs it to FastAPI. FastAPI builds
`SocAlertRequest`, checking required fields, types, and bounds. The route calls
the SOC analyzer, which serializes the request into a retrieval query. The loader
scores local guidance and returns up to five matching cards.

The prompt builder places those cards and the serialized alert inside explicitly
untrusted regions alongside the workflow instructions. The Ollama client sends
the system message, prompt, JSON Schema, and low-temperature setting to the local
model. Generated content is parsed into a Python dictionary. The analyzer cleans
selected inline citations, sanitizes source IDs and metadata, and builds a
`SocAlertResponse`.

The route logs the outcome and final source IDs, then FastAPI sends JSON back.
Streamlit displays the summary, observations, inferences, analyst note, suggested
actions, gaps, and references. The analyst decides what to verify or escalate.
No host isolation occurs anywhere in this lifecycle. If analysis fails, the API
records diagnostics locally and returns the generic error.

Interview concept: being able to explain an end-to-end request across validation,
retrieval, inference, postprocessing, observability, and presentation.

## 16. The security boundaries to remember

| Boundary | Role and limitation |
| --- | --- |
| Application code and system instructions | Define workflow authority and deterministic contracts; code quality still matters. |
| User input | Untrusted analytical data; suspicious content is preserved rather than executed. |
| Retrieved cards | Candidate guidance/evidence; membership does not independently verify a claim. |
| Model output | Untrusted generated content, even when it is valid JSON. |
| Python controls | Enforce schemas and source contracts; do not prove semantic truth. |
| Human review | Makes operational and governance decisions; the application has no action tools. |

The system has no RBAC, containment tools, or live threat-intelligence integrations.
It should remain local. Prompt delimiters, schemas, and source allowlists address
different problems; none replaces the others or makes a model infallible.

## 17. Connecting the project to interviews

When describing this project, start with one concrete request and explain why
each boundary exists. Pydantic demonstrates defensive API design. Reference
scoring demonstrates an understandable retrieval baseline. The Ollama wrapper
demonstrates local inference and structured-output integration. Source filtering
demonstrates enforcing provenance in ordinary code. Document identities and
SQLite demonstrate state modeling and idempotent processing. The benchmark
demonstrates controlled measurement and the ability to report limitations.

The strongest explanation separates implemented behavior from desired behavior.
The model is instructed to distinguish evidence from inference; Python verifies
the resulting types and source membership; a human must still assess whether the
findings are sound. Use the actual results in the evaluation report when discussing
security outcomes, including any failures or regressions.
