import pytest

from cloakbridge.detection.dictionary import DictionaryEntry, DictionaryMatcher
from cloakbridge.detection.local_ai import DisabledLocalAI
from cloakbridge.detection.pipeline import DetectionPipeline
from cloakbridge.detection.regex_detector import RegexDetector
from cloakbridge.domain.entities import EntityType
from cloakbridge.gateway.leakage_guard import LeakageDetected, LeakageGuard


def make_guard() -> LeakageGuard:
    pipeline = DetectionPipeline(
        RegexDetector(),
        DictionaryMatcher([DictionaryEntry("华东三期项目", EntityType.PROJECT, "project", "confirmed")]),
        DisabledLocalAI(),
    )
    return LeakageGuard(pipeline)


def test_leakage_guard_blocks_raw_sensitive_dictionary_term():
    with pytest.raises(LeakageDetected) as error:
        make_guard().assert_safe("请处理华东三期项目资料")

    assert "华东三期项目" in str(error.value)


def test_leakage_guard_allows_sanitized_tokens():
    make_guard().assert_safe("请处理<PROJECT_001>资料和<IP_001>。")


def test_leakage_guard_blocks_raw_ip_even_without_dictionary():
    with pytest.raises(LeakageDetected) as error:
        make_guard().assert_safe("请处理服务器10.18.2.4")

    assert "10.18.2.4" in str(error.value)
