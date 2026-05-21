from cloakbridge.detection.dictionary import DictionaryEntry, DictionaryMatcher
from cloakbridge.detection.local_ai import DisabledLocalAI, HeuristicChineseLocalAI
from cloakbridge.detection.pipeline import DetectionPipeline
from cloakbridge.detection.regex_detector import RegexDetector
from cloakbridge.domain.entities import EntityType


def test_pipeline_combines_regex_dictionary_and_dedupes():
    pipeline = DetectionPipeline(
        regex_detector=RegexDetector(),
        dictionary_matcher=DictionaryMatcher(
            [DictionaryEntry("华东三期项目", EntityType.PROJECT, "project", "confirmed")]
        ),
        local_ai=DisabledLocalAI(),
    )

    findings = pipeline.detect("华东三期项目服务器为10.18.2.4。")
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.PROJECT, "华东三期项目") in found
    assert (EntityType.IP_ADDRESS, "10.18.2.4") in found


def test_pipeline_uses_lightweight_local_chinese_heuristics():
    pipeline = DetectionPipeline(
        regex_detector=RegexDetector(),
        dictionary_matcher=DictionaryMatcher([]),
        local_ai=HeuristicChineseLocalAI(),
    )

    findings = pipeline.detect("上海明远科技有限公司负责华东三期项目。")
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.COMPANY, "上海明远科技有限公司") in found
    assert (EntityType.PROJECT, "华东三期项目") in found
