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
