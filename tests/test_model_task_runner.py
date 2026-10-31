"""Real analyzer seams with fake completed streams; no local provider requests."""

import json

import pytest

from app import ollama_client
from evals.model_task_diagnostic_v1 import runner, transport
from evals.model_task_diagnostic_v1.umbrella import CampaignLedger


def install(monkeypatch, payloads, calls):
    iterator = iter(payloads)

    class Connection:
        def __init__(self, deadline, clock):
            self.payload = next(iterator)

        def request(self, method, path, *, body, headers):
            calls.append(json.loads(body))
            assert method == "POST" and path == "/api/chat"

        def getresponse(self):
            payload = self.payload

            class Response:
                status = 200
                sent = False

                def read1(self, size):
                    if self.sent:
                        return b""
                    self.sent = True
                    return (
                        transport.encoded(
                            {
                                "model": transport.MODEL,
                                "done": True,
                                "done_reason": "stop",
                                "message": {
                                    "role": "assistant",
                                    "content": json.dumps(payload),
                                },
                                "eval_count": 50,
                            }
                        )
                        + b"\n"
                    )

                def close(self):
                    pass

            return Response()

        def close(self):
            pass

    monkeypatch.setattr(transport, "_Connection", Connection)


def invoke(
    tmp_path,
    monkeypatch,
    cases,
    payloads,
    *,
    formulation="full",
    mode="off",
    contrast="D1",
):
    calls = []
    install(monkeypatch, payloads, calls)
    root = tmp_path / "workspaces"
    lab = root / "lab/accounting"
    with (
        CampaignLedger(
            root / "campaign",
            lab_journal=lab / "journal.jsonl",
            acceptance_journal=root / "acceptance/accounting/journal.jsonl",
        ) as umbrella,
        transport.DiagnosticBudget(lab, umbrella=umbrella) as budget,
    ):
        rows = runner.execute(
            cases,
            budget,
            trial="mock-trial",
            contrast=contrast,
            mode=mode,
            formulation=formulation,
            ledger=False,
            reason="",
        )
        return rows, budget.snapshot(), calls


@pytest.mark.parametrize("mode", ["default", "off", "on"])
@pytest.mark.parametrize("formulation", ["full", "narrow"])
def test_real_analyzer_uses_one_counted_stream_and_restores_default(
    tmp_path, monkeypatch, mode, formulation
):
    original = ollama_client._complete_context_chat
    raw = (
        {
            "findings": [],
            "evidence_gaps": ["Independent testing not supplied."],
            "human_review_requirements": ["Human review required."],
        }
        if formulation == "full"
        else {
            "decision": "no_finding",
            "rationale": "Unverified software stub.",
            "supporting_facts": ["Declared input remains supplied data."],
            "missing_prerequisites": ["Independent testing."],
            "validation_recommendations": ["Human review."],
        }
    )
    rows, budget, calls = invoke(
        tmp_path,
        monkeypatch,
        runner.read("cases.json")[:1],
        [raw],
        formulation=formulation,
        mode=mode,
        contrast="D2",
    )
    assert rows[0]["state"] == "RETURNED" and rows[0]["raw_attempts"] == 1
    assert budget["raw_attempts"] == 1 and budget["phase_counts"]["D2"] == 1
    assert len(calls) == 1 and calls[0]["options"] == transport.OPTIONS
    assert ("think" in calls[0]) is (mode != "default")
    if mode != "default":
        assert calls[0]["think"] is (mode == "on")
    assert ollama_client._complete_context_chat is original
    # This asserts plumbing only; the positive graph's zero-finding stub is NOT a semantic pass.
    assert rows[0]["semantic_judgment"] == "PENDING"


def test_invalid_completed_json_is_withheld_without_transport_retry(
    tmp_path, monkeypatch
):
    rows, budget, calls = invoke(
        tmp_path,
        monkeypatch,
        runner.read("cases.json")[:1],
        [{"unexpected": "schema-invalid"}],
    )
    assert rows[0]["state"] == "WITHHELD"
    assert budget["raw_attempts"] == len(calls) == 1 and not budget["blocked"]


def test_actual_soc_single_repair_consumes_two_phase_reservations(
    tmp_path, monkeypatch
):
    case = runner.read("cases.json")[2]
    raw = {
        "alert_id": case["input"]["alert_id"],
        "severity": "low",
        "likely_incident_type": "Unknown cause",
        "summary": "One supplied failed TCP check on elm-calibration-3.",
        "mitre_mapping": [],
        "recommended_containment": [],
        "recommended_investigation_steps": [
            "Verify listener ownership with the operator."
        ],
        "false_positive_considerations": [
            "Check is within the supplied limited approval."
        ],
        "evidence_gaps": ["Failure cause unknown."],
        "analyst_note": "No actions executed.",
        "observed_evidence": [],
        "analyst_inferences": [],
        "source_references": [],
    }
    valid = raw | {
        "observed_evidence": [
            "Device elm-calibration-3 reported ConnectionFailed: 192.0.2.170:51234 to 203.0.113.170:9445 using TCP."
        ]
    }
    rows, budget, calls = invoke(
        tmp_path, monkeypatch, [case], [raw, valid], contrast="D3"
    )
    assert rows[0]["state"] == "RETURNED"
    assert budget["raw_attempts"] == budget["phase_counts"]["D3"] == len(calls) == 2


def test_fixed_pairs_cannot_be_filtered_or_narrowed_in_mode_comparison():
    assert len(runner.selected_cases("D1", "full", (), "")) == 2
    with pytest.raises(ValueError):
        runner.selected_cases("D1", "narrow", (), "")
    with pytest.raises(ValueError):
        runner.selected_cases("D2", "full", ["ELM-SEC-NUMERIC-V1"], "")
    with pytest.raises(ValueError):
        runner.selected_cases("D4", "narrow", ["ELM-SEC-NUMERIC-V1"], "")


def test_existing_trial_refused_before_new_budget_or_provider_send(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(runner, "LAB", tmp_path / "accounting")
    monkeypatch.setattr(runner, "verify_plan", dict)
    monkeypatch.setattr(runner, "preflight", lambda: {"metadata_only": True})
    directory = runner.LAB / "trials/fixed-trial"
    directory.mkdir(parents=True)
    with pytest.raises(FileExistsError):
        runner.run(trial="fixed-trial", contrast="D1")
    assert not (runner.LAB / "journal.jsonl").exists()
