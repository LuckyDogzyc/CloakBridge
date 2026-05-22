from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel

from cloakbridge.detection.dictionary import DictionaryEntry, DictionaryMatcher
from cloakbridge.detection.local_ai import HeuristicChineseLocalAI
from cloakbridge.detection.pipeline import DetectionPipeline
from cloakbridge.detection.regex_detector import RegexDetector
from cloakbridge.documents.txt_processor import TxtProcessor
from cloakbridge.domain.entities import EntityType, Finding
from cloakbridge.domain.tokens import TokenMap
from cloakbridge.gateway.token_prompt import build_token_handling_prompt

router = APIRouter(prefix="/api")


class DictionaryEntryIn(BaseModel):
    text: str
    entity_type: EntityType
    scope: str = "project"


class AnalyzeTextRequest(BaseModel):
    text: str
    dictionary: list[DictionaryEntryIn] = []


class FindingIn(BaseModel):
    text: str
    entity_type: EntityType
    start: int
    end: int
    source: str
    confidence: float


class SanitizeTextRequest(BaseModel):
    text: str
    findings: list[FindingIn]


class RestoreTextRequest(BaseModel):
    sanitized_text: str
    token_map: dict[str, str]


@router.post("/analyze-text")
def analyze_text(request: AnalyzeTextRequest) -> dict[str, object]:
    entries = [
        DictionaryEntry(item.text, item.entity_type, item.scope, "confirmed")
        for item in request.dictionary
    ]
    pipeline = DetectionPipeline(RegexDetector(), DictionaryMatcher(entries), HeuristicChineseLocalAI())
    findings = pipeline.detect(request.text)
    return {"findings": [asdict(finding) for finding in findings]}


@router.post("/sanitize-text")
def sanitize_text(request: SanitizeTextRequest) -> dict[str, object]:
    token_map = TokenMap(replacement_style="structured")
    findings = [
        Finding(item.text, item.entity_type, item.start, item.end, item.source, item.confidence)
        for item in request.findings
    ]
    sanitized_text = TxtProcessor().replace_text(request.text, findings, token_map)
    return {
        "sanitized_text": sanitized_text,
        "token_map": token_map.token_to_original,
        "token_prompt": build_token_handling_prompt(token_map.token_to_original),
    }


@router.post("/restore-text")
def restore_text(request: RestoreTextRequest) -> dict[str, str]:
    restored = _restore_once(request.sanitized_text, request.token_map)
    return {"restored_text": restored}


def _restore_once(text: str, token_map: dict[str, str]) -> str:
    import re

    if not token_map:
        return text
    pattern = re.compile("|".join(re.escape(token) for token in sorted(token_map, key=len, reverse=True)))
    return pattern.sub(lambda match: token_map[match.group(0)], text)
