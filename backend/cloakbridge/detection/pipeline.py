from __future__ import annotations

from dataclasses import dataclass

from cloakbridge.detection.dictionary import DictionaryMatcher
from cloakbridge.detection.local_ai import LocalAI
from cloakbridge.detection.regex_detector import RegexDetector
from cloakbridge.domain.entities import Finding


@dataclass
class DetectionPipeline:
    regex_detector: RegexDetector
    dictionary_matcher: DictionaryMatcher
    local_ai: LocalAI

    def detect(self, text: str) -> list[Finding]:
        findings = [
            *self.regex_detector.detect(text),
            *self.dictionary_matcher.detect(text),
            *self.local_ai.detect(text),
        ]
        return self._dedupe(findings)

    def _dedupe(self, findings: list[Finding]) -> list[Finding]:
        ordered = sorted(
            findings,
            key=lambda item: (item.start, -(item.end - item.start), -item.confidence),
        )
        accepted: list[Finding] = []
        for finding in ordered:
            if any(finding.overlaps(existing) for existing in accepted):
                continue
            accepted.append(finding)
        return accepted
