"""No inference: count real dispatch boundaries, frozen identities and failures."""

import json
from contextlib import contextmanager
from pathlib import Path

import pytest

from evals.deterministic_evidence_v1 import runner
from evals.deterministic_evidence_v1 import transport as t

CASES = json.loads(Path("evals/deterministic_evidence_v1/dev_cases.json").read_bytes())
MESSAGES = [{"role": "user", "content": "Synthetic public input"}]
SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
OPTIONS = {"temperature": 0.1, "num_ctx": 32768}


@contextmanager
def accounting(tmp_path, track="lab"):
    with (
        t.CampaignLedger(
            tmp_path / "campaign",
            lab_journal=tmp_path / "lab/journal.jsonl",
            acceptance_journal=tmp_path / "acceptance/journal.jsonl",
        ) as campaign,
        t.DiagnosticBudget(tmp_path / track, umbrella=campaign, track=track) as budget,
    ):
        budget.begin(
            "LARCH-TEST", trial="test", contrast="D0" if track == "lab" else "A"
        )
        yield budget, campaign


def wire(content='{"ok":true}', **changes):
    row = {
        "model": t.MODEL,
        "done": True,
        "done_reason": "stop",
        "message": {"role": "assistant", "content": content},
        "eval_count": 12,
        "prompt_eval_count": 200,
    }
    row.update(changes)
    return t.encoded(row) + b"\n"


def install(monkeypatch, budget, chunks):
    calls = []

    class Connection:
        def __init__(self, deadline, clock):
            assert 719 < deadline - clock() <= 720
            self.chunks = iter(chunks)

        def request(self, method, path, *, body, headers):
            local = [
                json.loads(l)
                for l in (budget.root / "journal.jsonl").read_bytes().splitlines()
            ]
            assert local[-1]["event"] == "provider_reserved"
            assert budget.umbrella.pending == (budget.track, budget.pending)
            calls.append(json.loads(body))

        def getresponse(self):
            return self

        status = 200

        def read1(self, n):
            v = next(self.chunks, b"")
            if isinstance(v, BaseException):
                raise v
            return v

        def close(self):
            pass

    monkeypatch.setattr(t, "_Connection", Connection)
    return calls


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_actual_counted_wire_delivers_every_required_value_and_exports(
    case, tmp_path, monkeypatch
):
    with accounting(tmp_path) as (b, c):
        raw = {
            "decision": "no_finding",
            "explanation": "Unverified interpretation",
            "fact_ids": [],
            "unknowns": [],
            "validation": ["Human validation"],
        }
        calls = install(monkeypatch, b, [wire(json.dumps(raw))])
        output = runner.execute(case, "F3", b)
        assert b.count == c.counts["lab"] == len(calls) == 1
        assert calls[0]["options"] == t.OPTIONS and calls[0]["think"] is False
        assert calls[0]["truncate"] is calls[0]["shift"] is False
        delivered = json.loads(calls[0]["messages"][1]["content"])["untrusted_facts"]
        expected = {f["path"]: f["value"] for f in case["expected_facts"]}
        assert {f["path"]: f["value"] for f in delivered} == expected
        assert {
            f["input_path"]: f["value"] for f in output["report"]["facts"]
        } == expected
        assert output["required_omissions"] == 0


@pytest.mark.parametrize(
    "chunks",
    [
        [TimeoutError()],
        [b"not json\n"],
        [wire(done_reason="unknown")],
        [wire(model="other")],
        [wire(done=False)],
        [wire(message={"role": "assistant", "content": "<think>unfinished"})],
    ],
)
def test_unknown_stops_all_new_sends_and_reopen(tmp_path, monkeypatch, chunks):
    with accounting(tmp_path) as (b, c):
        calls = install(monkeypatch, b, chunks)
        with pytest.raises(t.DiagnosticStop):
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        assert b.count == 1 and b.blocked and c.blocked
        with pytest.raises(t.DiagnosticStop):
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        assert len(calls) == 1
    with pytest.raises(t.CampaignStop):
        t.CampaignLedger(
            tmp_path / "campaign",
            lab_journal=tmp_path / "lab/journal.jsonl",
            acceptance_journal=tmp_path / "acceptance/journal.jsonl",
        )


