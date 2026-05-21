# CloakBridge MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local WebUI MVP that sanitizes `.txt`, `.docx`, and `.xlsx`, lets the user review findings, blocks outbound leaks, calls external model providers with sanitized content only, and restores AI responses locally.

**Architecture:** A Python FastAPI backend owns all sensitive processing, storage, document mutation, and model gateway logic. A React/Vite WebUI talks only to `127.0.0.1`, displays findings for review, and defaults to restored model responses while keeping sanitized responses in a hidden details panel. The first implementation uses deterministic rules and dictionary matching; lightweight Chinese AI is represented by a pluggable interface with a disabled no-op provider so the MVP stays fast and safe.

**Tech Stack:** Python 3.11+, FastAPI, pytest, lxml, openpyxl, pyahocorasick, SQLite, React, TypeScript, Vite, Vitest.

---

## Scope

This plan implements the first working software slice from the design spec:

- Local backend bound to `127.0.0.1`.
- Public-repo-safe project structure and ignore rules.
- Rule and dictionary detection for Chinese-heavy office content.
- Tokenization and restoration.
- `.txt`, `.docx`, and `.xlsx` sanitization with style preservation tests.
- Leakage guard before outbound model calls.
- Provider adapter interface with OpenAI-compatible, Anthropic-compatible, GLM, MiniMax, DeepSeek, Qwen/Tongyi, OpenRouter, and custom endpoint config shapes.
- Basic WebUI for upload, review, sanitize, model call, and restored answer display.

This plan does not implement PDF, PPT, CAD, image OCR, LAN team mode, or heavy local LLMs.

## File Structure

Create this structure:

```text
cloakbridge/
  pyproject.toml
  README.md
  .gitignore
  .env.example
  backend/
    cloakbridge/
      __init__.py
      main.py
      config.py
      domain/
        __init__.py
        entities.py
        tokens.py
      detection/
        __init__.py
        regex_detector.py
        dictionary.py
        local_ai.py
        pipeline.py
      documents/
        __init__.py
        txt_processor.py
        docx_processor.py
        xlsx_processor.py
      gateway/
        __init__.py
        leakage_guard.py
        providers.py
      storage/
        __init__.py
        paths.py
        sqlite_store.py
        vault.py
      api/
        __init__.py
        routes.py
    tests/
      conftest.py
      fixtures.py
      test_regex_detector.py
      test_dictionary.py
      test_tokens.py
      test_txt_processor.py
      test_docx_processor.py
      test_xlsx_processor.py
      test_leakage_guard.py
      test_api_flow.py
  frontend/
    package.json
    tsconfig.json
    vite.config.ts
    index.html
    src/
      main.tsx
      App.tsx
      api/client.ts
      components/
        Shell.tsx
        FileDrop.tsx
        FindingsReview.tsx
        ProviderPanel.tsx
        ResponseViewer.tsx
      styles.css
    tests/
      App.test.tsx
```

Responsibilities:

- `domain/`: small typed data classes shared across backend modules.
- `detection/`: regex, dictionary, and local AI candidate detection.
- `documents/`: file-specific extraction and replacement while preserving formats.
- `gateway/`: outbound provider calls and final leakage guard.
- `storage/`: app data paths, SQLite metadata, and local mapping vault.
- `api/`: FastAPI routes used by the WebUI.
- `frontend/`: Codex-App-inspired local WebUI.

## Task 1: Repository Safety and Backend Bootstrap

**Files:**
- Create: `/Users/luckydog/Documents/LocalEncrypter/.gitignore`
- Create: `/Users/luckydog/Documents/LocalEncrypter/.env.example`
- Create: `/Users/luckydog/Documents/LocalEncrypter/README.md`
- Create: `/Users/luckydog/Documents/LocalEncrypter/pyproject.toml`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/__init__.py`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/config.py`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/tests/conftest.py`

- [ ] **Step 1: Write repository ignore rules**

Create `.gitignore` with:

```gitignore
.DS_Store
.env
.env.*
!.env.example
__pycache__/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.venv/
node_modules/
frontend/dist/
frontend/coverage/
data/
vault/
uploads/
outputs/
*.sqlite
*.sqlite3
*.db
*.docx
*.xlsx
*.xlsm
mapping*.json
*.key
```

- [ ] **Step 2: Add safe environment template**

Create `.env.example` with:

```dotenv
CLOAKBRIDGE_HOST=127.0.0.1
CLOAKBRIDGE_PORT=8765
CLOAKBRIDGE_DATA_DIR=.local-data
```

- [ ] **Step 3: Add minimal README**

Create `README.md` with:

```markdown
# CloakBridge

CloakBridge is a local privacy gateway for office documents and external AI.

The MVP keeps original files, dictionaries, token mappings, and logs on the local machine.
```

- [ ] **Step 4: Add project metadata**

Create `pyproject.toml` with:

```toml
[project]
name = "cloakbridge"
version = "0.1.0"
description = "Local privacy gateway for office documents and external AI."
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0",
  "pydantic>=2.8.0",
  "python-multipart>=0.0.9",
  "lxml>=5.2.0",
  "openpyxl>=3.1.5",
  "pyahocorasick>=2.1.0",
  "httpx>=0.27.0",
  "charset-normalizer>=3.3.2",
  "cryptography>=42.0.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2.0",
  "pytest-asyncio>=0.23.0",
  "ruff>=0.5.0",
]

[tool.pytest.ini_options]
pythonpath = ["backend"]
testpaths = ["backend/tests"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] **Step 5: Add app config**

Create `backend/cloakbridge/config.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    data_dir: Path

    @classmethod
    def from_env(cls) -> "Settings":
        host = os.getenv("CLOAKBRIDGE_HOST", "127.0.0.1")
        if host != "127.0.0.1":
            raise ValueError("CloakBridge MVP must bind to 127.0.0.1")
        port = int(os.getenv("CLOAKBRIDGE_PORT", "8765"))
        data_dir = Path(os.getenv("CLOAKBRIDGE_DATA_DIR", ".local-data")).resolve()
        return cls(host=host, port=port, data_dir=data_dir)
```

- [ ] **Step 6: Add pytest config fixture**

Create `backend/tests/conftest.py` with:

```python
from __future__ import annotations

import pytest


@pytest.fixture()
def sample_chinese_text() -> str:
    return "华东三期项目由上海明远科技有限公司负责，服务器IP为10.18.2.4。"
```

- [ ] **Step 7: Run bootstrap verification**

Run:

```bash
python -m pytest -q
```

Expected: `no tests ran` or `0 passed` without import errors.

- [ ] **Step 8: Commit**

