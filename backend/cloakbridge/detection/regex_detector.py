from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from cloakbridge.domain.entities import EntityType, Finding


@dataclass(frozen=True)
class RegexRule:
    entity_type: EntityType
    pattern: re.Pattern[str]


class RegexDetector:
    def __init__(self) -> None:
        self.rules = [
            RegexRule(
                EntityType.URL,
                re.compile(r"https?://[A-Za-z0-9._~:/?#\[\]@$&'()*+,;=%-]+"),
            ),
            RegexRule(
                EntityType.EMAIL,
                re.compile(
                    r"(?<![A-Za-z0-9_.+-])"
                    r"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
                    r"(?![A-Za-z0-9_.-])"
                ),
            ),
            RegexRule(
                EntityType.IP_RANGE,
                re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}-\d{1,3}(?![\d.-])"),
            ),
            RegexRule(
                EntityType.IP_PREFIX,
                re.compile(r"(?<![\d.])(?:\d{1,3}\.){2}\d{1,3}(?=开头|段|网段|范围)"),
            ),
            RegexRule(
                EntityType.IP_ADDRESS,
                re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?(?![\d./])"),
            ),
            RegexRule(EntityType.MOBILE_PHONE, re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
            RegexRule(
                EntityType.PROJECT_CODE,
                re.compile(r"(?<![A-Z0-9-])[A-Z]{2,8}-\d{4}-\d{2,6}(?![A-Z0-9-])"),
            ),
            RegexRule(
                EntityType.PROJECT,
                re.compile(
                    r"(?<![A-Za-z0-9])"
                    r"\d{3,8}[\u4e00-\u9fff]{0,12}?"
                    r"(?:备用域名|项目|工程|系统|平台|应用|业务)"
                    r"(?![A-Za-z0-9])"
                ),
            ),
            RegexRule(
                EntityType.PROJECT,
                re.compile(r"(?<![A-Za-z0-9])\d{3,8}(?=APP|App|app)"),
            ),
            RegexRule(
                EntityType.CONTRACT,
                re.compile(r"\b(?:HT|合同|CONTRACT)[-_]?[A-Za-z0-9-]{4,}\b"),
            ),
            RegexRule(
                EntityType.DOMAIN,
                re.compile(r"(?<![A-Za-z0-9-])\d{3,8}(?:-[A-Za-z0-9]+)?\.cn"),
            ),
            RegexRule(
                EntityType.DOMAIN,
                re.compile(r"(?<![@/A-Za-z0-9_.-])(?:[A-Za-z0-9-]+\.)+(?:com|cn|net|org|io|local)\b"),
            ),
        ]

    def detect(self, text: str) -> list[Finding]:
        findings: list[Finding] = []
        for rule in self.rules:
            findings.extend(self._find_rule(text, rule))
        return self._dedupe_overlaps(findings)

    def _find_rule(self, text: str, rule: RegexRule) -> Iterable[Finding]:
        for match in rule.pattern.finditer(text):
            if rule.entity_type is EntityType.IP_ADDRESS and not self._valid_ip(match.group()):
                continue
            if rule.entity_type is EntityType.IP_PREFIX and not self._valid_ip_prefix(match.group()):
                continue
            if rule.entity_type is EntityType.IP_RANGE and not self._valid_ip_range(match.group()):
                continue
            yield Finding(
                text=match.group(),
                entity_type=rule.entity_type,
                start=match.start(),
                end=match.end(),
                source="regex",
                confidence=1.0,
            )

    def _valid_ip(self, value: str) -> bool:
        ip, separator, cidr = value.partition("/")
        if separator and not (cidr.isdigit() and 0 <= int(cidr) <= 32):
            return False
        return all(0 <= int(part) <= 255 for part in ip.split("."))

    def _valid_ip_prefix(self, value: str) -> bool:
        parts = value.split(".")
        return len(parts) == 3 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

    def _valid_ip_range(self, value: str) -> bool:
        start_ip, separator, end_host = value.partition("-")
        if not separator or not end_host.isdigit() or not self._valid_ip(start_ip):
            return False
        start = int(start_ip.split(".")[-1])
        end = int(end_host)
        return 0 <= end <= 255 and start <= end

    def _dedupe_overlaps(self, findings: list[Finding]) -> list[Finding]:
        ordered = sorted(findings, key=lambda item: (item.start, -(item.end - item.start)))
        accepted: list[Finding] = []
        for finding in ordered:
            if any(finding.overlaps(existing) for existing in accepted):
                continue
            accepted.append(finding)
        return accepted
