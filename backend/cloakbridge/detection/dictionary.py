from __future__ import annotations

from dataclasses import dataclass

import ahocorasick

from cloakbridge.domain.entities import EntityType, Finding


@dataclass(frozen=True, slots=True)
class DictionaryEntry:
    text: str
    entity_type: EntityType
    scope: str
    status: str


class DictionaryMatcher:
    def __init__(self, entries: list[DictionaryEntry]) -> None:
        self.entries = [entry for entry in entries if entry.status == "confirmed" and entry.text]
        self.automaton = ahocorasick.Automaton()
        for index, entry in enumerate(self.entries):
            self.automaton.add_word(entry.text, (index, entry))
        self.automaton.make_automaton()

    def detect(self, text: str) -> list[Finding]:
        if not self.entries:
            return []

        findings: list[Finding] = []
        for end_index, (_, entry) in self.automaton.iter(text):
            start = end_index - len(entry.text) + 1
            findings.append(
                Finding(
                    text=entry.text,
                    entity_type=entry.entity_type,
                    start=start,
                    end=end_index + 1,
                    source=f"dictionary:{entry.scope}",
                    confidence=1.0,
                )
            )
        return self._prefer_longest(findings)

    def _prefer_longest(self, findings: list[Finding]) -> list[Finding]:
        ordered = sorted(findings, key=lambda item: (item.start, -(item.end - item.start)))
        accepted: list[Finding] = []
        for finding in ordered:
            if any(finding.overlaps(existing) for existing in accepted):
                continue
            accepted.append(finding)
        return accepted