```bash
git add .gitignore .env.example README.md pyproject.toml backend/cloakbridge/__init__.py backend/cloakbridge/config.py backend/tests/conftest.py
git commit -m "chore: bootstrap CloakBridge backend"
```

## Task 2: Local Storage Paths, SQLite, and Mapping Vault

**Files:**
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/storage/__init__.py`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/storage/paths.py`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/storage/sqlite_store.py`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/storage/vault.py`
- Test: `/Users/luckydog/Documents/LocalEncrypter/backend/tests/test_storage.py`

- [ ] **Step 1: Write storage tests**

Create `backend/tests/test_storage.py` with:

```python
from pathlib import Path

from cloakbridge.storage.paths import AppPaths
from cloakbridge.storage.sqlite_store import SQLiteStore
from cloakbridge.storage.vault import MappingVault


def test_app_paths_keep_data_in_local_data_dir(tmp_path: Path):
    paths = AppPaths.from_base(tmp_path)

    assert paths.data_dir == tmp_path
    assert paths.uploads_dir == tmp_path / "uploads"
    assert paths.outputs_dir == tmp_path / "outputs"
    assert paths.vault_dir == tmp_path / "vault"


def test_sqlite_store_initializes_dictionary_table(tmp_path: Path):
    store = SQLiteStore(tmp_path / "cloakbridge.sqlite")
    store.initialize()

    rows = store.connection.execute(
        "select name from sqlite_master where type='table' and name='dictionary_entries'"
    ).fetchall()

    assert rows == [("dictionary_entries",)]


def test_mapping_vault_round_trips_encrypted_token_map(tmp_path: Path):
    vault = MappingVault(tmp_path / "vault")
    vault.save("job-1", {"<PROJECT_001>": "华东三期项目"})

    raw = (tmp_path / "vault" / "job-1.bin").read_bytes()
    assert "华东三期项目".encode("utf-8") not in raw
    assert vault.load("job-1") == {"<PROJECT_001>": "华东三期项目"}
```

- [ ] **Step 2: Run failing storage tests**

Run:

```bash
python -m pytest backend/tests/test_storage.py -q
```

Expected: fail with missing storage modules.

- [ ] **Step 3: Implement local app paths**

Create `backend/cloakbridge/storage/paths.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    data_dir: Path
    uploads_dir: Path
    outputs_dir: Path
    vault_dir: Path

    @classmethod
    def from_base(cls, base: Path) -> "AppPaths":
        data_dir = base.resolve()
        return cls(
            data_dir=data_dir,
            uploads_dir=data_dir / "uploads",
            outputs_dir=data_dir / "outputs",
            vault_dir=data_dir / "vault",
        )

    def ensure(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.vault_dir.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Implement SQLite store**

Create `backend/cloakbridge/storage/sqlite_store.py` with:

```python
from __future__ import annotations

import sqlite3
from pathlib import Path


class SQLiteStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)

    def initialize(self) -> None:
        self.connection.execute(
            """
            create table if not exists dictionary_entries (
              id integer primary key autoincrement,
              text text not null,
              entity_type text not null,
              scope text not null,
              status text not null,
              source text not null default 'user',
              confidence real not null default 1.0,
              created_at text not null default current_timestamp,
              updated_at text not null default current_timestamp
            )
            """
        )
        self.connection.execute(
            "create index if not exists idx_dictionary_scope_status on dictionary_entries(scope, status)"
        )
        self.connection.commit()
```

- [ ] **Step 5: Implement encrypted mapping vault**

Create `backend/cloakbridge/storage/vault.py` with:

```python
from __future__ import annotations

import json
from pathlib import Path

from cryptography.fernet import Fernet


class MappingVault:
    def __init__(self, vault_dir: Path) -> None:
        self.vault_dir = vault_dir
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.key_path = self.vault_dir / "vault.key"
        self.fernet = Fernet(self._load_or_create_key())

    def save(self, job_id: str, token_map: dict[str, str]) -> None:
        payload = json.dumps(token_map, ensure_ascii=False).encode("utf-8")
        encrypted = self.fernet.encrypt(payload)
        (self.vault_dir / f"{job_id}.bin").write_bytes(encrypted)

    def load(self, job_id: str) -> dict[str, str]:
        encrypted = (self.vault_dir / f"{job_id}.bin").read_bytes()
        payload = self.fernet.decrypt(encrypted)
        return json.loads(payload.decode("utf-8"))

    def _load_or_create_key(self) -> bytes:
        if self.key_path.exists():
            return self.key_path.read_bytes()
        key = Fernet.generate_key()
        self.key_path.write_bytes(key)
        return key
```

- [ ] **Step 6: Run storage tests**

Run:

```bash
python -m pytest backend/tests/test_storage.py -q
```

Expected: `3 passed`.

- [ ] **Step 7: Commit**

```bash
git add backend/cloakbridge/storage backend/tests/test_storage.py pyproject.toml
git commit -m "feat: add local storage and encrypted mapping vault"
```

## Task 3: Domain Models for Findings and Token Maps

**Files:**
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/domain/__init__.py`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/domain/entities.py`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/domain/tokens.py`
- Test: `/Users/luckydog/Documents/LocalEncrypter/backend/tests/test_tokens.py`

- [ ] **Step 1: Write token tests**

Create `backend/tests/test_tokens.py` with:

```python
from cloakbridge.domain.entities import EntityType, Finding
from cloakbridge.domain.tokens import TokenMap


def test_token_map_reuses_token_for_same_entity_text():
    token_map = TokenMap()
    finding = Finding(
        text="华东三期项目",
        entity_type=EntityType.PROJECT,
        start=0,
        end=6,
        source="user",
        confidence=1.0,
    )

    first = token_map.token_for(finding)
    second = token_map.token_for(finding)

    assert first == "<PROJECT_001>"
    assert second == "<PROJECT_001>"
    assert token_map.restore("请总结<PROJECT_001>风险") == "请总结华东三期项目风险"


def test_token_map_allocates_by_entity_family():
    token_map = TokenMap()

    project = Finding("华东三期项目", EntityType.PROJECT, 0, 6, "user", 1.0)
    ip = Finding("10.18.2.4", EntityType.IP_ADDRESS, 7, 16, "regex", 1.0)

    assert token_map.token_for(project) == "<PROJECT_001>"
    assert token_map.token_for(ip) == "<IP_001>"
```

- [ ] **Step 2: Run failing token tests**

Run:

```bash
python -m pytest backend/tests/test_tokens.py -q
```

Expected: fail with `ModuleNotFoundError` or missing classes.

- [ ] **Step 3: Implement entity domain classes**

