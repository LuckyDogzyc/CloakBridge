from __future__ import annotations

from dataclasses import asdict
import os
from pathlib import Path

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
from cloakbridge.storage.sqlite_store import SQLiteStore

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


class AliasGroupIn(BaseModel):
    entity_type: EntityType
    canonical: str
    aliases: list[str]


class AliasGroupCreateRequest(AliasGroupIn):
    scope: str = "project"


class SanitizeTextRequest(BaseModel):
    text: str
    findings: list[FindingIn]
    alias_groups: list[AliasGroupIn] = []


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


@router.post("/alias-groups")
def create_alias_group(request: AliasGroupCreateRequest) -> dict[str, object]:
    store = _local_store()
    return store.create_alias_group(
        entity_type=request.entity_type.value,
        canonical=request.canonical,
        aliases=request.aliases,
        scope=request.scope,
    )


@router.get("/alias-groups")
def list_alias_groups(scope: str | None = None) -> dict[str, object]:
    store = _local_store()
    return {"alias_groups": store.list_alias_groups(scope)}


@router.post("/sanitize-text")
def sanitize_text(request: SanitizeTextRequest) -> dict[str, object]:
    token_map = TokenMap(replacement_style="structured")
    for group in request.alias_groups:
        token_map.register_alias_group(group.entity_type, group.canonical, group.aliases)
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


def _local_store() -> SQLiteStore:
    data_dir = Path(os.environ.get("CLOAKBRIDGE_DATA_DIR", ".local-data")).resolve()
    store = SQLiteStore(data_dir / "cloakbridge.sqlite")
    store.initialize()
    return store
