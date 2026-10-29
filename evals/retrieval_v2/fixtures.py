"""Author the V2 fixtures before viewing candidate results. Synthetic lab rules."""

import json
from pathlib import Path

from app.retrieval.contracts import Authority, EvidenceRecord, RetrievalQuery, Workflow
from app.retrieval.storage import canonical_value

ROOT = Path(__file__).parent
# Topic, workflow, requirement chunk, procedure chunk, fresh compound question.
TOPICS = [
    (
        "custody",
        Workflow.SOC,
        "LAB-EC-21 requires original event exports to be hashed before analyst transformations. Retain the original export separately.",
        "Custody handoff records the exporting analyst, export time, hash and each recipient. A working copy can be transformed without replacing the original.",
        "How should the lab preserve an event export before editing it, and what must accompany a transfer to another analyst?",
    ),
    (
        "transport",
        Workflow.SOC,
        "LAB-NT-22 requires a protocol field or explicit application-layer observation before naming an application protocol. Destination port alone is insufficient.",
        "For uncertain transport, obtain packet or TLS/application telemetry and retain the exact source and destination endpoints. Distinguish TCP from an HTTPS assertion.",
        "What evidence permits naming the service on a network connection, and what should an investigator collect if only endpoints are known?",
    ),
    (
        "authentication",
        Workflow.SOC,
        "LAB-ID-23 treats successful multifactor authentication as an authentication observation, not proof that the person using the session was legitimate.",
        "Review device compliance, token/session context and user confirmation. A different location can be explained by a VPN; unfamiliar geography alone does not establish compromise.",
        "Does a completed second factor settle whether the session belongs to the real user, and which contextual checks should follow?",
    ),
    (
        "process-link",
        Workflow.SOC,
        "LAB-PC-24 correlates a process with network events using device identity, process identifier and process creation time. A process name alone is insufficient.",
        "Compare ProcessId and ProcessCreationTime with InitiatingProcessId and InitiatingProcessCreationTime on the same DeviceId. Reused process IDs require a time-qualified match.",
        "Which keys tie an executable instance to its outbound traffic, and how should reused numeric process identifiers be handled?",
    ),
    (
        "severity",
        Workflow.SOC,
        "LAB-SV-25 preserves differing alert and incident severities as separate vendor observations. Platform severity requires the analyst's evidence-based assessment.",
        "Record each source's severity and aggregation scope. Investigate whether an incident includes additional alerts before explaining a disagreement.",
        "How should an analyst handle an incident marked high and its alert marked medium, and what aggregation detail could explain the difference?",
    ),
    (
        "containment",
        Workflow.SOC,
        "LAB-CT-26 requires accountable approval before host isolation. An assistant may propose a containment action but cannot execute it.",
        "Confirm asset ownership, business impact and authorization with the incident lead before an operator isolates the host. Preserve the rationale and approval record.",
        "Who must authorize isolating a workstation, and what operational checks precede the operator's action?",
    ),
    (
        "sharepoint",
        Workflow.AI_RISK,
        "LAB-SP-31 requires SharePoint retrieval to respect the requesting employee's document permissions. Service-account visibility cannot substitute for user access.",
        "Test access trimming with allowed and denied users, including snippets and citations. Recheck permission changes and avoid leaking cached document previews.",
        "How can a company assistant avoid exposing files visible only to its connector, and what should permission-change tests inspect?",
    ),
    (
        "hiring",
        Workflow.AI_RISK,
        "LAB-HR-32 requires a recruiter to review resume rankings before adverse hiring decisions. Candidate rankings alone must not trigger rejection.",
        "Evaluate subgroup error rates and the relevance of ranking features. Document recruiter overrides and provide an accountable path for candidate challenge.",
        "What human decision boundary applies to applicant ranking, and which fairness and challenge controls belong in the review?",
    ),
    (
        "agent-actions",
        Workflow.AI_RISK,
        "LAB-AG-33 requires a human approval gate before an agent invokes identity-changing Graph or Logic Apps actions. Read access does not authorize writes.",
        "Use least-privilege action scopes, an action preview and an approval record. An approval must bind the proposed target and operation; changed targets require fresh approval.",
        "What separates an agent reading directory data from changing an account, and what must an approval bind?",
    ),
    (
        "plugin-egress",
        Workflow.AI_RISK,
        "LAB-PL-34 requires review of sensitive-data disclosure before enabling a third-party assistant extension. A vendor brand alone is not authorization to share data.",
        "Inventory transmitted fields, recipient retention and onward sharing. Reduce fields and test the extension with synthetic records before granting production access.",
        "What should be checked before an assistant sends confidential records to an outside extension, and how can disclosure be reduced?",
    ),
    (
        "review-consistency",
        Workflow.AI_RISK,
        "LAB-RV-35 treats a proposal claiming both mandatory human review and automatic irreversible action as an unresolved design conflict.",
        "Request an explicit state transition diagram with the reviewer decision before the action. Confirm failure and timeout behavior instead of assuming the oversight claim is effective.",
        "How should a review handle a design that promises human signoff while acting automatically, and what artifact clarifies the action order?",
    ),
    (
        "faq",
        Workflow.AI_RISK,
        "LAB-FAQ-36 limits a read-only internal FAQ assistant to approved nonsensitive material. It has no authority to change accounts or initiate external actions.",
        "Keep citations and a route for reporting incorrect answers. Define retention with the data owner; these notes prescribe no universal retention duration.",
        "What bounds a low-impact internal question-answering tool, and how should errors and conversation retention be handled?",
    ),
]


