from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from charset_normalizer import from_bytes

from cloakbridge.domain.entities import Finding
from cloakbridge.domain.tokens import TokenMap


@dataclass(frozen=True)
class SanitizedText:
    text: str
    encoding: str
    newline: str


class TxtProcessor:
    def sanitize(self, path: Path, findings: list[Finding], token_map: TokenMap) -> SanitizedText:
        raw = path.read_bytes()
        match = from_bytes(raw).best()
        encoding = match.encoding if match else "utf-8"
        text = raw.decode(encoding)
        newline = "\r\n" if "\r\n" in text else "\n"
        sanitized = self.replace_text(text, findings, token_map)
        return SanitizedText(text=sanitized, encoding=encoding, newline=newline)

    def replace_text(self, text: str, findings: list[Finding], token_map: TokenMap) -> str:
        result = text
        for finding in sorted(findings, key=lambda item: item.start, reverse=True):
            token = token_map.token_for(finding)
            result = result[: finding.start] + token + result[finding.end :]
        return result
