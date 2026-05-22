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


def test_structured_project_aliases_share_entity_group_but_restore_surface_form():
    token_map = TokenMap(replacement_style="structured")
    token_map.register_alias_group(
        EntityType.PROJECT,
        canonical="西调工程",
        aliases=["西调工程", "西调2025工程", "西调搬迁", "2025资源补强"],
    )

    first = token_map.token_for(Finding("西调工程", EntityType.PROJECT, 0, 4, "dictionary", 1.0))
    second = token_map.token_for(Finding("西调搬迁", EntityType.PROJECT, 10, 14, "dictionary", 1.0))

    assert first == "[[PRJ:001#001]]"
    assert second == "[[PRJ:001#003]]"
    assert token_map.restore(f"{first}服务器，{second}清单") == "西调工程服务器，西调搬迁清单"
    assert token_map.restore("[[PRJ:001]]整体风险") == "西调工程整体风险"


def test_structured_ip_tokens_preserve_prefix_and_range_relationships():
    token_map = TokenMap(replacement_style="structured")

    ip = token_map.token_for(Finding("10.18.2.18", EntityType.IP_ADDRESS, 0, 10, "regex", 1.0))
    same_prefix_ip = token_map.token_for(Finding("10.18.2.90", EntityType.IP_ADDRESS, 11, 21, "regex", 1.0))
    other_prefix_ip = token_map.token_for(Finding("10.18.3.4", EntityType.IP_ADDRESS, 22, 31, "regex", 1.0))
    prefix = token_map.token_for(Finding("10.18.2", EntityType.IP_PREFIX, 32, 39, "regex", 1.0))
    ip_range = token_map.token_for(Finding("10.18.2.18-90", EntityType.IP_RANGE, 40, 53, "regex", 1.0))

    assert ip == "[[IP:A.B.C.018]]"
    assert same_prefix_ip == "[[IP:A.B.C.090]]"
    assert other_prefix_ip == "[[IP:A.B.D.004]]"
    assert prefix == "[[IP_PREFIX:A.B.C.*]]"
    assert ip_range == "[[IP_RANGE:A.B.C.018-090]]"
    assert token_map.restore(f"{prefix} 包含 {ip_range} 和 {same_prefix_ip}") == (
        "10.18.2 包含 10.18.2.18-90 和 10.18.2.90"
    )
