import pytest

from cloakbridge.detection.dictionary import DictionaryEntry, DictionaryMatcher
from cloakbridge.detection.local_ai import DisabledLocalAI
from cloakbridge.detection.pipeline import DetectionPipeline
from cloakbridge.detection.regex_detector import RegexDetector
from cloakbridge.domain.entities import EntityType
from cloakbridge.gateway.leakage_guard import LeakageDetected, LeakageGuard
from cloakbridge.gateway.providers import EchoProvider, ProviderConfig


def guard() -> LeakageGuard:
    return LeakageGuard(
        DetectionPipeline(
            RegexDetector(),
            DictionaryMatcher([DictionaryEntry("华东三期项目", EntityType.PROJECT, "project", "confirmed")]),
            DisabledLocalAI(),
        )
    )


def test_echo_provider_returns_sanitized_response():
    provider = EchoProvider(ProviderConfig(provider="custom-openai", model="test", base_url="http://local"))

    response = provider.complete("请总结<PROJECT_001>", guard())

    assert response.sanitized_text == "请总结<PROJECT_001>"


def test_provider_blocks_raw_sensitive_prompt():
    provider = EchoProvider(ProviderConfig(provider="glm", model="glm-test", base_url="http://local"))

    with pytest.raises(LeakageDetected):
        provider.complete("请总结华东三期项目", guard())


def test_provider_config_supports_domestic_and_custom_models():
    providers = {
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

    for provider in providers:
        assert ProviderConfig(provider=provider, model="model").provider == provider
