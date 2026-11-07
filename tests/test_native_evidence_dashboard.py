"""Loopback client plus actual API -> Streamlit render/download, without GUI."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from app import native_evidence_api as api
from app.native_evidence_config import ENABLE_FLAG, ENDPOINT, INVALID_INPUT, WITHHELD
from app.native_observations import NativeObservationRequest, build_response
from dashboard import native_evidence_client as client
from dashboard.native_evidence import PAGE, navigation_groups
from dashboard.navigation import PAGE_GROUPS

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "dashboard/streamlit_app.py"
SAMPLE = ROOT / "sample_data/native_evidence/network_observation.json"


def request():
    return NativeObservationRequest(
        source_text=SAMPLE.read_text(encoding="utf-8"), source_format="microsoft_json"
    )


class StreamResponse:
    def __init__(self, content=b"", status=200):
        self.content, self.status_code = content, status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def iter_content(self, chunk_size):
        for offset in range(0, len(self.content), chunk_size):
            yield self.content[offset : offset + chunk_size]


def transport(monkeypatch, *, body=None, status=200, forward=None, failure=None):
    calls, sessions = [], []

    class Session:
        trust_env = True

        def __enter__(self):
            sessions.append(self)
            return self

        def __exit__(self, *args):
            return None

        def post(self, url, **kwargs):
            calls.append((url, kwargs))
            assert self.trust_env is False
            assert kwargs["allow_redirects"] is False
            assert kwargs["stream"] is True
            assert kwargs["timeout"] == (3, 15)
            if failure:
                raise failure
            if forward is not None:
                response = forward.post(ENDPOINT, json=kwargs["json"])
                return StreamResponse(response.content, response.status_code)
            return StreamResponse(body or b"", status)

    monkeypatch.setattr(requests, "Session", Session)
    return calls, sessions


def open_native(monkeypatch):
    monkeypatch.setenv(ENABLE_FLAG, "1")
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:8000")
    return AppTest.from_file(ENTRY, default_timeout=15).run().switch_page(PAGE[0]).run()


def button(app, label):
    return next(item for item in app.button if item.label == label)


def test_navigation_copy_default_off_and_original_groups_unchanged(monkeypatch):
    import streamlit as st

    original = deepcopy(PAGE_GROUPS)
    assert navigation_groups(PAGE_GROUPS, enabled=False) == original
    enabled = navigation_groups(PAGE_GROUPS, enabled=True)
    assert enabled["Experimental"] == (PAGE,)
    assert PAGE_GROUPS == original
    monkeypatch.delenv(ENABLE_FLAG, raising=False)
    observed = []
    original_navigation = st.navigation

    def capture(pages, **kwargs):
        observed.append(tuple(pages))
        return original_navigation(pages, **kwargs)

    monkeypatch.setattr(st, "navigation", capture)
    app = AppTest.from_file(ENTRY, default_timeout=15).run()
    assert not app.exception
    assert observed and "Experimental" not in observed[0]


def test_actual_client_api_page_render_exports_and_no_automatic_resubmit(monkeypatch):
    monkeypatch.setenv(ENABLE_FLAG, "1")
    with TestClient(api.create_app()) as backend:
        calls, _ = transport(monkeypatch, forward=backend)
        app = open_native(monkeypatch)
        assert not app.exception
        assert button(app, "Build native observations").disabled
        button(app, "Load synthetic network example").click().run()
        assert not calls
        button(app, "Build native observations").click().run()
        assert not app.exception, app.exception
        assert len(calls) == 1
        assert len(app.get("download_button")) == 2
        texts = "\n".join(item.value for item in app.text)
        assert "Comparator: not executed (0 calls)" in texts
        assert "Relationship: unassessable" in texts
        assert "Currentness: submitted snapshot only" in texts
        assert "Original byte SHA-256" in texts
        fields = app.dataframe[0].value
        assert (
            fields.loc[
                fields["Source field"].str.endswith("RemotePort"),
                "Original value (JSON)",
            ].iloc[0]
            == "443"
        )
        assert (
            fields.loc[
                fields["Source field"].str.endswith("RemotePort"), "Original type"
            ].iloc[0]
            == "int"
        )
        app.run()
        assert not app.exception and len(calls) == 1
        assert len(app.get("download_button")) == 2
        app.number_input(key="native_row").set_value(1).run()
        assert not app.get("download_button") and len(calls) == 1
        button(app, "Build native observations").click().run()
        assert not app.exception and len(calls) == 2
        assert len(app.get("download_button")) == 2
        app.text_area(key="native_source_text").set_value('{"bad":1}').run()
        assert not app.get("download_button") and len(calls) == 2


@pytest.mark.parametrize(
    "base",
    [
        "https://example.invalid",
        "http://127.0.0.1.example.invalid",
        "http://localhost:8000",
        "http://192.0.2.3",
        "file:///tmp/api",
        "http://user:secret@127.0.0.1:8000",
        "http://127.0.0.1:8000/elsewhere",
        "http://127.0.0.1:8000?redirect=evil",
    ],
)
def test_client_rejects_nonloopback_or_credential_urls_before_upload(monkeypatch, base):
    calls, _ = transport(monkeypatch)
    result, error = client.post_native_observations(base, request())
    assert result is None and error == client.LOCAL_ONLY
    assert not calls


@pytest.mark.parametrize("base", ["http://127.0.0.1:8000", "https://[::1]:8000/"])
def test_local_client_validates_source_bound_response_and_disables_environment_proxy(
    monkeypatch, base
):
    body = build_response(request()).model_dump_json().encode()
    calls, sessions = transport(monkeypatch, body=body)
    envelope, error = client.post_native_observations(base, request())
    assert error is None and envelope.report.source_status == "supplied_unverified"
    assert len(calls) == len(sessions) == 1
    assert sessions[0].trust_env is False


@pytest.mark.parametrize(
    "status,error",
    [(307, WITHHELD), (404, client.UNAVAILABLE), (422, INVALID_INPUT), (500, WITHHELD)],
)
def test_client_never_follows_redirects_or_displays_response_bodies(
    monkeypatch, status, error
):
    calls, _ = transport(monkeypatch, body=b"SECRET_SERVER_ERROR", status=status)
    result, actual = client.post_native_observations("http://127.0.0.1:8000", request())
    assert result is None and actual == error
    assert len(calls) == 1 and "SECRET" not in actual


@pytest.mark.parametrize(
    "kind", ["size", "duplicate", "encoding", "source", "export", "approval"]
)
def test_client_rejects_oversized_ambiguous_or_forged_response(monkeypatch, kind):
    data = build_response(request()).model_dump(mode="json")
    if kind == "size":
        body = b"x" * 4097
        monkeypatch.setattr(client, "MAX_RESPONSE_BYTES", 4096)
    elif kind == "duplicate":
        body = b'{"report":{},"report":{}}'
    elif kind == "encoding":
        body = b"\xff"
    else:
        if kind == "source":
            data["report"]["source_sha256"] = "0" * 64
        elif kind == "export":
            data["markdown_export"] += "FORGED APPROVAL"
        else:
            data["report"]["approval_granted"] = True
        body = json.dumps(data).encode()
    calls, _ = transport(monkeypatch, body=body)
    result, error = client.post_native_observations("http://127.0.0.1:8000", request())
    assert result is None and error == WITHHELD and len(calls) == 1


@pytest.mark.parametrize(
    "failure", [requests.Timeout("PRIVATE"), requests.ConnectionError("PRIVATE")]
)
def test_client_disconnect_and_timeout_have_one_attempt_no_raw_error(
    monkeypatch, failure
):
    calls, _ = transport(monkeypatch, failure=failure)
    result, error = client.post_native_observations("http://127.0.0.1:8000", request())
    assert result is None and "PRIVATE" not in error and len(calls) == 1


def test_saved_report_mutation_is_withheld_on_rerender_without_resubmit(monkeypatch):
    monkeypatch.setenv(ENABLE_FLAG, "1")
    with TestClient(api.create_app()) as backend:
        calls, _ = transport(monkeypatch, forward=backend)
        app = open_native(monkeypatch)
        button(app, "Load synthetic network example").click().run()
        button(app, "Build native observations").click().run()
        assert len(app.get("download_button")) == 2
        saved = app.session_state["native_result"]
        saved["response"]["report"]["approval_granted"] = True
        app.session_state["native_result"] = saved
        app.run()
        assert not app.exception and len(calls) == 1
        assert not app.get("download_button")
        assert WITHHELD in [item.value for item in app.error]


def test_csv_upload_actual_route_and_invalid_replacement_clear_downloads(monkeypatch):
    import streamlit as st

    class Upload:
        def __init__(self, raw):
            self.raw, self.size = raw, len(raw)

        def getvalue(self):
            return self.raw

    uploaded = [Upload(b"Timestamp,RemotePort\r\n2026-11-07T14:00:00Z,00443\r\n")]
    monkeypatch.setattr(st, "file_uploader", lambda *args, **kwargs: uploaded[0])
    monkeypatch.setenv(ENABLE_FLAG, "1")
    with TestClient(api.create_app()) as backend:
        calls, _ = transport(monkeypatch, forward=backend)
        app = open_native(monkeypatch)
        app.selectbox(key="native_mode").select("Upload CSV").run()
        button(app, "Build native observations").click().run()
        assert not app.exception and len(calls) == 1
        assert len(app.get("download_button")) == 2
        fields = app.dataframe[0].value
        port = fields[fields["Source field"].str.endswith("RemotePort")].iloc[0]
        assert (
            port["Original value (JSON)"] == '"00443"'
            and port["Original type"] == "str"
        )
        uploaded[0] = Upload(b"\xff")
        app.run()
        assert not app.exception and not app.get("download_button")
        assert len(calls) == 1 and button(app, "Build native observations").disabled
        assert INVALID_INPUT in [item.value for item in app.error]


def test_oversized_upload_is_rejected_before_getvalue(monkeypatch):
    import streamlit as st

    class Upload:
        size = 64_001

        def getvalue(self):
            pytest.fail("oversized upload must be rejected before copying its contents")

    monkeypatch.setattr(st, "file_uploader", lambda *args, **kwargs: Upload())
    calls, _ = transport(monkeypatch)
    app = open_native(monkeypatch)
    app.selectbox(key="native_mode").select("Upload JSON").run()
    assert not app.exception and not calls
    assert button(app, "Build native observations").disabled
    assert INVALID_INPUT in [item.value for item in app.error]


def test_old_gateway_guidance_and_source_errors_remove_previous_exports(monkeypatch):
    calls, _ = transport(monkeypatch, status=404, body=b"PRIVATE")
    app = open_native(monkeypatch)
    button(app, "Load synthetic network example").click().run()
    button(app, "Build native observations").click().run()
    assert not app.exception and len(calls) == 1
    assert not app.get("download_button")
    assert client.UNAVAILABLE in [item.value for item in app.error]


def test_missing_synthetic_sample_error_survives_input_invalidation(
    monkeypatch, tmp_path
):
    from dashboard import native_evidence

    monkeypatch.setattr(native_evidence, "SAMPLE", tmp_path / "absent.json")
    calls, _ = transport(monkeypatch)
    app = open_native(monkeypatch)
    button(app, "Load synthetic network example").click().run()
    assert not app.exception and not calls
    assert "The synthetic example is unavailable." in [item.value for item in app.error]