def author_suite() -> tuple[list, list]:
    records, cases = [], []
    for index, (topic, workflow, first, second, question) in enumerate(TOPICS, 1):
        prefix = f"V2-{index:02}"
        common = {
            "source_type": "lab_note",
            "source_family": "Synthetic lab",
            "workflows": frozenset({workflow}),
            "applicability": frozenset({"lab"}),
            "synthetic": True,
        }
        chunks = []
        for suffix, text in (("a", first), ("b", second)):
            chunks.append(
                EvidenceRecord(
                    evidence_id=f"{prefix}-{suffix}",
                    source_id=prefix,
                    title=f"{topic} handling",
                    content=text,
                    document_id=prefix,
                    document_version_id=f"{prefix}-current",
                    chunk_id=f"{prefix}-{suffix}",
                    authority=Authority.POLICY,
                    policy_scope="synthetic-lab",
                    **common,
                )
            )
        records.extend(chunks)
        records.append(
            EvidenceRecord(
                evidence_id=f"{prefix}-alt",
                source_id=f"{prefix}-alt",
                title=f"{topic} training note",
                content="Alternate analyst summary: " + first,
                authority=Authority.LOCAL,
                **common,
            )
        )
        # Strongly related but categorically ineligible variants. No result-driven tuning.
        for suffix, changes in (
            (
                "obsolete",
                {"status": "inactive", "document_version_id": f"{prefix}-old"},
            ),
            ("restricted", {"required_scopes": frozenset({"private-investigations"})}),
            ("other-scope", {"policy_scope": "another-organization"}),
            ("other-use", {"applicability": frozenset({"production-only"})}),
            (
                "other-workflow",
                {
                    "workflows": frozenset(
                        {Workflow.AI_RISK if workflow == Workflow.SOC else Workflow.SOC}
                    )
                },
            ),
        ):
            original = chunks[0].model_dump()
            original.update(
                evidence_id=f"{prefix}-{suffix}",
                chunk_id=f"{prefix}-{suffix}",
                content=first
                + " Superseded or differently scoped copy: do the opposite.",
                **changes,
            )
            records.append(EvidenceRecord(**original))
        query = RetrievalQuery(
            text=f"What does {first.split()[0]} require?",
            workflow=workflow,
            policy_scopes=frozenset({"synthetic-lab"}),
            applicability=frozenset({"lab"}),
            as_of="2026-10-29",
        )
        forbidden = [
            f"{prefix}-{s}"
            for s in (
                "obsolete",
                "restricted",
                "other-scope",
                "other-use",
                "other-workflow",
            )
        ]
        cases.append(
            {
                "case_id": f"R2-ID-{index:02}",
                "category": "exact_identifier",
                "query": query,
                "relevance": {f"{prefix}-a": 3, f"{prefix}-alt": 2},
                "required": [],
                "forbidden": forbidden,
                "rationale": "Either the current requirement chunk or its alternate summary supports the answer.",
            }
        )
        cases.append(
            {
                "case_id": f"R2-MULTI-{index:02}",
                "category": "multi_chunk",
                "query": query.model_copy(update={"text": question}),
                "relevance": {f"{prefix}-a": 3, f"{prefix}-b": 3, f"{prefix}-alt": 2},
                "required": [f"{prefix}-b"],
                "required_groups": [[f"{prefix}-a", f"{prefix}-alt"], [f"{prefix}-b"]],
                "forbidden": forbidden,
                "rationale": "Requirement plus adjacent procedure are needed; the alternate can replace the requirement chunk.",
            }
        )
        if index <= 6:
            cases.append(
                {
                    "case_id": f"R2-GATE-{index:02}",
                    "category": "scope_version_access",
                    "query": query.model_copy(
                        update={
                            "text": f"Current synthetic lab {topic} handling requirement",
                            "authorities": frozenset({Authority.POLICY}),
                        }
                    ),
                    "relevance": {f"{prefix}-a": 3},
                    "required": [f"{prefix}-a"],
                    "forbidden": forbidden,
                    "rationale": "Only current accessible applicable policy in the requested scope qualifies.",
                }
            )
    negatives = [
        (
            Workflow.SOC,
            "What is the mandatory 72-hour incident notification deadline for this lab?",
        ),
        (
            Workflow.SOC,
            "Is 198.51.100.143 currently a verified malicious command-and-control address?",
        ),
        (
            Workflow.SOC,
            "Which CVE explains this workstation's infection and what CVSS score applies?",
        ),
        (
            Workflow.SOC,
            "What is the lab's required forensic evidence retention duration in days?",
        ),
        (
            Workflow.SOC,
            "Which named operator approved isolation of workstation-57 yesterday?",
        ),
        (
            Workflow.AI_RISK,
            "How many days must SharePoint assistant conversations be retained under the lab rule?",
        ),
        (
            Workflow.AI_RISK,
            "Which exact recruiter approved candidate Morgan's rejection?",
        ),
        (
            Workflow.AI_RISK,
            "What is the mandatory fairness error-rate threshold for applicant ranking?",
        ),
        (
            Workflow.AI_RISK,
            "Which region does the outside extension use to store confidential records?",
        ),
        (
            Workflow.AI_RISK,
            "What is the exact legal penalty for an agent changing a directory account?",
        ),
    ]
    for i, (workflow, text) in enumerate(negatives, 1):
        cases.append(
            {
                "case_id": f"R2-NONE-{i:02}",
                "category": "no_answer",
                "query": RetrievalQuery(
                    text=text,
                    workflow=workflow,
                    policy_scopes=frozenset({"synthetic-lab"}),
                    applicability=frozenset({"lab"}),
                    as_of="2026-10-29",
                ),
                "relevance": {},
                "required": [],
                "forbidden": [],
                "rationale": "Related guidance exists but no eligible record supplies the requested fact. Expected retrieval is empty.",
            }
        )
    return records, cases


if __name__ == "__main__":
    records, cases = author_suite()
    for name, values in (("corpus.json", records), ("cases.json", cases)):
        (ROOT / name).write_text(
            json.dumps(canonical_value(values), indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
