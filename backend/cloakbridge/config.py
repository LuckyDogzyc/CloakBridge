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
