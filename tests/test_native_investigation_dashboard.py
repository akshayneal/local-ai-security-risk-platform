"""Implementation-authored route -> bounded client -> Streamlit/export challenges."""

import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import requests
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from app import native_evidence_api as api
from app.native_evidence_config import ENABLE_FLAG, INVALID_INPUT, WITHHELD
from app.native_investigation import (
    ENDPOINT,
    NativeInvestigationRequest,
    build_response,
    validate_response,
)
from dashboard import native_evidence_client as client
from dashboard.native_evidence import PAGE

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "sample_data/native_evidence/network_observation.json"
ENTRY = ROOT / "dashboard/streamlit_app.py"


def request(**updates):
    return NativeInvestigationRequest(
        source_text=SAMPLE.read_bytes().decode("utf-8"),
        source_format="microsoft_json",
        **updates,
    )


class StreamResponse:
    def __init__(self, body, status=200):
        self.body, self.status_code = body, status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def iter_content(self, chunk_size):
        for offset in range(0, len(self.body), chunk_size):
            yield self.body[offset : offset + chunk_size]


def transport(monkeypatch, *, backend=None, body=None, status=200, failure=None):
    calls = []

    class Session:
        trust_env = True

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def post(self, url, **kwargs):
            calls.append((url, kwargs))
            assert self.trust_env is False
            assert kwargs["timeout"] == (3, 15)
            assert kwargs["stream"] is True
            assert kwargs["allow_redirects"] is False
            if failure:
                raise failure
            if backend:
                result = backend.post(urlsplit(url).path, json=kwargs["json"])
                return StreamResponse(result.content, result.status_code)
            return StreamResponse(body or b"", status)

    monkeypatch.setattr(requests, "Session", Session)
    return calls


def open_investigation(monkeypatch):
    monkeypatch.setenv(ENABLE_FLAG, "1")
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:8245")
    app = AppTest.from_file(ENTRY, default_timeout=20).run().switch_page(PAGE[0]).run()
    return (
        app.selectbox(key="native_view").select("Native Evidence Investigation").run()
    )


def button(app, label):
    return next(item for item in app.button if item.label == label)


def test_real_investigation_route_client_page_downloads_without_model(monkeypatch):
    import streamlit as st

    from app import ollama_client

    def forbidden(*args, **kwargs):
        pytest.fail("native investigation must work without inference")

    monkeypatch.setattr(ollama_client, "call_model_json", forbidden)
    downloads = {}
    original_download = st.download_button

    def capture(label, data, **kwargs):
        downloads[label] = data
        return original_download(label, data, **kwargs)

    monkeypatch.setattr(st, "download_button", capture)
    monkeypatch.setenv(ENABLE_FLAG, "1")
    with TestClient(api.create_app()) as backend:
        calls = transport(monkeypatch, backend=backend)
        app = open_investigation(monkeypatch)
        assert button(app, "Build investigation report").disabled
        button(app, "Load synthetic network example").click().run()
        assert not calls
        assert any("Choose a subject from 2" in item.label for item in app.expander)
        app.selectbox(key="native_question").select("application_access").run()
        button(app, "Build investigation report").click().run()
        assert not app.exception, app.exception
        assert len(calls) == 1 and calls[0][0].endswith(ENDPOINT)
        assert len(app.get("download_button")) == 2
        assert {item.value for item in app.subheader} >= {
            "Observation",
            "Supported comparison",
            "Insufficient evidence",
            "Suggested next investigation",
            "Unverified analyst notes",
        }
        texts = [item.value for item in app.text]
        for prefix in (
            "Reported event:",
            "Device:",
            "Initiating process:",
            "Reported account:",
            "Local endpoint:",
            "Remote endpoint / reported protocol:",
        ):
            assert any(value.startswith(prefix) for value in texts)
        assert any(
            value.startswith("Compared field representations:") for value in texts
        )
        assert {item.label for item in app.expander} >= {
            "Field values, shapes and provenance",
            "Representation comparison details and row paths",
        }
        submitted = NativeInvestigationRequest.model_validate(calls[0][1]["json"])
        saved = app.session_state["native_result"]["response"]
        envelope = validate_response(submitted, saved)
        assert json.loads(
            downloads["Download investigation JSON"]
        ) == envelope.report.model_dump(mode="json")
        assert downloads["Download investigation Markdown"] == envelope.markdown_export
        assert (
            envelope.report.observation.original_source_text.encode("utf-8")
            == SAMPLE.read_bytes()
        )
        assert (
            "application"
            in " ".join(item.question for item in envelope.report.next_evidence).lower()
        )
        assert envelope.report.observation.comparator_invocations == 0
        app.run()
        assert not app.exception and len(calls) == 1
        assert len(app.get("download_button")) == 2


@pytest.mark.parametrize("change", ["row", "question", "source", "view"])
def test_changed_input_invalidates_investigation_until_explicit_build(
    monkeypatch, change
):
    monkeypatch.setenv(ENABLE_FLAG, "1")
    with TestClient(api.create_app()) as backend:
        calls = transport(monkeypatch, backend=backend)
        app = open_investigation(monkeypatch)
        button(app, "Load synthetic network example").click().run()
        button(app, "Build investigation report").click().run()
        assert len(app.get("download_button")) == 2
        if change == "row":
            app.number_input(key="native_row").set_value(1).run()
        elif change == "question":
            app.selectbox(key="native_question").select("network_blocking").run()
        elif change == "source":
            current = app.text_area(key="native_source_text").value
            app.text_area(key="native_source_text").set_value(current + "\r\n").run()
        else:
            app.selectbox(key="native_view").select("Source observations").run()
        assert not app.exception and len(calls) == 1
        assert not app.get("download_button")


