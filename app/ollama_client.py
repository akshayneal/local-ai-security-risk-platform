import json
import os
import re
import time
from typing import Any
from urllib.parse import urlsplit

import requests
from dotenv import load_dotenv
from ollama import Client
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_fixed

from app.inference_context import EvidenceBudgetError, complete_context_required
from app.model_metrics import configured_context, finish_attempt, start_attempt
from app.prompts import SYSTEM_PROMPT

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_TEMPERATURE = 0.1

client = Client(host=OLLAMA_HOST)


def _clean_model_json(text: str) -> str:
    """
    Removes common formatting problems if the model wraps JSON in markdown.
    """
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").strip()

    if cleaned.endswith("```"):
        cleaned = cleaned.removesuffix("```").strip()

    return cleaned


def _complete_context_chat(
    messages: list[dict], response_schema: dict, options: dict
) -> dict:
    """Use the documented local API because SDK 0.6.2 lacks these request fields.

    No environment proxy, redirect, remote host, fallback, raw error or partial
    content is permitted in this mode. The SDK/default path remains unchanged.
    """
    parsed = urlsplit(OLLAMA_HOST)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise EvidenceBudgetError("runtime_unsupported")
    host = OLLAMA_HOST.rstrip("/")
    try:
        with requests.Session() as session:
            session.trust_env = False
            version_response = session.get(
                host + "/api/version", timeout=10, allow_redirects=False
            )
            version = (
                version_response.json().get("version")
                if version_response.status_code == 200
                else None
            )
            if (
                not isinstance(version, str)
                or not re.fullmatch(r"\d+\.\d+\.\d+", version)
                or tuple(map(int, version.split("."))) < (0, 40, 12)
            ):
                raise EvidenceBudgetError("runtime_unsupported")
            response = session.post(
                host + "/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "format": response_schema,
                    "options": options,
                    "stream": False,
                    "truncate": False,
                    "shift": False,
                },
                timeout=300,
                allow_redirects=False,
            )
            if response.status_code in (400, 413):
                # This is a rejected complete-context request, not proof of a
                # particular error body. Never echo or classify arbitrary text.
                raise EvidenceBudgetError("request_rejected")
            if response.status_code != 200:
                raise RuntimeError("Local complete-context request failed")
            data = response.json()
            if not isinstance(data, dict) or "error" in data:
                raise RuntimeError("Local complete-context response failed")
            return data
    except EvidenceBudgetError:
        raise
    except (requests.RequestException, ValueError, TypeError, AttributeError) as exc:
        raise RuntimeError("Local complete-context request failed") from exc


@retry(
    stop=stop_after_attempt(2),
    wait=wait_fixed(1),
    retry=retry_if_not_exception_type(EvidenceBudgetError),
)
def call_model_json(
    user_prompt: str, response_schema: dict[str, Any]
) -> dict[str, Any]:
    """
    Sends a prompt to the local Ollama model and asks for JSON matching a schema.
    """
    record = start_attempt(user_prompt, response_schema)
    started = time.perf_counter()
    options = {"temperature": OLLAMA_TEMPERATURE}
    if configured_context() is not None:
        options["num_ctx"] = configured_context()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    try:
        if complete_context_required():
            response = _complete_context_chat(messages, response_schema, options)
        else:
            response = client.chat(
                model=OLLAMA_MODEL,
                messages=messages,
                format=response_schema,
                options=options,
            )
    except EvidenceBudgetError as exc:
        if record is not None:
            record.update(
                context_status=exc.code,
                elapsed_ms=(time.perf_counter() - started) * 1000,
            )
        raise
    finish_attempt(record, response, started)
    if complete_context_required() and (
        response.get("done_reason") == "length" or response.get("done") is not True
    ):
        code = (
            "generation_limit"
            if response.get("done_reason") == "length"
            else "incomplete_generation"
        )
        if record is not None:
            record["context_status"] = code
        raise EvidenceBudgetError(code)

    content = response["message"]["content"]
    cleaned = _clean_model_json(content)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        if record is not None:
            record["status"] = "invalid_json"
        raise ValueError("Model returned invalid JSON") from exc
