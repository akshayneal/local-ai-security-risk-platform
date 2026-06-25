import json
import os
from typing import Any

from dotenv import load_dotenv
from ollama import Client
from tenacity import retry, stop_after_attempt, wait_fixed

from app.prompts import SYSTEM_PROMPT

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

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


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
def call_model_json(user_prompt: str, response_schema: dict[str, Any]) -> dict[str, Any]:
    """
    Sends a prompt to the local Ollama model and asks for JSON matching a schema.
    """
    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        format=response_schema,
        options={
            "temperature": 0.1,
        },
    )

    content = response["message"]["content"]
    cleaned = _clean_model_json(content)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned invalid JSON: {cleaned[:500]}") from exc