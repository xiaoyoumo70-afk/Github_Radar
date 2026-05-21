"""Application configuration via environment variables."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings

Provider = Literal["local", "openai", "deepseek", "custom"]

PROVIDER_PRESETS: dict[str, dict] = {
    "local": {
        "base_url": "http://localhost:8000/v1",
        "needs_key": False,
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "needs_key": True,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "needs_key": True,
    },
    "custom": {
        "base_url": "http://localhost:8000/v1",
        "needs_key": True,
    },
}


class Settings(BaseSettings):
    """Central configuration loaded from env / .env file."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # GitHub
    github_token: str | None = None

    # LLM — Provider
    llm_provider: Provider = "local"
    llm_api_key: str | None = None

    # LLM — Connection (used for custom provider, or to override presets)
    llm_base_url: str = ""
    llm_model: str = "qwen3.7"

    # Obsidian
    obsidian_vault: str | None = None

    # Storage
    artifacts_dir: Path = Path("artifacts")

    # Content limits
    max_readme_chars: int = 30_000
    max_file_chars: int = 20_000
    context_warning_chars: int = 90_000  # ~36k tokens approximate
    snapshot_ctx_chars: int = 12_000
    structure_ctx_chars: int = 16_000
    synthesis_ctx_chars: int = 24_000

    @property
    def effective_base_url(self) -> str:
        """Resolve the actual base URL: preset defaults → override by LLM_BASE_URL."""
        preset = PROVIDER_PRESETS.get(self.llm_provider, PROVIDER_PRESETS["local"])
        if self.llm_base_url:
            return self.llm_base_url
        return preset["base_url"]

    @property
    def needs_api_key(self) -> bool:
        """Whether this provider requires an API key."""
        preset = PROVIDER_PRESETS.get(self.llm_provider, PROVIDER_PRESETS["local"])
        return preset["needs_key"]
