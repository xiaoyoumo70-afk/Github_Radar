"""LLM client abstraction — supports local, OpenAI, DeepSeek, and custom providers."""

from __future__ import annotations

import json
import requests

from github_radar.models.config import Settings, PROVIDER_PRESETS


class LLMClient:
    """Multi-provider chat completions client (OpenAI-compatible API)."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: int = 120,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> str:
        """Call the LLM and return the message text."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            body["response_format"] = response_format

        resp = requests.post(
            f"{self.base_url}/chat/completions",
            json=body,
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        msg = data["choices"][0]["message"]
        return msg.get("content") or msg.get("reasoning_content", "")


def build_client(
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    settings: Settings | None = None,
) -> LLMClient:
    """Factory — creates a properly configured LLMClient from settings.

    Resolution order:
    1. Explicit arguments (Python-side override)
    2. Settings object (from .env / env vars)
    3. Preset defaults
    """
    if settings is None:
        settings = Settings()

    resolved_base_url = base_url or settings.effective_base_url
    resolved_model = model or settings.llm_model
    resolved_key = api_key or settings.llm_api_key

    return LLMClient(
        base_url=resolved_base_url,
        model=resolved_model,
        api_key=resolved_key,
    )


def get_provider_info(provider: str) -> dict:
    """Return metadata for a given provider key."""
    return PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS["local"])
