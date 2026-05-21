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
                re.compile(r"https?://[^\s，。；;：:！!？?、）)\]\}]+"),
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
                EntityType.IP_ADDRESS,
                re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?(?![\d./])"),
            ),
            RegexRule(EntityType.MOBILE_PHONE, re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
            RegexRule(
                EntityType.PROJECT_CODE,
                re.compile(r"(?<![A-Z0-9-])[A-Z]{2,8}-\d{4}-\d{2,6}(?![A-Z0-9-])"),
            ),
            RegexRule(
                EntityType.CONTRACT,
                re.compile(r"\b(?:HT|合同|CONTRACT)[-_]?[A-Za-z0-9-]{4,}\b"),
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

    def _dedupe_overlaps(self, findings: list[Finding]) -> list[Finding]:
        ordered = sorted(findings, key=lambda item: (item.start, -(item.end - item.start)))
        accepted: list[Finding] = []
        for finding in ordered:
            if any(finding.overlaps(existing) for existing in accepted):
                continue
            accepted.append(finding)
        return accepted