Create `backend/cloakbridge/domain/entities.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EntityType(StrEnum):
    PERSON = "PERSON"
    COMPANY = "COMPANY"
    DEPARTMENT = "DEPARTMENT"
    PROJECT = "PROJECT"
    PROJECT_CODE = "PROJECT_CODE"
    IP_ADDRESS = "IP_ADDRESS"
    HOSTNAME = "HOSTNAME"
    DOMAIN = "DOMAIN"
    URL = "URL"
    EMAIL = "EMAIL"
    MOBILE_PHONE = "MOBILE_PHONE"
    LANDLINE = "LANDLINE"
    NATIONAL_ID = "NATIONAL_ID"
    BANK_CARD = "BANK_CARD"
    CREDIT_CODE = "CREDIT_CODE"
    CONTRACT = "CONTRACT"
    DRAWING = "DRAWING"
    DEVICE = "DEVICE"
    SERVER = "SERVER"
    CUSTOM = "CUSTOM"

    @property
    def token_family(self) -> str:
        return {
            EntityType.IP_ADDRESS: "IP",
            EntityType.MOBILE_PHONE: "PHONE",
            EntityType.LANDLINE: "PHONE",
            EntityType.NATIONAL_ID: "ID",
        }.get(self, self.value)


@dataclass(frozen=True, slots=True)
class Finding:
    text: str
    entity_type: EntityType
    start: int
    end: int
    source: str
    confidence: float

    def overlaps(self, other: "Finding") -> bool:
        return self.start < other.end and other.start < self.end
```

- [ ] **Step 4: Implement token map**

Create `backend/cloakbridge/domain/tokens.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass, field

from cloakbridge.domain.entities import Finding


@dataclass
class TokenMap:
    original_to_token: dict[tuple[str, str], str] = field(default_factory=dict)
    token_to_original: dict[str, str] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)

    def token_for(self, finding: Finding) -> str:
        family = finding.entity_type.token_family
        key = (family, finding.text)
        if key in self.original_to_token:
            return self.original_to_token[key]
        next_index = self.counters.get(family, 0) + 1
        self.counters[family] = next_index
        token = f"<{family}_{next_index:03d}>"
        self.original_to_token[key] = token
        self.token_to_original[token] = finding.text
        return token

    def restore(self, text: str) -> str:
        restored = text
        for token, original in sorted(self.token_to_original.items(), key=lambda item: -len(item[0])):
            restored = restored.replace(token, original)
        return restored
```

- [ ] **Step 5: Run token tests**

Run:

```bash
python -m pytest backend/tests/test_tokens.py -q
```

Expected: `2 passed`.

- [ ] **Step 6: Commit**

```bash
git add backend/cloakbridge/domain backend/tests/test_tokens.py
git commit -m "feat: add finding and token map domain models"
```

## Task 4: Regex Detection for Structured Sensitive Content

**Files:**
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/detection/__init__.py`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/detection/regex_detector.py`
- Test: `/Users/luckydog/Documents/LocalEncrypter/backend/tests/test_regex_detector.py`

- [ ] **Step 1: Write regex detector tests**

Create `backend/tests/test_regex_detector.py` with:

```python
from cloakbridge.detection.regex_detector import RegexDetector
from cloakbridge.domain.entities import EntityType


def test_regex_detector_finds_ip_email_phone_and_project_code():
    text = "项目PRJ-2026-042联系人test@example.com，电话13800138000，内网10.18.2.4。"

    findings = RegexDetector().detect(text)
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.PROJECT_CODE, "PRJ-2026-042") in found
    assert (EntityType.EMAIL, "test@example.com") in found
    assert (EntityType.MOBILE_PHONE, "13800138000") in found
    assert (EntityType.IP_ADDRESS, "10.18.2.4") in found


def test_regex_detector_finds_url_and_domain():
    text = "访问https://secure.example.com/path，备用域名internal.example.cn。"

    findings = RegexDetector().detect(text)
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.URL, "https://secure.example.com/path") in found
    assert (EntityType.DOMAIN, "internal.example.cn") in found
```

- [ ] **Step 2: Run failing regex tests**

Run:

```bash
python -m pytest backend/tests/test_regex_detector.py -q
```

Expected: fail with missing `RegexDetector`.

- [ ] **Step 3: Implement regex detector**

Create `backend/cloakbridge/detection/regex_detector.py` with:

```python
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
            RegexRule(EntityType.URL, re.compile(r"https?://[^\s，。；;）)]+")),
            RegexRule(EntityType.EMAIL, re.compile(r"(?<![\w.-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")),
            RegexRule(EntityType.IP_ADDRESS, re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b")),
            RegexRule(EntityType.MOBILE_PHONE, re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
            RegexRule(EntityType.PROJECT_CODE, re.compile(r"\b[A-Z]{2,8}-\d{4}-\d{2,6}\b")),
            RegexRule(EntityType.CONTRACT, re.compile(r"\b(?:HT|合同|CONTRACT)[-_]?[A-Za-z0-9-]{4,}\b")),
            RegexRule(EntityType.DOMAIN, re.compile(r"(?<![@/\w.-])(?:[A-Za-z0-9-]+\.)+(?:com|cn|net|org|io|local)\b")),
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
        ip = value.split("/", 1)[0]
        return all(0 <= int(part) <= 255 for part in ip.split("."))

    def _dedupe_overlaps(self, findings: list[Finding]) -> list[Finding]:
        ordered = sorted(findings, key=lambda item: (item.start, -(item.end - item.start)))
        accepted: list[Finding] = []
        for finding in ordered:
            if any(finding.overlaps(existing) for existing in accepted):
                continue
            accepted.append(finding)
        return accepted
```

- [ ] **Step 4: Run regex tests**

Run:

```bash
python -m pytest backend/tests/test_regex_detector.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/cloakbridge/detection backend/tests/test_regex_detector.py
git commit -m "feat: detect structured sensitive entities"
```

## Task 5: Dictionary Store and High-Speed Matcher

**Files:**
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/detection/dictionary.py`
- Test: `/Users/luckydog/Documents/LocalEncrypter/backend/tests/test_dictionary.py`

- [ ] **Step 1: Write dictionary tests**

Create `backend/tests/test_dictionary.py` with:

```python
from cloakbridge.detection.dictionary import DictionaryEntry, DictionaryMatcher
from cloakbridge.domain.entities import EntityType


def test_dictionary_matcher_finds_project_and_company():
    matcher = DictionaryMatcher(
        [
            DictionaryEntry("华东三期项目", EntityType.PROJECT, "project", "confirmed"),
            DictionaryEntry("上海明远科技有限公司", EntityType.COMPANY, "global", "confirmed"),
        ]
    )

    findings = matcher.detect("华东三期项目由上海明远科技有限公司负责。")
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.PROJECT, "华东三期项目") in found
    assert (EntityType.COMPANY, "上海明远科技有限公司") in found