def test_known_censor_thought_redaction_and_context_pre_send_refusal(
    tmp_path, monkeypatch
):
    with accounting(tmp_path) as (b, c):
        calls = install(
            monkeypatch,
            b,
            [
                wire(
                    "<think>HIDDEN_REASON</think>{}",
                    message={
                        "role": "assistant",
                        "thinking": "HIDDEN_CHANNEL",
                        "content": "<think>HIDDEN_REASON</think>{}",
                    },
                    done_reason="length",
                )
            ],
        )
        with pytest.raises(
            t.DiagnosticStop, match="supported context or generation limits"
        ):
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        assert not b.blocked and not c.blocked and b.count == 1
        assert all(
            b"HIDDEN" not in p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
        )
        with pytest.raises(t.DiagnosticStop):
            b.chat(
                [{"role": "user", "content": "x" * 30000}], SCHEMA, OPTIONS, think=False
            )
        assert b.count == len(calls) == 1


def test_all_caps_are_disjoint_and_phase_caps_survive_reopen(tmp_path, monkeypatch):
    with accounting(tmp_path) as (b, c):
        for phase, count in [("D0", 12), ("D1", 8), ("D3", 4)]:
            b.begin("LARCH-TEST", trial="test", contrast=phase)
            for _ in range(count):
                install(monkeypatch, b, [wire()])
                b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
            with pytest.raises(t.DiagnosticStop):
                b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        assert b.count == 24 and c.counts == {"lab": 24, "acceptance": 0}
    with accounting(tmp_path, "acceptance") as (b, c):
        for _ in range(12):
            install(monkeypatch, b, [wire()])
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        with pytest.raises(t.DiagnosticStop):
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        assert c.snapshot()["reserved"] == 36 and c.counts == {
            "lab": 24,
            "acceptance": 12,
        }
    with accounting(tmp_path) as (b, c):
        assert b.count == 24 and b.phase_counts["D0"] == 12
        with pytest.raises(t.DiagnosticStop):
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)


def test_real_soc_repair_uses_two_counted_sends(tmp_path, monkeypatch):
    with accounting(tmp_path) as (b, c):
        b.begin(CASES[0]["id"], trial="repair", contrast="D1")
        outputs = iter(
            [
                {},
                {
                    "alert_id": CASES[0]["id"],
                    "severity": "medium",
                    "likely_incident_type": "Unverified transfer concern",
                    "summary": "One connection succeeded; impact unknown.",
                    "mitre_mapping": [],
                    "recommended_containment": [],
                    "recommended_investigation_steps": [
                        "Have a human verify the transfer scope."
                    ],
                    "false_positive_considerations": [],
                    "evidence_gaps": ["Content and approval unknown."],
                    "analyst_note": "No actions executed.",
                    "observed_evidence": ["A ConnectionSuccess row is supplied."],
                    "analyst_inferences": [],
                    "source_references": [],
                },
            ]
        )
        sent = []

        class C:
            status = 200

            def __init__(self, *args):
                self.done = False

            def request(self, *args, **kwargs):
                sent.append(json.loads(kwargs["body"]))

            def getresponse(self):
                return self

            def read1(self, n):
                if self.done:
                    return b""
                self.done = True
                return wire(json.dumps(next(outputs)))

            def close(self):
                pass

        monkeypatch.setattr(t, "_Connection", C)
        result = runner.execute(CASES[0], "F2", b)
        assert b.count == c.counts["lab"] == len(sent) == 2
        assert result["repair_attempted"] is True and "analysis" in result


def test_freeze_rejects_changed_method_and_acceptance_gate_cannot_create_root(
    monkeypatch,
):
    from evals.deterministic_evidence_v1.acceptance import run

    # No true readiness and no model access; frozen identity validation is separate.
    monkeypatch.setattr(runner, "verify_freeze", lambda: None)
    with pytest.raises(ValueError, match="NOT RUN"):
        run({})
    assert not runner.ACCEPTANCE.exists()


