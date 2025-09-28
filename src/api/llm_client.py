"""Unified LLM client backed by the Grok API.

OpenAI / LangChain support is temporarily suspended. The implementation is
structured to allow future provider switching, but only the Grok backend is
active. All configuration values are supplied via `src.settings` and
ultimately via environment variables (.env).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

import requests

import src.settings as settings
from src.utils.logging_config import get_logger


class LLMProvider(str, Enum):
    """Enumerate supported providers for future extensibility."""

    GROK = "grok"
    OPENAI = "openai"  # intentionally disabled for now


@dataclass
class GrokLLMConfig:
    """Settings required to interact with the Grok API."""

    api_key: str
    api_base: str = "https://api.x.ai/v1"
    model: str = "grok-beta"
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    timeout: int = 30

    @classmethod
    def from_settings(cls) -> "GrokLLMConfig":
        if not settings.GROK_API_KEY:
            raise RuntimeError("GROK_API_KEY is required to use the Grok backend")
        return cls(
            api_key=settings.GROK_API_KEY,
            api_base=settings.GROK_API_BASE,
            model=settings.GROK_DEFAULT_MODEL,
        )


@dataclass
class LLMResponse:
    """Normalized response returned by LLMClient."""

    content: str
    raw: Dict[str, Any]


class GrokAPIError(RuntimeError):
    """Raised when the Grok API returns an error or unexpected payload."""


class BaseLLMBackend:
    """Simple protocol for LLM backends."""

    provider: LLMProvider

    def generate(self, system_prompt: str, user_content: str) -> LLMResponse:  # pragma: no cover - interface
        raise NotImplementedError


class GrokLLMBackend(BaseLLMBackend):
    provider = LLMProvider.GROK

    def __init__(self, config: GrokLLMConfig) -> None:
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

    @property
    def _endpoint(self) -> str:
        return f"{self.config.api_base.rstrip('/')}/chat/completions"

    def generate(self, system_prompt: str, user_content: str) -> LLMResponse:
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": self.config.temperature,
        }
        if self.config.max_tokens is not None:
            payload["max_tokens"] = self.config.max_tokens

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        self.logger.info(
            "Calling Grok API",
            extra={"endpoint": self._endpoint, "model": self.config.model},
        )
        try:
            response = requests.post(
                self._endpoint,
                headers=headers,
                json=payload,
                timeout=self.config.timeout,
            )
        except requests.RequestException as exc:  # pragma: no cover - network failure
            raise GrokAPIError("Failed to reach Grok API") from exc

        if response.status_code >= 400:
            raise GrokAPIError(
                f"Grok API error {response.status_code}: {response.text[:200]}"
            )

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GrokAPIError("Unexpected response format from Grok API") from exc

        self.logger.debug("Grok API response received", extra={"length": len(content)})
        return LLMResponse(content=content, raw=data)


class LLMClient:
    """Facade for instantiating and using provider-specific LLM backends."""

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.GROK,
        *,
        grok_config: Optional[GrokLLMConfig] = None,
    ) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.provider = provider

        if provider == LLMProvider.GROK:
            self.backend = GrokLLMBackend(grok_config or GrokLLMConfig.from_settings())
        elif provider == LLMProvider.OPENAI:
            raise NotImplementedError(
                "OpenAI support is currently disabled. Enable once provider policy allows it."
            )
        else:  # pragma: no cover - defensive
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def generate(self, system_prompt: str, user_content: str) -> LLMResponse:
        self.logger.info("Dispatching prompt to provider", extra={"provider": self.provider})
        return self.backend.generate(system_prompt, user_content)


__all__ = [
    "LLMProvider",
    "LLMClient",
    "GrokLLMBackend",
    "GrokLLMConfig",
    "LLMResponse",
    "GrokAPIError",
]
