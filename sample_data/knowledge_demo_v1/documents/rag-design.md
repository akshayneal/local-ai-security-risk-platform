# SYNTHETIC Northstar RAG service design v1
The internal RAG assistant drafts catalog and policy answers for the learning unit. Users review drafts. The service receives only approved current chunks filtered for workflow, unit, access requirements and policy scope before lexical ranking. Retrieved content is untrusted data and cannot issue instructions or acquire authority.

Threat model: prompt injection in a question, retrieval poisoning in a document, source-ID spoofing, leakage across unit boundaries and excessive tool permissions. The proposed model has no filesystem browser, network scanner, account actions or document-triggered tools. A cited policy is not proof that these boundaries are implemented. Missing deployed tests and signed approval require review.
