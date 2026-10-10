"""One OpenAI-compatible client (LiteLLM or TokenRouter), traced by neatlogs.

Roles, not model names, are used in the agent: "cheap", "vision", "strong".
Escalation (cheap first, strong only when checks fail) is decided by callers.
"""

import base64
import json
from pathlib import Path

from openai import OpenAI

from munshi import tracing
from munshi.config import settings

_client = None


def client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.llm_api_key:
            raise RuntimeError(f"No API key for LLM provider '{settings.llm_provider}' in .env")
        _client = tracing.wrap(OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url))
    return _client


def model_for(role: str) -> str:
    return {"cheap": settings.model_cheap, "vision": settings.model_vision, "strong": settings.model_strong}[role]


def ask_json(role: str, system: str, user: str, images: list[Path] | None = None) -> dict:
    """Ask for a JSON object. Raises ValueError if the reply isn't valid JSON."""
    content: list[dict] | str = user
    if images:
        content = [{"type": "text", "text": user}] + [_image_part(p) for p in images]
    reply = client().chat.completions.create(
        model=model_for(role),
        messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
    )
    return _parse_json(reply.choices[0].message.content or "")


def _image_part(path: Path) -> dict:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}}


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError(f"No JSON object in model reply: {text[:200]}")
    return json.loads(text[start : end + 1])
