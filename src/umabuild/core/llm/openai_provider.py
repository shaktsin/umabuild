from __future__ import annotations

import os
from typing import Any

import requests
from rich.console import Console

from .base import LLMProvider

console = Console()


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider.")

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        payload.update(kwargs)
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
        except requests.RequestException as exc:
            raise RuntimeError(f"Network error calling OpenAI API: {exc}") from exc
        if resp.status_code == 401:
            raise RuntimeError("OpenAI API authentication failed. Check OPENAI_API_KEY.")
        if resp.status_code == 429:
            raise RuntimeError("OpenAI API rate limit hit. Try again later.")
        if resp.status_code >= 400:
            raise RuntimeError(f"OpenAI API error {resp.status_code}: {resp.text}")
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Invalid response format from OpenAI API.") from exc
