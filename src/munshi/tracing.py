"""neatlogs setup. Every agent step goes through these helpers so tracing is uniform.

Without NEATLOGS_API_KEY the helpers become no-ops, so the agent still runs locally.
"""

import contextlib
import functools

from munshi.config import settings

_enabled = False

try:
    import neatlogs
except ImportError:  # pragma: no cover
    neatlogs = None


def init(agent_version: str) -> bool:
    """Start tracing for one process. Returns True when traces are being sent."""
    global _enabled
    if neatlogs is None or not settings.neatlogs_api_key:
        return False
    neatlogs.init(
        api_key=settings.neatlogs_api_key,
        workflow_name="munshi-close",
        tags=[f"agent_version={agent_version}", f"llm={settings.llm_provider}"],
    )
    _enabled = True
    return True


def wrap(client):
    """Wrap an OpenAI-compatible client so every LLM call is traced."""
    return neatlogs.wrap(client) if _enabled else client


def span(kind: str, name: str | None = None, **attrs):
    """Decorator for our own steps (WORKFLOW / AGENT / TOOL)."""

    def decorator(fn):
        if not _enabled:
            return fn
        options = {"kind": kind, **attrs}
        if name:
            options["tool_name" if kind == "TOOL" else "name"] = name
        traced = neatlogs.span(**options)(fn)

        @functools.wraps(fn)
        def call(*args, **kwargs):
            return traced(*args, **kwargs)

        return call

    return decorator


def run(name: str, session_id: str, end_user_id: str):
    """Root trace for one close run: one session per business-month, business = end user."""
    if not _enabled:
        return contextlib.nullcontext()
    return neatlogs.trace(name, session_id=session_id, end_user_id=end_user_id)


def shutdown() -> None:
    if _enabled:
        neatlogs.flush()
        neatlogs.shutdown()
