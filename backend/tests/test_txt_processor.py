from pathlib import Path

from cloakbridge.documents.txt_processor import TxtProcessor
from cloakbridge.domain.entities import EntityType, Finding
from cloakbridge.domain.tokens import TokenMap


def test_txt_processor_sanitizes_and_restores_text(tmp_path: Path):
    source = tmp_path / "input.txt"
    source.write_text("华东三期项目服务器10.18.2.4", encoding="utf-8", newline="\n")
    findings = [
        Finding("华东三期项目", EntityType.PROJECT, 0, 6, "user", 1.0),
        Finding("10.18.2.4", EntityType.IP_ADDRESS, 9, 18, "regex", 1.0),
    ]
    token_map = TokenMap()

    sanitized = TxtProcessor().sanitize(source, findings, token_map)

    assert sanitized.text == "<PROJECT_001>服务器<IP_001>"
    assert token_map.restore(sanitized.text) == "华东三期项目服务器10.18.2.4"


def test_txt_processor_reuses_tokens_across_files_when_token_map_is_shared(tmp_path: Path):
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("华东三期项目需要检查", encoding="utf-8")
    second.write_text("请复核华东三期项目", encoding="utf-8")
    token_map = TokenMap()

    first_sanitized = TxtProcessor().sanitize(
        first,
        [Finding("华东三期项目", EntityType.PROJECT, 0, 6, "user", 1.0)],
        token_map,
    )
    second_sanitized = TxtProcessor().sanitize(
        second,
        [Finding("华东三期项目", EntityType.PROJECT, 3, 9, "user", 1.0)],
        token_map,
    )

    assert first_sanitized.text == "<PROJECT_001>需要检查"
    assert second_sanitized.text == "请复核<PROJECT_001>"
