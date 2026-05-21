"""Application configuration via environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration loaded from env / .env file."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # GitHub
    github_token: str | None = None

    # LLM
    llm_base_url: str = "http://localhost:8000/v1"
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
