"""Separate Microsoft case evidence from adapter-authored ranking instructions."""

import json

from app.microsoft_evidence import microsoft_evidence
from app.schemas import SocAlertRequest

TABLE_CATEGORIES = {
    "DeviceProcessEvents": "process",
    "DeviceNetworkEvents": "network connection",
    "DeviceLogonEvents": "authentication",
    "SigninLogs": "authentication",
}


def soc_retrieval_query(request: SocAlertRequest) -> str:
    evidence = microsoft_evidence(request.model_dump(mode="json"))
    if evidence is None:
        return request.model_dump_json()
    categories = sorted(
        {
            TABLE_CATEGORIES[table]
            for table, rows in evidence.bundle["tables"].items()
            if rows and table in TABLE_CATEGORIES
        }
    )
    # Categories describe supplied table modalities, never event outcomes or grants.
    # Preserve every table observation, including allegations/negated mentions.
    # The routing case ID is not a behavioral search term; it remains in the prompt.
    return json.dumps(
        {"observations": evidence.bundle["tables"], "event_categories": categories},
        sort_keys=True,
        ensure_ascii=False,
    )
