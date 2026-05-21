from __future__ import annotations

import json
import re
from pathlib import Path

from cryptography.fernet import Fernet


_SAFE_JOB_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class MappingVault:
    def __init__(self, vault_dir: Path) -> None:
        self.vault_dir = vault_dir
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.key_path = self.vault_dir / "vault.key"
        self.fernet = Fernet(self._load_or_create_key())

    def save(self, job_id: str, token_map: dict[str, str]) -> None:
        payload = json.dumps(token_map, ensure_ascii=False).encode("utf-8")
        encrypted = self.fernet.encrypt(payload)
        self._path_for_job(job_id).write_bytes(encrypted)

    def load(self, job_id: str) -> dict[str, str]:
        encrypted = self._path_for_job(job_id).read_bytes()
        payload = self.fernet.decrypt(encrypted)
        return json.loads(payload.decode("utf-8"))

    def _path_for_job(self, job_id: str) -> Path:
        if not _SAFE_JOB_ID_PATTERN.fullmatch(job_id):
            raise ValueError("Invalid vault job id")
        return self.vault_dir / f"{job_id}.bin"

    def _load_or_create_key(self) -> bytes:
        if self.key_path.exists():
            return self.key_path.read_bytes()
        key = Fernet.generate_key()
        self.key_path.write_bytes(key)
        return key
