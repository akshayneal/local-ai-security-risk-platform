import json
from pathlib import Path

import pytest

from app.prompts import build_soc_prompt
from app.soc_inputs import (
    MAX_INPUT_BYTES,
    MicrosoftSocAdapter,
    SocInputError,
    canonical_bundle,
    parse_csv_bundle,
    parse_json_bundle,
)

SAMPLES = Path(__file__).resolve().parents[1] / "sample_data/microsoft"


@pytest.mark.parametrize("path", sorted(SAMPLES.glob("*.json")))
def test_samples_lossless_and_provenance(path):
    bundle = parse_json_bundle(path.read_bytes())
    case = MicrosoftSocAdapter().normalize(bundle)
    assert json.loads(case.request.raw_log) == bundle
    assert case.request.raw_log == canonical_bundle(bundle)
    for observation in case.observations:
        assert (
            observation.value
            == bundle["tables"][observation.table][observation.row][observation.field]
        )
    assert len(case.observations) == sum(
        len(row) for rows in bundle["tables"].values() for row in rows
    )


def test_multiple_alerts_orphans_duplicates_and_unknown_fields():
    bundle = {
        "case_id": "TEST",
        "tables": {
            "AlertInfo": [{"AlertId": "A"}, {"AlertId": "B"}],
            "AlertEvidence": [
                {
                    "AlertId": "A",
                    "DeviceName": "one",
                    "Unknown": {"x": [1, True, None]},
                },
                {"AlertId": "C", "AccountUpn": "two@example.invalid"},
                {"AlertId": "A", "DeviceName": "one"},
            ],
        },
    }
    case = MicrosoftSocAdapter().normalize(bundle)
    assert case.alert_links == {
        "A": ["AlertInfo[0]", "AlertEvidence[0]", "AlertEvidence[2]"],
        "B": ["AlertInfo[1]"],
        "C": ["AlertEvidence[1]"],
    }
    assert case.entities == ["one", "two@example.invalid"]
    assert case.request.known_indicators == case.entities
    assert any("Orphan" in w for w in case.warnings)
    assert any("no matching" in w for w in case.warnings)
    assert json.loads(case.request.raw_log) == bundle


def test_port_uncertainty_conflict_and_injection_boundary():
    for number, word in [(3, "HTTPS"), (4, "severity values differ")]:
        path = next(SAMPLES.glob(f"MSFT-00{number}*.json"))
        case = MicrosoftSocAdapter().normalize(parse_json_bundle(path.read_bytes()))
        assert any(word in w for w in case.warnings)
    case = MicrosoftSocAdapter().normalize(
        parse_json_bundle(next(SAMPLES.glob("MSFT-002*.json")).read_bytes())
    )
    assert "IGNORE ALL PREVIOUS INSTRUCTIONS" in case.request.raw_log
    prompt = build_soc_prompt(case.request, "No local references.")
    assert "IGNORE ALL PREVIOUS INSTRUCTIONS" not in prompt
    assert "potential instruction-like content removed" in prompt


def test_csv_windows_newlines_bom_exact_values_and_explicit_table():
    text = '\ufeffRemoteIP,RemotePort,ProcessCommandLine\r\n203.0.113.4,00443,"echo a,b\r\nnext"\r\n'
    bundle = parse_csv_bundle(text, "DeviceNetworkEvents", "CSV")
    row = bundle["tables"]["DeviceNetworkEvents"][0]
    assert row == {
        "RemoteIP": "203.0.113.4",
        "RemotePort": "00443",
        "ProcessCommandLine": "echo a,b\r\nnext",
    }
    assert json.loads(MicrosoftSocAdapter().normalize(bundle).request.raw_log) == bundle


@pytest.mark.parametrize(
    "data",
    [
        b"[]",
        b"{}",
        b'{"case_id":"X","tables":{},"extra":1}',
        b'{"case_id":"X","tables":{"Unknown":[{}]}}',
        b'{"case_id":"X","tables":{"AlertInfo":[1]}}',
        b'{"case_id":"X","tables":{"AlertInfo":{}}}',
        b'{"case_id":"X","tables":{"AlertInfo":[{"X":NaN}]}}',
        b'{"case_id":"X","case_id":"Y","tables":{"AlertInfo":[{}]}}',
        b"[" * 1000,
        b"\xff",
        b" " * (MAX_INPUT_BYTES + 1),
    ],
    ids=[f"invalid-{i}" for i in range(11)],
)
def test_reject_invalid_json(data):
    with pytest.raises(SocInputError):
        parse_json_bundle(data)


@pytest.mark.parametrize(
    "tables",
    [
        {"AlertInfo": [{}] * 51},
        {t: [{}] * 40 for t in ("AlertInfo", "AlertEvidence", "SigninLogs")},
        {"AlertInfo": [{"X": "a" * 4097}]},
        {"AlertInfo": [{str(i): i for i in range(65)}]},
        {"AlertInfo": [{"X": [list(range(100))] * 51}]},
        {"AlertInfo": [{"X": "a" * 4000} for _ in range(21)]},
    ],
)
def test_direct_adapter_bounds(tables):
    with pytest.raises(SocInputError):
        MicrosoftSocAdapter().normalize({"case_id": "X", "tables": tables})


@pytest.mark.parametrize(
    "text,table",
    [
        ("a,a\n1,2", "AlertInfo"),
        ("a,b\n1", "AlertInfo"),
        ("a\n1,2", "AlertInfo"),
        ("a\n1", "Unknown"),
        ("a\n" + "1\n" * 51, "AlertInfo"),
    ],
)
def test_invalid_csv(text, table):
    with pytest.raises(SocInputError):
        parse_csv_bundle(text, table, "CSV")
