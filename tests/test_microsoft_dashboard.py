import json
from io import BytesIO

import pytest
from test_dashboard import button, fake_post, open_page

from dashboard.sample_loader import load_microsoft_samples


def microsoft_page():
    app = open_page()
    app.selectbox(key="soc_input_profile").select("Microsoft Security telemetry").run()
    return app


def test_microsoft_preview_submit_export_and_profile_invalidation(monkeypatch):
    calls = fake_post(monkeypatch)
    app = microsoft_page()
    assert not app.exception
    assert button(app, "Analyze Microsoft telemetry").disabled
    button(app, "Load Microsoft sample").click().run()
    assert "Normalization preview" in [w.value for w in app.subheader]
    assert not button(app, "Analyze Microsoft telemetry").disabled
    button(app, "Analyze Microsoft telemetry").click().run()
    assert not app.exception and len(calls) == 1
    assert calls[0][0].endswith("/ui/analyze/soc-alert")
    assert json.loads(calls[0][1]["raw_log"]) == next(
        iter(load_microsoft_samples().values())
    )
    assert len(app.get("download_button")) == 2
    app.text_area(key="ms_json").set_value('{"bad":1}').run()
    assert not app.get("download_button")
    assert button(app, "Analyze Microsoft telemetry").disabled
    assert app.error
    app.selectbox(key="soc_input_profile").select(
        "Generic / normalized SOC input"
    ).run()
    assert not app.exception
    assert any(w.label == "Analyze SOC alert" for w in app.button)


@pytest.mark.parametrize(
    "data", ["{}", " " * 80001, "[" * 500], ids=["shape", "size", "depth"]
)
def test_microsoft_invalid_input_never_submits(monkeypatch, data):
    calls = fake_post(monkeypatch)
    app = microsoft_page()
    app.text_area(key="ms_json").set_value(data).run()
    assert not app.exception and app.error
    assert button(app, "Analyze Microsoft telemetry").disabled
    assert not calls


def test_microsoft_upload_modes_and_csv_explicit_selection():
    app = microsoft_page()
    mode = next(w for w in app.selectbox if w.label == "Telemetry input")
    mode.select("Upload CSV").run()
    table = next(w for w in app.selectbox if w.label == "CSV source table")
    assert "DeviceLogonEvents" in table.options
    assert len(app.get("file_uploader")) == 1
    assert button(app, "Analyze Microsoft telemetry").disabled


def test_microsoft_input_change_and_profile_change_clear_results(monkeypatch):
    fake_post(monkeypatch)
    app = microsoft_page()
    button(app, "Load Microsoft sample").click().run()
    button(app, "Analyze Microsoft telemetry").click().run()
    assert app.get("download_button")
    app.selectbox(key="soc_input_profile").select(
        "Generic / normalized SOC input"
    ).run()
    app.selectbox(key="soc_input_profile").select("Microsoft Security telemetry").run()
    assert not app.get("download_button")


@pytest.mark.parametrize("csv", [False, True])
def test_uploaded_json_and_csv_normalize_and_submit(monkeypatch, csv):
    import streamlit as st

    calls = fake_post(monkeypatch)
    bundle = next(iter(load_microsoft_samples().values()))
    data = (
        b'AlertId,Title\r\nSYN-UPLOAD,"Synthetic CSV alert"\r\n'
        if csv
        else json.dumps(bundle).encode()
    )
    monkeypatch.setattr(st, "file_uploader", lambda *a, **kw: BytesIO(data))
    app = microsoft_page()
    mode = next(w for w in app.selectbox if w.label == "Telemetry input")
    mode.select("Upload CSV" if csv else "Upload JSON").run()
    assert not app.exception
    assert not button(app, "Analyze Microsoft telemetry").disabled
    button(app, "Analyze Microsoft telemetry").click().run()
    assert not app.exception and len(calls) == 1
    supplied = json.loads(calls[0][1]["raw_log"])
    assert (
        supplied["tables"]["AlertInfo"][0]["AlertId"] == "SYN-UPLOAD"
        if csv
        else supplied == bundle
    )
    assert len(app.get("download_button")) == 2