def test_dictionary_matcher_ignores_pending_and_ignored_entries():
    matcher = DictionaryMatcher(
        [
            DictionaryEntry("待确认项目", EntityType.PROJECT, "project", "pending"),
            DictionaryEntry("普通词", EntityType.CUSTOM, "global", "ignored"),
        ]
    )

    assert matcher.detect("待确认项目和普通词都不应自动脱敏。") == []
```

- [ ] **Step 2: Run failing dictionary tests**

Run:

```bash
python -m pytest backend/tests/test_dictionary.py -q
```

Expected: fail with missing matcher.

- [ ] **Step 3: Implement dictionary matcher**

Create `backend/cloakbridge/detection/dictionary.py` with:

```python
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
```

- [ ] **Step 4: Run dictionary tests**

Run:

```bash
python -m pytest backend/tests/test_dictionary.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/cloakbridge/detection/dictionary.py backend/tests/test_dictionary.py
git commit -m "feat: add high-speed sensitive dictionary matcher"
```

## Task 6: Detection Pipeline and Lightweight Local Chinese Heuristics

**Files:**
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/detection/local_ai.py`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/detection/pipeline.py`
- Test: `/Users/luckydog/Documents/LocalEncrypter/backend/tests/test_detection_pipeline.py`

- [ ] **Step 1: Write pipeline tests**

Create `backend/tests/test_detection_pipeline.py` with:

```python
from cloakbridge.detection.dictionary import DictionaryEntry, DictionaryMatcher
from cloakbridge.detection.local_ai import DisabledLocalAI, HeuristicChineseLocalAI
from cloakbridge.detection.pipeline import DetectionPipeline
from cloakbridge.detection.regex_detector import RegexDetector
from cloakbridge.domain.entities import EntityType


def test_pipeline_combines_regex_dictionary_and_dedupes():
    pipeline = DetectionPipeline(
        regex_detector=RegexDetector(),
        dictionary_matcher=DictionaryMatcher(
            [DictionaryEntry("华东三期项目", EntityType.PROJECT, "project", "confirmed")]
        ),
        local_ai=DisabledLocalAI(),
    )

    findings = pipeline.detect("华东三期项目服务器为10.18.2.4。")
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.PROJECT, "华东三期项目") in found
    assert (EntityType.IP_ADDRESS, "10.18.2.4") in found


def test_pipeline_uses_lightweight_local_chinese_heuristics():
    pipeline = DetectionPipeline(
        regex_detector=RegexDetector(),
        dictionary_matcher=DictionaryMatcher([]),
        local_ai=HeuristicChineseLocalAI(),
    )

    findings = pipeline.detect("上海明远科技有限公司负责华东三期项目。")
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.COMPANY, "上海明远科技有限公司") in found
    assert (EntityType.PROJECT, "华东三期项目") in found
```

- [ ] **Step 2: Run failing pipeline tests**

Run:

```bash
python -m pytest backend/tests/test_detection_pipeline.py -q
```

Expected: fail with missing pipeline modules.

- [ ] **Step 3: Implement local AI interface**

Create `backend/cloakbridge/detection/local_ai.py` with:

```python
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
    def detect(self, text: str) -> list[Finding]:
        findings: list[Finding] = []
        findings.extend(self._find_suffix_entity(text, "有限公司", 12, EntityType.COMPANY))
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
            start = suffix_start
            while start > 0 and suffix_start - start < max_prefix_chars:
                if text[start - 1] in "，。；;：:、 \n\t":
                    break
                start -= 1
            end = suffix_start + len(suffix)
            value = text[start:end]
            if len(value) > len(suffix):
                findings.append(Finding(value, entity_type, start, end, "local_ai:heuristic", 0.72))
            search_from = end
