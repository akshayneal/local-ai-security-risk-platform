"""Pre-treatment compatibility probes against the unchanged textual recognizer.

These document bounded behavior; they do not ascribe values to discarded live
responses and remain independent of any subsequent structured compatibility path.
"""

import json

import pytest

from app.observables import endpoint_violations, network_endpoints
from app.soc_inputs import MicrosoftSocAdapter


@pytest.fixture
def network_request():
    return (
        MicrosoftSocAdapter()
        .normalize(
            {
                "case_id": "SYN-PROBE",
                "tables": {
                    "DeviceNetworkEvents": [
                        {
                            "LocalIP": "192.0.2.31",
                            "LocalPort": 50131,
                            "RemoteIP": "203.0.113.31",
                            "RemotePort": 443,
                        },
                        {
                            "LocalIP": "192.0.2.32",
                            "LocalPort": 50132,
                            "RemoteIP": "203.0.113.32",
                            "RemotePort": 8443,
                            "Protocol": "Tcp",
                        },
                    ]
                },
            }
        )
        .request
    )


@pytest.mark.parametrize(
    "prose",
    [
        "203.0.113.31:443",
        "192.0.2.31:50131",
        "destination_ip=203.0.113.31 destination_port=443",
        "to 203.0.113.31 on port 443",
    ],
)
def test_legacy_false_rejection_of_valid_structured_pairs(network_request, prose):
    assert network_endpoints(network_request.raw_log) == set()
    assert endpoint_violations(prose, network_request.raw_log, field="summary") == [
        "summary contains an endpoint relationship absent from the original request"
    ]


@pytest.mark.parametrize(
    "prose", ["203.0.113.31:8443", "203.0.113.31:50131", "203.0.113.99:443"]
)
def test_legacy_correct_rejections_include_cross_row_and_local_port(
    network_request, prose
):
    assert endpoint_violations(prose, network_request.raw_log, field="summary")


def test_json_fields_are_not_textual_grammar(network_request):
    assert not network_endpoints('{"RemoteIP":"203.0.113.31","RemotePort":443}')
    assert not endpoint_violations(
        '{"RemoteIP":"203.0.113.31","RemotePort":8443}',
        network_request.raw_log,
        field="summary",
    )
    rows = json.loads(network_request.raw_log)["tables"]["DeviceNetworkEvents"]
    assert "Protocol" not in rows[0]
    assert rows[1]["Protocol"] == "Tcp"


def test_generic_text_roles_and_protocol_behavior_are_bounded():
    original = "source_ip=192.0.2.31 destination_ip=203.0.113.31 destination_port=443"
    assert not endpoint_violations("203.0.113.31:443", original, field="summary")
    assert endpoint_violations("source_ip=203.0.113.31", original, field="summary")
    # Protocol correctness is prompt/manual, never claimed by this recognizer.
    assert not endpoint_violations("HTTPS traffic", original, field="summary")
