"""Inspect adapter-owned query terms without changing retrieval or calling a model."""

import json

from app.reference_loader import (
    get_relevant_references,
    load_references,
    normalize_text,
    score_reference,
)
from app.soc_inputs import MicrosoftSocAdapter
from evals.microsoft_reliability.cases import load_cases
from evals.microsoft_reliability.runner import request_for


def collect() -> dict:
    card = next(
        c
        for c in load_references("soc_alert")
        if c["source_id"] == "SOC-BRUTE-FORCE-SUCCESS"
    )
    cases = load_cases()
    requests = [
        (key, request_for(next(c for c in cases if c["case_id"] == key)))
        for key in ("REL-SOC-002", "REL-SOC-006", "REL-SOC-010")
    ]
    authentication = (
        MicrosoftSocAdapter()
        .normalize(
            {
                "case_id": "SYN-QUERY-AUTH",
                "tables": {
                    "SigninLogs": [
                        {
                            "UserPrincipalName": "synthetic-query@example.invalid",
                            "ResultType": "50126",
                            "ResultDescription": "Failed authentication",
                        },
                        {
                            "UserPrincipalName": "synthetic-query@example.invalid",
                            "ResultType": "0",
                            "ResultDescription": "Successful authentication",
                        },
                    ]
                },
            }
        )
        .request
    )
    requests.append(("SYN-QUERY-AUTH", authentication))
    records = []
    for key, request in requests:
        variants = {
            "full_request": request.model_dump_json(),
            "without_adapter_behavior": json.dumps(
                {
                    k: v
                    for k, v in request.model_dump(mode="json").items()
                    if k != "observed_behavior"
                }
            ),
            "raw_evidence_only": request.raw_log,
        }
        records.append(
            {
                "case_id": key,
                "query_variants": {
                    name: {
                        "authentication_card_score": score_reference(
                            set(normalize_text(query)), card
                        ),
                        "top5_ids": [
                            c["source_id"]
                            for c in get_relevant_references("soc_alert", query, 5)
                        ],
                    }
                    for name, query in variants.items()
                },
            }
        )
    return {
        "scope": "read-only lexical-query diagnosis; no model calls, no production change, no support/abstention claim",
        "planned_controls": [
            "process enumeration",
            "network connection",
            "credential-access evidence",
            "synthetic true authentication",
        ],
        "records": records,
    }