def test_baseline_export_has_no_canonical_fact_panel():
    # Falsification of the previous ownership assumption, not a change to old exports.
    from app.schemas import GovernanceRiskResponse
    from dashboard.exports import export_document

    case = CASES[3]
    raw = {
        "system_name": "MODEL-RENAMED",
        "risk_level": "low",
        "decision": "needs_review",
        "summary": "Generic response",
        "key_risks": [],
        "required_controls": [],
        "human_review_requirements": [],
        "logging_requirements": [],
        "evidence_gaps": [],
        "recommended_next_steps": [],
        "source_references": [],
    }
    old = export_document(
        runner.request(case), GovernanceRiskResponse.model_validate(raw)
    )
    assert "facts" not in old
    assert "nine of nine" not in json.dumps(old)
    assert old["case"]["system_name"] == case["id"]


def test_socket_deadline_and_real_http_framing_ignore_proxy(tmp_path, monkeypatch):
    import io

    content = wire()
    response = (
        b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n"
        + format(len(content), "x").encode()
        + b"\r\n"
        + content
        + b"\r\n0\r\n\r\n"
    )

    class Socket:
        def __init__(self):
            self.source, self.sent, self.timeouts = io.BytesIO(response), [], []

        def settimeout(self, value):
            self.timeouts.append(value)

        def sendall(self, value):
            self.sent.append(value)

        def recv_into(self, value):
            return self.source.readinto(value)

        def close(self):
            pass

    raw, addresses = Socket(), []

    def connect(address, timeout):
        addresses.append((address, timeout))
        return raw

    monkeypatch.setattr(t.socket, "create_connection", connect)
    monkeypatch.setenv("HTTP_PROXY", "http://example.invalid:3128")
    with accounting(tmp_path) as (b, _):
        answer = b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        assert json.loads(answer["message"]["content"]) == {"ok": True}
        assert addresses[0][0] == ("127.0.0.1", 11434) and len(addresses) == 1
        assert all(0 < timeout <= 120 for timeout in raw.timeouts)
        sent = b"".join(raw.sent)
        assert b"POST /api/chat" in sent and b'"num_predict":4096' in sent
    now = [0]
    socket = t._DeadlineSocket(raw, 720, lambda: now[0])
    now[0] = 719
    socket.sendall(b"allowed")
    assert raw.timeouts[-1] == 1
    now[0] = 720
    with pytest.raises(TimeoutError):
        socket.sendall(b"forbidden")


def test_d3_only_replaces_suggestive_identity_and_never_dispatches_gold():
    changed = runner.opaque_governance_cases(CASES)
    originals = [c for c in CASES if c["pillar"] == "governance"]
    for old, new in zip(originals, changed, strict=True):
        assert (
            new["input"] | {"system_name": old["input"]["system_name"]} == old["input"]
        )
        assert (new["question"], new["rule"], new["expected_decision"]) == (
            old["question"],
            old["rule"],
            old["expected_decision"],
        )
        for form in ("F1", "F3"):

            class Capture:
                def chat(self, messages, schema, options, *, think):
                    self.messages = messages
                    return {
                        "message": {
                            "content": json.dumps(
                                {
                                    "decision": "no_finding",
                                    "explanation": "Synthetic test",
                                    "fact_ids": [],
                                    "unknowns": [],
                                    "validation": [],
                                }
                            )
                        }
                    }

            client = Capture()
            runner.execute(new, form, client)
            wire = json.dumps(client.messages)
            assert old["id"] not in wire and new["id"] in wire
            assert all(
                key not in wire
                for key in (
                    "expected_decision",
                    "parent_case_id",
                    "expected_facts",
                    '"control"',
                )
            )


def test_original_literal_freeze_is_anchored_to_preregistration_commit():
    import subprocess

    expected = subprocess.check_output(
        [
            "git",
            "show",
            runner.PREREGISTRATION + ":evals/deterministic_evidence_v1/freeze.json",
        ]
    )
    assert (runner.HERE / "freeze.json").read_bytes() == expected
