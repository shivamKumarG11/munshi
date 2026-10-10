"""Settings loaded from the environment (.env in the project root)."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    llm_api_key: str
    llm_base_url: str
    model_cheap: str
    model_vision: str
    model_strong: str
    neatlogs_api_key: str
    crustdata_api_key: str
    sec_user_agent: str
    companies_house_api_key: str
    dodo_api_key: str
    dodo_webhook_secret: str


def load() -> Settings:
    provider = _env("LLM_PROVIDER", "litellm").lower()
    prefix = "TOKENROUTER" if provider == "tokenrouter" else "LITELLM"
    return Settings(
        llm_provider=provider,
        llm_api_key=_env(f"{prefix}_API_KEY"),
        llm_base_url=_env(f"{prefix}_BASE_URL", "https://litellm.vision.aivar.app/v1"),
        model_cheap=_env(f"{prefix}_MODEL_CHEAP", "claude-haiku"),
        model_vision=_env(f"{prefix}_MODEL_VISION", "nova-lite"),
        model_strong=_env(f"{prefix}_MODEL_STRONG", "claude-sonnet-4.6"),
        neatlogs_api_key=_env("NEATLOGS_API_KEY"),
        crustdata_api_key=_env("CRUSTDATA_API_KEY"),
        sec_user_agent=_env("SEC_USER_AGENT"),
        companies_house_api_key=_env("COMPANIES_HOUSE_API_KEY"),
        dodo_api_key=_env("DODO_API_KEY"),
        dodo_webhook_secret=_env("DODO_WEBHOOK_SECRET"),
    )


settings = load()
