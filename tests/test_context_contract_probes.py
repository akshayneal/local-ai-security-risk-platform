import json

from evals.context_contract import runner


def test_contract_probe_does_not_persist_content_or_errors(monkeypatch):
    monkeypatch.setattr(runner, "runtime_snapshot", dict)

    class Response:
        ok = True
        status_code = 200

        def json(self):
            return {
                "message": {"content": "PRIVATE GENERATED TEXT"},
                "eval_count": 32,
                "prompt_eval_count": 2200,
                "done_reason": "length",
                "extra": "SECRET",
            }

    class Session:
        def post(self, url, **kwargs):
            assert url.startswith("http://localhost:")
            assert kwargs["json"]["truncate"] is False
            assert kwargs["json"]["shift"] is False
            return Response()

    plan = json.loads((runner.SUITE / "plan.json").read_bytes())
    record = runner.probe(plan["probes"][0], Session())
    assert record["status"] == "response"
    assert record["usage"]["eval_count"] == 32
    assert "PRIVATE" not in json.dumps(record) and "SECRET" not in json.dumps(record)


def test_local_host_boundary(monkeypatch):
    import pytest

    for host in (
        "https://example.invalid",
        "http://user:password@localhost:11434",
        "http://localhost:11434/path",
    ):
        monkeypatch.setattr(runner, "OLLAMA_HOST", host)
        with pytest.raises(ValueError, match="plain local"):
            runner.local_url()
