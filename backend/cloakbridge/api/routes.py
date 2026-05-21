from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel

from cloakbridge.detection.dictionary import DictionaryEntry, DictionaryMatcher
from cloakbridge.detection.local_ai import DisabledLocalAI
from cloakbridge.detection.pipeline import DetectionPipeline
from cloakbridge.detection.regex_detector import RegexDetector
from cloakbridge.documents.txt_processor import TxtProcessor
from cloakbridge.domain.entities import EntityType, Finding
from cloakbridge.domain.tokens import TokenMap

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
    pipeline = DetectionPipeline(RegexDetector(), DictionaryMatcher(entries), DisabledLocalAI())
    findings = pipeline.detect(request.text)
    return {"findings": [asdict(finding) for finding in findings]}


@router.post("/sanitize-text")
def sanitize_text(request: SanitizeTextRequest) -> dict[str, object]:
    token_map = TokenMap()
    findings = [
        Finding(item.text, item.entity_type, item.start, item.end, item.source, item.confidence)
        for item in request.findings
    ]
    sanitized_text = TxtProcessor().replace_text(request.text, findings, token_map)
    return {"sanitized_text": sanitized_text, "token_map": token_map.token_to_original}


@router.post("/restore-text")
def restore_text(request: RestoreTextRequest) -> dict[str, str]:
    restored = request.sanitized_text
    for token, original in sorted(request.token_map.items(), key=lambda item: -len(item[0])):
        restored = restored.replace(token, original)
    return {"restored_text": restored}