```

- [ ] **Step 4: Implement detection pipeline**

Create `backend/cloakbridge/detection/pipeline.py` with:

```python
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
```

- [ ] **Step 5: Run pipeline tests**

Run:

```bash
python -m pytest backend/tests/test_detection_pipeline.py -q
```

Expected: `2 passed`.

- [ ] **Step 6: Commit**

```bash
git add backend/cloakbridge/detection/local_ai.py backend/cloakbridge/detection/pipeline.py backend/tests/test_detection_pipeline.py
git commit -m "feat: compose local detection pipeline"
```

## Task 7: Text Sanitization and Restoration

**Files:**
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/documents/__init__.py`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/documents/txt_processor.py`
- Test: `/Users/luckydog/Documents/LocalEncrypter/backend/tests/test_txt_processor.py`

- [ ] **Step 1: Write TXT processor tests**

Create `backend/tests/test_txt_processor.py` with:

```python
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
```

- [ ] **Step 2: Run failing TXT tests**

Run:

```bash
python -m pytest backend/tests/test_txt_processor.py -q
```

Expected: fail with missing `TxtProcessor`.

- [ ] **Step 3: Implement TXT processor**

Create `backend/cloakbridge/documents/txt_processor.py` with:

```python
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
```

- [ ] **Step 4: Run TXT tests**

Run:

```bash
python -m pytest backend/tests/test_txt_processor.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/cloakbridge/documents backend/tests/test_txt_processor.py
git commit -m "feat: sanitize and restore plain text"
```

## Task 8: DOCX Sanitization with Format Preservation

**Files:**
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/tests/fixtures.py`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/documents/docx_processor.py`
- Test: `/Users/luckydog/Documents/LocalEncrypter/backend/tests/test_docx_processor.py`

- [ ] **Step 1: Write DOCX style preservation test**

Create `backend/tests/fixtures.py` with:

```python
from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def write_minimal_docx(path: Path, body_xml: str) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>{body_xml}<w:sectPr/></w:body>
</w:document>"""
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document_xml)
```

Create `backend/tests/test_docx_processor.py` with:

```python
from pathlib import Path
from zipfile import ZipFile

from cloakbridge.documents.docx_processor import DocxProcessor
from cloakbridge.domain.entities import EntityType, Finding
from cloakbridge.domain.tokens import TokenMap
from fixtures import write_minimal_docx


def test_docx_processor_replaces_text_without_removing_run_style(tmp_path: Path):
    source = tmp_path / "input.docx"
    output = tmp_path / "sanitized.docx"
    write_minimal_docx(
        source,
        """
        <w:p>
          <w:r><w:rPr><w:b/><w:color w:val="FF0000"/></w:rPr><w:t>华东</w:t></w:r>
          <w:r><w:rPr><w:b/><w:color w:val="FF0000"/></w:rPr><w:t>三期项目</w:t></w:r>
        </w:p>
        """,
    )
    token_map = TokenMap()
    findings = [Finding("华东三期项目", EntityType.PROJECT, 0, 6, "user", 1.0)]

    DocxProcessor().sanitize(source, output, findings, token_map)

    with ZipFile(output) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    assert "<PROJECT_001>" in xml
    assert 'w:val="FF0000"' in xml
    assert "<w:b" in xml
```

- [ ] **Step 2: Run failing DOCX tests**

Run:

```bash
python -m pytest backend/tests/test_docx_processor.py -q
```

Expected: fail with missing `DocxProcessor`.

- [ ] **Step 3: Implement DOCX processor**

Create `backend/cloakbridge/documents/docx_processor.py` with:

```python
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree

from cloakbridge.domain.entities import Finding
from cloakbridge.domain.tokens import TokenMap


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
TEXT_TAG = f"{{{W_NS}}}t"


class DocxProcessor:
    def sanitize(self, source: Path, output: Path, findings: list[Finding], token_map: TokenMap) -> None:
        replacements = {finding.text: token_map.token_for(finding) for finding in findings}
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with ZipFile(source) as archive:
                archive.extractall(tmp_path)
            document_path = tmp_path / "word" / "document.xml"
            self._replace_in_xml(document_path, replacements)
            self._zip_dir(tmp_path, output)

    def _replace_in_xml(self, xml_path: Path, replacements: dict[str, str]) -> None:
        parser = etree.XMLParser(remove_blank_text=False)
        tree = etree.parse(str(xml_path), parser)
        text_nodes = tree.xpath("//w:t", namespaces={"w": W_NS})
        paragraph_nodes = tree.xpath("//w:p", namespaces={"w": W_NS})
        for paragraph in paragraph_nodes:
            nodes = paragraph.xpath(".//w:t", namespaces={"w": W_NS})
            if not nodes:
                continue
            combined = "".join(node.text or "" for node in nodes)
            replaced = combined
            for original, token in sorted(replacements.items(), key=lambda item: -len(item[0])):
                replaced = replaced.replace(original, token)
            if replaced == combined:
                continue
            first = nodes[0]
            first.text = replaced
            for node in nodes[1:]:
                node.text = ""
        for node in text_nodes:
            if node.text == "":
                node.set(f"{{{W_NS}}}space", "preserve")
        tree.write(str(xml_path), encoding="UTF-8", xml_declaration=True, standalone=True)

    def _zip_dir(self, source_dir: Path, output: Path) -> None:
        with ZipFile(output, "w", ZIP_DEFLATED) as archive:
            for path in sorted(source_dir.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(source_dir).as_posix())
```

- [ ] **Step 4: Run DOCX tests**

Run:

```bash
python -m pytest backend/tests/test_docx_processor.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/cloakbridge/documents/docx_processor.py backend/tests/fixtures.py backend/tests/test_docx_processor.py
git commit -m "feat: sanitize docx while preserving styles"
```

## Task 9: XLSX Sanitization with Style Preservation

**Files:**
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/documents/xlsx_processor.py`
- Test: `/Users/luckydog/Documents/LocalEncrypter/backend/tests/test_xlsx_processor.py`

- [ ] **Step 1: Write XLSX preservation tests**

Create `backend/tests/test_xlsx_processor.py` with:

```python
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

from cloakbridge.documents.xlsx_processor import XlsxProcessor
from cloakbridge.domain.entities import EntityType, Finding
from cloakbridge.domain.tokens import TokenMap


def test_xlsx_processor_replaces_strings_and_preserves_style(tmp_path: Path):
    source = tmp_path / "input.xlsx"
    output = tmp_path / "sanitized.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "华东三期项目"
    sheet["A1"] = "上海明远科技有限公司"
    sheet["A1"].font = Font(bold=True, color="FF0000")
    sheet["A1"].fill = PatternFill(fill_type="solid", fgColor="FFFF00")
    workbook.save(source)

    findings = [
        Finding("华东三期项目", EntityType.PROJECT, 0, 6, "user", 1.0),
        Finding("上海明远科技有限公司", EntityType.COMPANY, 0, 10, "user", 1.0),
    ]
    token_map = TokenMap()

    XlsxProcessor().sanitize(source, output, findings, token_map)

    result = load_workbook(output)
    result_sheet = result["<PROJECT_001>"]
    assert result_sheet["A1"].value == "<COMPANY_001>"
    assert result_sheet["A1"].font.bold is True
    assert result_sheet["A1"].font.color.rgb == "00FF0000"
    assert result_sheet["A1"].fill.fgColor.rgb == "00FFFF00"
```

- [ ] **Step 2: Run failing XLSX tests**

Run:

```bash
python -m pytest backend/tests/test_xlsx_processor.py -q
```

Expected: fail with missing `XlsxProcessor`.

- [ ] **Step 3: Implement XLSX processor**

Create `backend/cloakbridge/documents/xlsx_processor.py` with:

```python
from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from cloakbridge.domain.entities import Finding
from cloakbridge.domain.tokens import TokenMap


class XlsxProcessor:
    def sanitize(self, source: Path, output: Path, findings: list[Finding], token_map: TokenMap) -> None:
        replacements = {finding.text: token_map.token_for(finding) for finding in findings}
        workbook = load_workbook(source)
        for sheet in workbook.worksheets:
            sheet.title = self._replace(sheet.title, replacements)
            for row in sheet.iter_rows():
                for cell in row:
                    if isinstance(cell.value, str):
                        cell.value = self._replace(cell.value, replacements)
                    if cell.comment and cell.comment.text:
                        cell.comment.text = self._replace(cell.comment.text, replacements)
                    if cell.hyperlink and cell.hyperlink.display:
                        cell.hyperlink.display = self._replace(cell.hyperlink.display, replacements)
        workbook.save(output)

    def _replace(self, text: str, replacements: dict[str, str]) -> str:
        result = text
        for original, token in sorted(replacements.items(), key=lambda item: -len(item[0])):
            result = result.replace(original, token)
        return result
```

- [ ] **Step 4: Run XLSX tests**

Run:

```bash
python -m pytest backend/tests/test_xlsx_processor.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/cloakbridge/documents/xlsx_processor.py backend/tests/test_xlsx_processor.py
git commit -m "feat: sanitize xlsx while preserving styles"
```

## Task 10: Leakage Guard

**Files:**
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/gateway/__init__.py`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/gateway/leakage_guard.py`
- Test: `/Users/luckydog/Documents/LocalEncrypter/backend/tests/test_leakage_guard.py`

- [ ] **Step 1: Write leakage guard tests**

Create `backend/tests/test_leakage_guard.py` with:

```python
import pytest

from cloakbridge.detection.dictionary import DictionaryEntry, DictionaryMatcher
from cloakbridge.detection.local_ai import DisabledLocalAI
from cloakbridge.detection.pipeline import DetectionPipeline
from cloakbridge.detection.regex_detector import RegexDetector
from cloakbridge.domain.entities import EntityType
from cloakbridge.gateway.leakage_guard import LeakageDetected, LeakageGuard


def make_guard() -> LeakageGuard:
    pipeline = DetectionPipeline(
        RegexDetector(),
        DictionaryMatcher([DictionaryEntry("华东三期项目", EntityType.PROJECT, "project", "confirmed")]),
        DisabledLocalAI(),
    )
    return LeakageGuard(pipeline)


def test_leakage_guard_blocks_raw_sensitive_dictionary_term():
    with pytest.raises(LeakageDetected) as error:
        make_guard().assert_safe("请处理华东三期项目资料")

    assert "华东三期项目" in str(error.value)


def test_leakage_guard_allows_sanitized_tokens():
    make_guard().assert_safe("请处理<PROJECT_001>资料和<IP_001>。")
```

- [ ] **Step 2: Run failing leakage tests**

Run:

```bash
python -m pytest backend/tests/test_leakage_guard.py -q
```

Expected: fail with missing `LeakageGuard`.

- [ ] **Step 3: Implement leakage guard**

Create `backend/cloakbridge/gateway/leakage_guard.py` with:

```python
from __future__ import annotations

from cloakbridge.detection.pipeline import DetectionPipeline


class LeakageDetected(RuntimeError):
    pass


class LeakageGuard:
    def __init__(self, detection_pipeline: DetectionPipeline) -> None:
        self.detection_pipeline = detection_pipeline

    def assert_safe(self, outbound_text: str) -> None:
        findings = self.detection_pipeline.detect(outbound_text)
        if findings:
            preview = ", ".join(f"{finding.entity_type}:{finding.text}" for finding in findings[:5])
            raise LeakageDetected(f"Outbound request contains raw sensitive content: {preview}")
```

- [ ] **Step 4: Run leakage tests**

Run:

```bash
python -m pytest backend/tests/test_leakage_guard.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/cloakbridge/gateway backend/tests/test_leakage_guard.py
git commit -m "feat: block outbound sensitive content"
```

## Task 11: Provider Adapter Shapes and Safe Echo Provider

**Files:**
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/gateway/providers.py`
- Test: `/Users/luckydog/Documents/LocalEncrypter/backend/tests/test_providers.py`

- [ ] **Step 1: Write provider tests**

Create `backend/tests/test_providers.py` with:

```python
import pytest

from cloakbridge.detection.dictionary import DictionaryEntry, DictionaryMatcher
from cloakbridge.detection.local_ai import DisabledLocalAI
from cloakbridge.detection.pipeline import DetectionPipeline
from cloakbridge.detection.regex_detector import RegexDetector
from cloakbridge.domain.entities import EntityType
from cloakbridge.gateway.leakage_guard import LeakageDetected, LeakageGuard
from cloakbridge.gateway.providers import EchoProvider, ProviderConfig


def guard() -> LeakageGuard:
    return LeakageGuard(
        DetectionPipeline(
            RegexDetector(),
            DictionaryMatcher([DictionaryEntry("华东三期项目", EntityType.PROJECT, "project", "confirmed")]),
            DisabledLocalAI(),
        )
    )


def test_echo_provider_returns_sanitized_response():
    provider = EchoProvider(ProviderConfig(provider="custom-openai", model="test", base_url="http://local"))

    response = provider.complete("请总结<PROJECT_001>", guard())

    assert response.sanitized_text == "请总结<PROJECT_001>"


def test_provider_blocks_raw_sensitive_prompt():
    provider = EchoProvider(ProviderConfig(provider="glm", model="glm-test", base_url="http://local"))

    with pytest.raises(LeakageDetected):
        provider.complete("请总结华东三期项目", guard())
```

- [ ] **Step 2: Run failing provider tests**

Run:

```bash
python -m pytest backend/tests/test_providers.py -q
```

Expected: fail with missing provider module.

- [ ] **Step 3: Implement provider adapter boundary**

Create `backend/cloakbridge/gateway/providers.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from cloakbridge.gateway.leakage_guard import LeakageGuard


SUPPORTED_PROVIDERS = {
    "openai",
    "anthropic",
    "gemini",
    "deepseek",
    "qwen",
    "glm",
    "minimax",
    "openrouter",
    "custom-openai",
    "custom-anthropic",
}


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    model: str
    base_url: str | None = None
    api_key: str | None = None

    def __post_init__(self) -> None:
        if self.provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {self.provider}")


@dataclass(frozen=True)
class ProviderResponse:
    sanitized_text: str
    attachments: list[str]


class ModelProvider(Protocol):
    def complete(self, sanitized_prompt: str, leakage_guard: LeakageGuard) -> ProviderResponse:
        """Send sanitized content only and return sanitized model output."""


class EchoProvider:
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    def complete(self, sanitized_prompt: str, leakage_guard: LeakageGuard) -> ProviderResponse:
        leakage_guard.assert_safe(sanitized_prompt)
        return ProviderResponse(sanitized_text=sanitized_prompt, attachments=[])
```

- [ ] **Step 4: Run provider tests**

Run:

```bash
python -m pytest backend/tests/test_providers.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/cloakbridge/gateway/providers.py backend/tests/test_providers.py
git commit -m "feat: define safe model provider boundary"
```

## Task 12: FastAPI MVP Flow

**Files:**
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/api/__init__.py`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/api/routes.py`
- Create: `/Users/luckydog/Documents/LocalEncrypter/backend/cloakbridge/main.py`
- Test: `/Users/luckydog/Documents/LocalEncrypter/backend/tests/test_api_flow.py`

- [ ] **Step 1: Write API flow test**

Create `backend/tests/test_api_flow.py` with:

```python
from fastapi.testclient import TestClient

from cloakbridge.main import app


def test_api_analyzes_sanitizes_and_restores_text():
    client = TestClient(app)

    analysis = client.post(
        "/api/analyze-text",
        json={
            "text": "华东三期项目服务器10.18.2.4",
            "dictionary": [{"text": "华东三期项目", "entity_type": "PROJECT", "scope": "project"}],
        },
    )
    assert analysis.status_code == 200
    findings = analysis.json()["findings"]
    assert any(item["text"] == "华东三期项目" for item in findings)
    assert any(item["text"] == "10.18.2.4" for item in findings)

    sanitized = client.post(
        "/api/sanitize-text",
        json={"text": "华东三期项目服务器10.18.2.4", "findings": findings},
    )
    assert sanitized.status_code == 200
    payload = sanitized.json()
    assert payload["sanitized_text"] == "<PROJECT_001>服务器<IP_001>"

    restored = client.post(
        "/api/restore-text",
        json={"sanitized_text": "分析<PROJECT_001>和<IP_001>", "token_map": payload["token_map"]},
    )
    assert restored.status_code == 200
    assert restored.json()["restored_text"] == "分析华东三期项目和10.18.2.4"
```

- [ ] **Step 2: Run failing API test**

Run:

```bash
python -m pytest backend/tests/test_api_flow.py -q
```

Expected: fail with missing `app`.

- [ ] **Step 3: Implement API routes**

Create `backend/cloakbridge/api/routes.py` with:

```python
from __future__ import annotations

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
    return {"findings": [finding.__dict__ for finding in findings]}


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
```

Create `backend/cloakbridge/main.py` with:

```python
from __future__ import annotations

from fastapi import FastAPI

from cloakbridge.api.routes import router

app = FastAPI(title="CloakBridge", version="0.1.0")
app.include_router(router)
```

- [ ] **Step 4: Run API tests**

Run:

```bash
python -m pytest backend/tests/test_api_flow.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/cloakbridge/api backend/cloakbridge/main.py backend/tests/test_api_flow.py
git commit -m "feat: expose local text sanitization API"
```

## Task 13: Frontend Bootstrap and Review UI

**Files:**
- Create: `/Users/luckydog/Documents/LocalEncrypter/frontend/package.json`
- Create: `/Users/luckydog/Documents/LocalEncrypter/frontend/tsconfig.json`
- Create: `/Users/luckydog/Documents/LocalEncrypter/frontend/vite.config.ts`
- Create: `/Users/luckydog/Documents/LocalEncrypter/frontend/index.html`
- Create: `/Users/luckydog/Documents/LocalEncrypter/frontend/src/main.tsx`
- Create: `/Users/luckydog/Documents/LocalEncrypter/frontend/src/App.tsx`
- Create: `/Users/luckydog/Documents/LocalEncrypter/frontend/src/styles.css`
- Create: `/Users/luckydog/Documents/LocalEncrypter/frontend/src/api/client.ts`
- Create: `/Users/luckydog/Documents/LocalEncrypter/frontend/src/components/Shell.tsx`
- Create: `/Users/luckydog/Documents/LocalEncrypter/frontend/src/components/FileDrop.tsx`
- Create: `/Users/luckydog/Documents/LocalEncrypter/frontend/src/components/FindingsReview.tsx`
- Create: `/Users/luckydog/Documents/LocalEncrypter/frontend/src/components/ProviderPanel.tsx`
- Create: `/Users/luckydog/Documents/LocalEncrypter/frontend/src/components/ResponseViewer.tsx`
- Test: `/Users/luckydog/Documents/LocalEncrypter/frontend/tests/App.test.tsx`

- [ ] **Step 1: Create frontend package**

Create `frontend/package.json` with:

```json
{
  "name": "cloakbridge-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1 --port 5173",
    "build": "tsc && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.4.0",
    "typescript": "^5.5.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.468.0"
  },
  "devDependencies": {
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.4.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "jsdom": "^25.0.0",
    "vitest": "^2.0.0"
  }
}
```

- [ ] **Step 2: Create TypeScript and Vite config**

Create `frontend/tsconfig.json` with:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src", "tests"]
}
```

Create `frontend/vite.config.ts` with:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8765",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
  },
});
```

- [ ] **Step 3: Create frontend shell files**

Create `frontend/index.html` with:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>CloakBridge</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `frontend/src/main.tsx` with:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 4: Create API client**

Create `frontend/src/api/client.ts` with:

```ts
export type Finding = {
  text: string;
  entity_type: string;
  start: number;
  end: number;
  source: string;
  confidence: number;
};

export async function analyzeText(text: string) {
  const response = await fetch("/api/analyze-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, dictionary: [] }),
  });
  if (!response.ok) throw new Error("分析失败");
  return (await response.json()) as { findings: Finding[] };
}

export async function sanitizeText(text: string, findings: Finding[]) {
  const response = await fetch("/api/sanitize-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, findings }),
  });
  if (!response.ok) throw new Error("脱敏失败");
  return (await response.json()) as { sanitized_text: string; token_map: Record<string, string> };
}
```

- [ ] **Step 5: Create Codex-inspired UI components**

Create `frontend/src/components/Shell.tsx` with:

```tsx
import type { ReactNode } from "react";

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">CloakBridge</div>
        <button className="nav-item active">审阅</button>
        <button className="nav-item">词库</button>
        <button className="nav-item">模型</button>
      </aside>
      <main className="workspace">{children}</main>
    </div>
  );
}
```

Create `frontend/src/components/FileDrop.tsx` with:

```tsx
export function FileDrop({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <section className="panel">
      <h2>本地内容</h2>
      <textarea
        aria-label="本地内容"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="粘贴需要脱敏的文字，文件上传会在后续任务接入。"
      />
    </section>
  );
}
```

Create `frontend/src/components/FindingsReview.tsx` with:

```tsx
import type { Finding } from "../api/client";

export function FindingsReview({ findings }: { findings: Finding[] }) {
  return (
    <section className="panel">
      <h2>敏感项审阅</h2>
      <div className="finding-list">
        {findings.map((finding, index) => (
          <label className="finding-row" key={`${finding.start}-${finding.end}-${index}`}>
            <input type="checkbox" defaultChecked />
            <span>{finding.text}</span>
            <code>{finding.entity_type}</code>
            <small>{finding.source}</small>
          </label>
        ))}
      </div>
    </section>
  );
}
```

Create `frontend/src/components/ProviderPanel.tsx` with:

```tsx
export function ProviderPanel() {
  return (
    <section className="panel">
      <h2>模型</h2>
      <select aria-label="模型供应商" defaultValue="custom-openai">
        <option value="custom-openai">Custom OpenAI-compatible</option>
        <option value="glm">GLM / 智谱</option>
        <option value="minimax">MiniMax</option>
        <option value="deepseek">DeepSeek</option>
        <option value="qwen">Qwen / 通义</option>
        <option value="openrouter">OpenRouter</option>
      </select>
    </section>
  );
}
```

Create `frontend/src/components/ResponseViewer.tsx` with:

```tsx
export function ResponseViewer({
  restored,
  sanitized,
}: {
  restored: string;
  sanitized: string;
}) {
  return (
    <section className="panel">
      <h2>回复</h2>
      <div className="restored-response">{restored || "恢复后的回复会显示在这里。"}</div>
      <details>
        <summary>查看脱敏回复</summary>
        <pre>{sanitized}</pre>
      </details>
    </section>
  );
}
```

- [ ] **Step 6: Create app composition and styles**

Create `frontend/src/App.tsx` with:

```tsx
import { useState } from "react";
import { analyzeText, sanitizeText, type Finding } from "./api/client";
import { FileDrop } from "./components/FileDrop";
import { FindingsReview } from "./components/FindingsReview";
import { ProviderPanel } from "./components/ProviderPanel";
import { ResponseViewer } from "./components/ResponseViewer";
import { Shell } from "./components/Shell";

export function App() {
  const [text, setText] = useState("华东三期项目服务器10.18.2.4");
  const [findings, setFindings] = useState<Finding[]>([]);
  const [sanitized, setSanitized] = useState("");
  const [restored, setRestored] = useState("");

  async function runAnalysis() {
    const analysis = await analyzeText(text);
    setFindings(analysis.findings);
  }

  async function runSanitize() {
    const result = await sanitizeText(text, findings);
    setSanitized(result.sanitized_text);
    setRestored(text);
  }

  return (
    <Shell>
      <div className="toolbar">
        <button onClick={runAnalysis}>分析</button>
        <button onClick={runSanitize}>脱敏</button>
      </div>
      <div className="grid">
        <FileDrop value={text} onChange={setText} />
        <FindingsReview findings={findings} />
        <ProviderPanel />
        <ResponseViewer restored={restored} sanitized={sanitized} />
      </div>
    </Shell>
  );
}
```

Create `frontend/src/styles.css` with:

```css
:root {
  color: #1f2328;
  background: #f6f7f9;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

body {
  margin: 0;
}

button,
select,
textarea {
  font: inherit;
}

.app-shell {
  display: grid;
  grid-template-columns: 220px 1fr;
  min-height: 100vh;
}

.sidebar {
  background: #ffffff;
  border-right: 1px solid #d8dee4;
  padding: 16px;
}

.brand {
  font-weight: 700;
  margin-bottom: 20px;
}

.nav-item {
  display: block;
  width: 100%;
  border: 0;
  background: transparent;
  text-align: left;
  padding: 8px 10px;
  border-radius: 6px;
}

.nav-item.active {
  background: #eef2f7;
}

.workspace {
  padding: 20px;
}

.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.toolbar button {
  border: 1px solid #c9d1d9;
  background: #ffffff;
  border-radius: 6px;
  padding: 8px 12px;
}

.grid {
  display: grid;
  grid-template-columns: minmax(320px, 1fr) minmax(320px, 1fr);
  gap: 16px;
}

.panel {
  background: #ffffff;
  border: 1px solid #d8dee4;
  border-radius: 8px;
  padding: 14px;
}

.panel h2 {
  font-size: 14px;
  margin: 0 0 12px;
}

textarea {
  box-sizing: border-box;
  width: 100%;
  min-height: 220px;
  border: 1px solid #c9d1d9;
  border-radius: 6px;
  padding: 10px;
}

.finding-list {
  display: grid;
  gap: 8px;
}

.finding-row {
  display: grid;
  grid-template-columns: 24px 1fr auto auto;
  gap: 8px;
  align-items: center;
}

code {
  background: #f6f8fa;
  border-radius: 4px;
  padding: 2px 4px;
}

.restored-response {
  min-height: 80px;
  white-space: pre-wrap;
}

pre {
  white-space: pre-wrap;
}

@media (max-width: 860px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-right: 0;
    border-bottom: 1px solid #d8dee4;
  }

  .grid {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 7: Add frontend smoke test**

Create `frontend/tests/App.test.tsx` with:

```tsx
import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { App } from "../src/App";

test("renders CloakBridge review workspace", () => {
  render(<App />);
  expect(screen.getByText("CloakBridge")).toBeInTheDocument();
  expect(screen.getByText("敏感项审阅")).toBeInTheDocument();
  expect(screen.getByText("模型")).toBeInTheDocument();
});
```

- [ ] **Step 8: Run frontend build and tests**

Run:

```bash
cd frontend && npm install && npm test && npm run build
```

Expected: tests pass and Vite build completes.

- [ ] **Step 9: Commit**

```bash
git add frontend
git commit -m "feat: add local review webui"
```

## Task 14: End-to-End Verification and Safety Scan

**Files:**
- Modify: `/Users/luckydog/Documents/LocalEncrypter/README.md`

- [ ] **Step 1: Add README operating rules**

Create or replace `README.md` with:

```markdown
# CloakBridge

CloakBridge is a local privacy gateway for office documents and external AI.

## Security Rules

- Original sensitive documents stay on the local machine.
- Sensitive dictionaries and token mappings stay on the local machine.
- External providers receive sanitized content only.
- The backend binds to `127.0.0.1` by default.
- The public repository contains synthetic data only.

## MVP Scope

- `.txt`
- `.docx`
- `.xlsx`

PDF, PPT, CAD, drawings, images, OCR, and heavy local LLMs are outside the first version.

## Local Backend

```bash
python -m uvicorn cloakbridge.main:app --app-dir backend --host 127.0.0.1 --port 8765
```

## WebUI

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.
```

- [ ] **Step 2: Run backend tests**

Run:

```bash
python -m pytest -q
```

Expected: all backend tests pass.

- [ ] **Step 3: Run frontend tests and build**

Run:

```bash
cd frontend && npm test && npm run build
```

Expected: Vitest passes and Vite build completes.

- [ ] **Step 4: Run repository safety scan**

Run:

```bash
git status --short
git ls-files | rg '(\.docx$|\.xlsx$|\.sqlite$|\.db$|mapping.*\.json$|\.env$|vault|uploads|outputs|data/)'
```

Expected: `git status --short` shows only intended source changes before commit. The `git ls-files` command prints no sensitive files.

- [ ] **Step 5: Commit verification docs**

```bash
git add README.md
git commit -m "docs: document local safety rules"
```

## Self-Review Checklist

- Spec coverage: Tasks cover local-only backend, WebUI, `.txt/.docx/.xlsx`, rule detection, dictionary matching, token restoration, provider boundary, leakage guard, GitHub public safety, and restored response display.
- Out-of-scope preserved: No PDF, PPT, CAD, OCR, cloud-hosted Web App, LAN mode, or Qwen 8B dependency is introduced.
- Public repo safety: `.gitignore`, README rules, and safety scan prevent sensitive files from entering GitHub.
- Format preservation: DOCX and XLSX tasks include style-preservation tests.
- Chinese-first: Tests use Chinese project/company examples and IP/project sensitive cases.
- Execution model: Each task can be implemented and committed independently.
