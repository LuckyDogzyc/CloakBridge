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
