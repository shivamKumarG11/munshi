"""One OpenAI-compatible client (LiteLLM or TokenRouter), traced by neatlogs.

Roles, not model names, are used in the agent: "cheap", "vision", "strong".
Escalation (cheap first, strong only when checks fail) is decided by callers.
"""

import base64
import json
import os
import time
from pathlib import Path

import openai
from openai import OpenAI

from munshi import tracing
from munshi.config import settings

_client = None
usage: dict[str, dict[str, int]] = {}   # model -> {"calls", "prompt", "completion"} for this process


def client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.llm_api_key:
            raise RuntimeError(f"No API key for LLM provider '{settings.llm_provider}' in .env")
        _client = tracing.wrap(OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url))
    return _client


def model_for(role: str) -> str:
    return {"cheap": settings.model_cheap, "vision": settings.model_vision, "strong": settings.model_strong}[role]


_fallback = None
FALLBACK_DEFAULTS = {"LITELLM": {"cheap": "claude-haiku", "vision": "nova-lite", "strong": "claude-sonnet-4.6"}}


def _fallback_provider():
    """The other configured provider (TokenRouter <-> LiteLLM), if its key is set: (client, {role: model})."""
    global _fallback
    if _fallback is None:
        other = "LITELLM" if settings.llm_provider == "tokenrouter" else "TOKENROUTER"
        key = os.environ.get(f"{other}_API_KEY", "").strip()
        base = os.environ.get(f"{other}_BASE_URL", "").strip() or (
            "https://litellm.vision.aivar.app/v1" if other == "LITELLM" else "")
        models = {role: os.environ.get(f"{other}_MODEL_{role.upper()}", "").strip()
                  or FALLBACK_DEFAULTS.get(other, {}).get(role, "") for role in ("cheap", "vision", "strong")}
        _fallback = (tracing.wrap(OpenAI(api_key=key, base_url=base)), models) if key and base and all(models.values()) else False
    return _fallback or None


RETRYABLE = (openai.APIConnectionError, openai.APITimeoutError, openai.RateLimitError, openai.InternalServerError,
             openai.NotFoundError, openai.BadRequestError, openai.PermissionDeniedError)


def _complete(role: str, messages: list[dict]):
    """Primary provider (one retry), then the fallback provider. Returns (reply, model actually used)."""
    attempts = [(client(), model_for(role)), (client(), model_for(role))]
    fb = _fallback_provider()
    if fb:
        attempts.append((fb[0], fb[1][role]))
    if role != "strong":  # last resort: the strong models (they also read images)
        attempts.append((client(), model_for("strong")))
        if fb:
            attempts.append((fb[0], fb[1]["strong"]))
    last = None
    for i, (c, model) in enumerate(attempts):
        try:
            return c.chat.completions.create(model=model, messages=messages), model
        except RETRYABLE as e:  # provider/model unavailable: try again, then switch provider
            last = e
            if isinstance(e, openai.BadRequestError) and "deprecated" not in str(e) and "channel" not in str(e):
                raise
            time.sleep(1.5 * (i + 1))
    raise last


def ask_json(role: str, system: str, user: str, images: list[Path] | None = None) -> dict:
    """Ask for a JSON object. Raises ValueError if the reply isn't valid JSON."""
    content: list[dict] | str = user
    if images:
        content = [{"type": "text", "text": user}] + [_image_part(p) for p in images]
    reply, used = _complete(role, [{"role": "system", "content": system}, {"role": "user", "content": content}])
    u = usage.setdefault(used, {"calls": 0, "prompt": 0, "completion": 0})
    u["calls"] += 1
    if reply.usage:
        u["prompt"] += reply.usage.prompt_tokens or 0
        u["completion"] += reply.usage.completion_tokens or 0
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


def ask_text(role: str, system: str, user: str) -> str:
    """Plain-text answer (used by the Ask Munshi chat)."""
    reply, used = _complete(role, [{"role": "system", "content": system}, {"role": "user", "content": user}])
    u = usage.setdefault(used, {"calls": 0, "prompt": 0, "completion": 0})
    u["calls"] += 1
    if reply.usage:
        u["prompt"] += reply.usage.prompt_tokens or 0
        u["completion"] += reply.usage.completion_tokens or 0
    return (reply.choices[0].message.content or "").strip()
