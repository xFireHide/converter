from __future__ import annotations

import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RetentionPolicy:
    """Describe how long files in a directory should be kept."""

    path: Path
    seconds: int
    pattern: str = "*"


def ensure_directory(path: Path) -> Path:
    """Create the directory if necessary and return its resolved path."""
    resolved = path.resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def cleanup_retention_policies(policies: Iterable[RetentionPolicy]) -> None:
    """Remove files older than the configured retention for each directory."""
    now = time.time()
    for policy in policies:
        path = ensure_directory(policy.path)
        cutoff = now - policy.seconds
        for file_path in path.glob(policy.pattern):
            try:
                mtime = file_path.stat().st_mtime
                if file_path.is_file() and mtime < cutoff:
                    file_path.unlink(missing_ok=True)
                elif file_path.is_dir() and mtime < cutoff:
                    shutil.rmtree(file_path, ignore_errors=True)
            except OSError as exc:  # pragma: no cover - log unexpected issue
                logging.getLogger(__name__).debug(
                    "Falha ao limpar %s: %s", file_path, exc, exc_info=exc
                )