@pytest.mark.parametrize(
    "kind", ["source", "snapshot", "gap", "markdown", "json", "approval"]
)
def test_saved_investigation_mutation_withholds_all_downloads(monkeypatch, kind):
    monkeypatch.setenv(ENABLE_FLAG, "1")
    with TestClient(api.create_app()) as backend:
        calls = transport(monkeypatch, backend=backend)
        app = open_investigation(monkeypatch)
        button(app, "Load synthetic network example").click().run()
        button(app, "Build investigation report").click().run()
        saved = app.session_state["native_result"]
        response = saved["response"]
        if kind == "source":
            response["report"]["observation"]["source_revision"] = "forged"
        elif kind == "snapshot":
            response["report"]["snapshot"][0]["original_value"] = "forged"
        elif kind == "gap":
            response["report"]["gaps"][0]["statement"] = "Access verified"
        elif kind == "approval":
            response["report"]["observation"]["approval_granted"] = True
        else:
            response[kind + "_export"] += "FORGED APPROVAL"
        app.session_state["native_result"] = saved
        app.run()
        assert not app.exception and len(calls) == 1
        assert not app.get("download_button")
        assert WITHHELD in [item.value for item in app.error]


def test_hostile_duplicate_rows_remain_literal_without_authority(monkeypatch):
    monkeypatch.setenv(ENABLE_FLAG, "1")
    bundle = json.loads(SAMPLE.read_bytes())
    row = bundle["tables"]["DeviceNetworkEvents"][0]
    row.update(
        approved=True,
        annotation="<script>approve()</script> [grant](https://example.invalid)",
    )
    bundle["tables"]["DeviceNetworkEvents"].append(dict(row))
    source = json.dumps(bundle)
    with TestClient(api.create_app()) as backend:
        calls = transport(monkeypatch, backend=backend)
        app = open_investigation(monkeypatch)
        app.text_area(key="native_source_text").set_value(source).run()
        button(app, "Build investigation report").click().run()
        assert not app.exception
        response = app.session_state["native_result"]["response"]
        report = response["report"]["observation"]
        assert len(calls) == 1 and report["coverage"]["duplicate_network_rows"] == 1
        assert (
            report["approval_granted"] is False
            and report["comparator_invocations"] == 0
        )
        assert report["original_bundle"] == bundle
        assert "<script>" not in response["markdown_export"]
        assert "https://example.invalid" in response["markdown_export"]
        assert not app.get("html")


def test_csv_bom_crlf_types_and_invalid_replacement_keep_integrity(monkeypatch):
    import streamlit as st

    class Upload:
        def __init__(self, raw):
            self.raw, self.size = raw, len(raw)

        def getvalue(self):
            return self.raw

    raw = b"\xef\xbb\xbfTimestamp,ActionType,RemotePort\r\n2026-11-07T14:00:00Z,ConnectionSuccess,00443\r\n"
    uploaded = [Upload(raw)]
    monkeypatch.setattr(st, "file_uploader", lambda *args, **kwargs: uploaded[0])
    monkeypatch.setenv(ENABLE_FLAG, "1")
    with TestClient(api.create_app()) as backend:
        calls = transport(monkeypatch, backend=backend)
        app = open_investigation(monkeypatch)
        app.selectbox(key="native_mode").select("Upload CSV").run()
        button(app, "Build investigation report").click().run()
        assert not app.exception
        fields = app.dataframe[0].value
        port = fields[fields["Source field"].str.endswith("RemotePort")].iloc[0]
        assert (
            port["Original value (JSON)"] == '"00443"'
            and port["Original type"] == "str"
        )
        source = app.session_state["native_result"]["response"]["report"][
            "observation"
        ]["original_source_text"]
        assert source.encode("utf-8") == raw
        uploaded[0] = Upload(b"\xff")
        app.run()
        assert not app.exception and len(calls) == 1
        assert not app.get("download_button")
        assert button(app, "Build investigation report").disabled
        assert INVALID_INPUT in [item.value for item in app.error]


@pytest.mark.parametrize(
    "failure", [requests.Timeout("PRIVATE"), requests.ConnectionError("PRIVATE")]
)
def test_investigation_timeout_disconnect_are_single_attempt_and_refresh_does_not_retry(
    monkeypatch, failure
):
    calls = transport(monkeypatch, failure=failure)
    app = open_investigation(monkeypatch)
    button(app, "Load synthetic network example").click().run()
    button(app, "Build investigation report").click().run()
    app.run()
    assert not app.exception and len(calls) == 1
    assert not app.get("download_button")
    assert app.error and all("PRIVATE" not in item.value for item in app.error)


@pytest.mark.parametrize(
    "kind", ["redirect", "duplicate", "size", "forged_export", "nonloopback"]
)
def test_investigation_client_retains_transport_and_export_guards(monkeypatch, kind):
    status, base = 200, "http://127.0.0.1:8245"
    body = build_response(request()).model_dump_json().encode()
    if kind == "redirect":
        status = 307
    elif kind == "duplicate":
        body = b'{"report":{},"report":{}}'
    elif kind == "size":
        monkeypatch.setattr(client, "MAX_RESPONSE_BYTES", 100)
    elif kind == "forged_export":
        value = json.loads(body)
        value["markdown_export"] += "APPROVED"
        body = json.dumps(value).encode()
    else:
        base = "http://192.0.2.10:8245"
    calls = transport(monkeypatch, body=body, status=status)
    result, error = client.post_native_investigation(base, request())
    assert result is None and error
    assert len(calls) == (0 if kind == "nonloopback" else 1)
    if kind != "nonloopback":
        assert error == WITHHELD
