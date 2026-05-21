from __future__ import annotations

from typing import Protocol

from cloakbridge.domain.entities import EntityType, Finding


class LocalAI(Protocol):
    def detect(self, text: str) -> list[Finding]:
        """Return locally detected findings without sending text over the network."""


class DisabledLocalAI:
    def detect(self, text: str) -> list[Finding]:
        return []


class HeuristicChineseLocalAI:
    _BOUNDARIES = set("，。；;：:、 \n\t")
    _CONNECTORS = ("负责", "属于", "关于", "检查", "处理", "上传", "中的", "以及", "和", "由", "与", "为")

    def detect(self, text: str) -> list[Finding]:
        findings: list[Finding] = []
        findings.extend(self._find_suffix_entity(text, "有限公司", 16, EntityType.COMPANY))
        findings.extend(self._find_suffix_entity(text, "项目", 12, EntityType.PROJECT))
        return findings

    def _find_suffix_entity(
        self,
        text: str,
        suffix: str,
        max_prefix_chars: int,
        entity_type: EntityType,
    ) -> list[Finding]:
        findings: list[Finding] = []
        search_from = 0
        while True:
            suffix_start = text.find(suffix, search_from)
            if suffix_start == -1:
                return findings
            start = self._scan_start(text, suffix_start, max_prefix_chars)
            end = suffix_start + len(suffix)
            start = self._trim_connectors(text, start, end)
            value = text[start:end]
            if len(value) > len(suffix):
                findings.append(Finding(value, entity_type, start, end, "local_ai:heuristic", 0.72))
            search_from = end

    def _scan_start(self, text: str, suffix_start: int, max_prefix_chars: int) -> int:
        start = suffix_start
        while start > 0 and suffix_start - start < max_prefix_chars:
            if text[start - 1] in self._BOUNDARIES:
                break
            start -= 1
        return start

    def _trim_connectors(self, text: str, start: int, end: int) -> int:
        value = text[start:end]
        best_offset = -1
        best_connector = ""
        for connector in self._CONNECTORS:
            offset = value.rfind(connector)
            if offset > best_offset:
                best_offset = offset
                best_connector = connector
        if best_offset == -1:
            return start
        return start + best_offset + len(best_connector)
