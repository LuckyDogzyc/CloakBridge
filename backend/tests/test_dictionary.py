from cloakbridge.detection.dictionary import DictionaryEntry, DictionaryMatcher
from cloakbridge.domain.entities import EntityType


def test_dictionary_matcher_finds_project_and_company():
    matcher = DictionaryMatcher(
        [
            DictionaryEntry("华东三期项目", EntityType.PROJECT, "project", "confirmed"),
            DictionaryEntry("上海明远科技有限公司", EntityType.COMPANY, "global", "confirmed"),
        ]
    )

    findings = matcher.detect("华东三期项目由上海明远科技有限公司负责。")
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.PROJECT, "华东三期项目") in found
    assert (EntityType.COMPANY, "上海明远科技有限公司") in found


def test_dictionary_matcher_ignores_pending_and_ignored_entries():
    matcher = DictionaryMatcher(
        [
            DictionaryEntry("待确认项目", EntityType.PROJECT, "project", "pending"),
            DictionaryEntry("普通词", EntityType.CUSTOM, "global", "ignored"),
        ]
    )

    assert matcher.detect("待确认项目和普通词都不应自动脱敏。") == []


def test_dictionary_matcher_prefers_longest_overlapping_match_even_if_it_starts_later():
    matcher = DictionaryMatcher(
        [
            DictionaryEntry("abcde", EntityType.CUSTOM, "global", "confirmed"),
            DictionaryEntry("bcdefgh", EntityType.PROJECT, "project", "confirmed"),
        ]
    )

    findings = matcher.detect("abcdefgh")

    assert [(finding.entity_type, finding.text) for finding in findings] == [
        (EntityType.PROJECT, "bcdefgh")
    ]


def test_dictionary_matcher_handles_duplicate_entries_once_per_span():
    matcher = DictionaryMatcher(
        [
            DictionaryEntry("华东三期项目", EntityType.PROJECT, "project", "confirmed"),
            DictionaryEntry("华东三期项目", EntityType.PROJECT, "project", "confirmed"),
        ]
    )

    findings = matcher.detect("华东三期项目")

    assert [(finding.entity_type, finding.text) for finding in findings] == [
        (EntityType.PROJECT, "华东三期项目")
    ]


def test_dictionary_matcher_empty_entries_returns_no_findings():
    assert DictionaryMatcher([]).detect("华东三期项目") == []
