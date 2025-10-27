from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    """Global application settings sourced from environment variables."""

    base_dir: Path = Path(__file__).resolve().parent.parent
    logs_dir: Path = base_dir / "logs"
    uploads_dir: Path = base_dir / "uploads"
    processed_dir: Path = base_dir / "processed"

    max_upload_mb: int = _env_int("MAX_UPLOAD_MB", 200)
    file_retention_seconds: int = _env_int("FILE_RETENTION_SECONDS", 60 * 60)
    cleanup_on_startup: bool = os.environ.get("ENABLE_STARTUP_CLEANUP", "1") not in (
        "0",
        "false",
        "False",
    )

    def override(
        self,
        *,
        max_upload_mb: Optional[int] = None,
        file_retention_seconds: Optional[int] = None,
    ) -> "Settings":
        return Settings(
            base_dir=self.base_dir,
            logs_dir=self.logs_dir,
            uploads_dir=self.uploads_dir,
            processed_dir=self.processed_dir,
            max_upload_mb=max_upload_mb if max_upload_mb is not None else self.max_upload_mb,
            file_retention_seconds=(
                file_retention_seconds
                if file_retention_seconds is not None
                else self.file_retention_seconds
            ),
            cleanup_on_startup=self.cleanup_on_startup,
        )


settings = Settings()
settings.logs_dir.mkdir(parents=True, exist_ok=True)
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
settings.processed_dir.mkdir(parents=True, exist_ok=True)
