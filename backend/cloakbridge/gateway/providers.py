from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

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


class ChatCompletionsProvider:
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    def complete(self, sanitized_prompt: str, leakage_guard: LeakageGuard) -> ProviderResponse:
        leakage_guard.assert_safe(sanitized_prompt)
        if not self.config.base_url:
            raise ValueError("Base URL is required")
        if not self.config.api_key:
            raise ValueError("API key is required")

        response = httpx.post(
            _chat_completions_url(self.config.base_url),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.config.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你处理的是已经脱敏的内容。必须保留所有 [[...]] 标记，"
                            "不要改写、翻译、删除、拆分或重排这些标记。"
                        ),
                    },
                    {"role": "user", "content": sanitized_prompt},
                ],
                "temperature": 0.2,
            },
            timeout=60,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            detail = response.text[:500]
            raise RuntimeError(f"Provider returned {response.status_code}: {detail}") from error
        payload = response.json()
        return ProviderResponse(sanitized_text=_extract_chat_text(payload), attachments=[])


def complete_with_provider(
    config: ProviderConfig,
    sanitized_prompt: str,
    leakage_guard: LeakageGuard,
) -> ProviderResponse:
    if config.provider == "echo":
        return EchoProvider(config).complete(sanitized_prompt, leakage_guard)
    return ChatCompletionsProvider(config).complete(sanitized_prompt, leakage_guard)


def _chat_completions_url(base_url: str) -> str:
    trimmed = base_url.rstrip("/")
    if trimmed.endswith("/chat/completions"):
        return trimmed
    return f"{trimmed}/chat/completions"


def _extract_chat_text(payload: dict[str, object]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Provider response does not contain choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("Provider response choice is invalid")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("Provider response message is invalid")
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        if parts:
            return "".join(parts)
    raise ValueError("Provider response content is empty")
