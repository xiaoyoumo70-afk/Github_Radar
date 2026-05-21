"""LLM client abstraction — pluggable backend (local qwen, OpenAI-compatible)."""

from __future__ import annotations

import json
import requests


class LLMClient:
    """Minimal OpenAI-compatible chat completions client."""

    def __init__(self, base_url: str, model: str, timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

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
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        msg = data["choices"][0]["message"]
        return msg.get("content") or msg.get("reasoning_content", "")


def build_client(base_url: str = "http://localhost:5000/v1", model: str = "qwen3.6-27b") -> LLMClient:
    """Factory for the default LLM client."""
    return LLMClient(base_url=base_url, model=model)
