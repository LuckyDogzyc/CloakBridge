from cloakbridge.domain.entities import EntityType, Finding
from cloakbridge.domain.tokens import TokenMap


def test_token_map_reuses_token_for_same_entity_text():
    token_map = TokenMap()
    finding = Finding(
        text="华东三期项目",
        entity_type=EntityType.PROJECT,
        start=0,
        end=6,
        source="user",
        confidence=1.0,
    )

    first = token_map.token_for(finding)
    second = token_map.token_for(finding)

    assert first == "<PROJECT_001>"
    assert second == "<PROJECT_001>"
    assert token_map.restore("请总结<PROJECT_001>风险") == "请总结华东三期项目风险"


def test_token_map_allocates_by_entity_family():
    token_map = TokenMap()

    project = Finding("华东三期项目", EntityType.PROJECT, 0, 6, "user", 1.0)
    ip = Finding("10.18.2.4", EntityType.IP_ADDRESS, 7, 16, "regex", 1.0)

    assert token_map.token_for(project) == "<PROJECT_001>"
    assert token_map.token_for(ip) == "<IP_001>"


def test_restore_does_not_recursively_replace_original_that_looks_like_token():
    token_map = TokenMap()
    project = Finding("<IP_001>", EntityType.PROJECT, 0, 8, "user", 1.0)
    ip = Finding("10.0.0.1", EntityType.IP_ADDRESS, 9, 17, "regex", 1.0)

    assert token_map.token_for(project) == "<PROJECT_001>"
    assert token_map.token_for(ip) == "<IP_001>"

    assert token_map.restore("<PROJECT_001>") == "<IP_001>"


def test_phone_family_is_shared_between_mobile_and_landline():
    token_map = TokenMap()
    mobile = Finding("13800138000", EntityType.MOBILE_PHONE, 0, 11, "regex", 1.0)
    landline = Finding("010-88886666", EntityType.LANDLINE, 12, 24, "regex", 1.0)

    assert token_map.token_for(mobile) == "<PHONE_001>"
    assert token_map.token_for(landline) == "<PHONE_002>"


def test_finding_overlap_boundaries():
    left = Finding("abc", EntityType.CUSTOM, 0, 3, "test", 1.0)
    touching = Finding("def", EntityType.CUSTOM, 3, 6, "test", 1.0)
    overlapping = Finding("bc", EntityType.CUSTOM, 1, 3, "test", 1.0)

    assert not left.overlaps(touching)
    assert left.overlaps(overlapping)
