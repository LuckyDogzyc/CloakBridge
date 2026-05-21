from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from cloakbridge.gateway.leakage_guard import LeakageGuard


SUPPORTED_PROVIDERS = {
    "openai",
    "anthropic",
    "gemini",
    "deepseek",
    "qwen",
    "glm",
    "minimax",
    "openrouter",
    "custom-openai",
    "custom-anthropic",
}


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    model: str
    base_url: str | None = None
    api_key: str | None = None

    def __post_init__(self) -> None:
        if self.provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {self.provider}")


@dataclass(frozen=True)
class ProviderResponse:
    sanitized_text: str
    attachments: list[str]


class ModelProvider(Protocol):
    def complete(self, sanitized_prompt: str, leakage_guard: LeakageGuard) -> ProviderResponse:
        """Send sanitized content only and return sanitized model output."""


class EchoProvider:
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    def complete(self, sanitized_prompt: str, leakage_guard: LeakageGuard) -> ProviderResponse:
        leakage_guard.assert_safe(sanitized_prompt)
        return ProviderResponse(sanitized_text=sanitized_prompt, attachments=[])
