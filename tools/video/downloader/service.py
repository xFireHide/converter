"""Serviços para download de vídeos/áudios do YouTube."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from yt_dlp import YoutubeDL

from core.settings import settings
from core.storage import RetentionPolicy, cleanup_retention_policies, ensure_directory

DOWNLOAD_FOLDER = ensure_directory(settings.base_dir / "static" / "video" / "downloader" / "downloads")
ALLOWED_FORMATS = {"mp4", "mp3"}
YOUTUBE_URL_REGEX = re.compile(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/")


@dataclass(slots=True)
class DownloadResult:
    filename: str
    filepath: Path
    title: str
    duration: int | None


def cleanup_old_files(retention_seconds: int = settings.file_retention_seconds) -> None:
    cleanup_retention_policies([RetentionPolicy(DOWNLOAD_FOLDER, retention_seconds)])


def validate_url(url: str) -> bool:
    if not url:
        return False
    return bool(YOUTUBE_URL_REGEX.match(url.strip()))


def _build_downloader(format_: Literal["mp4", "mp3"], output_path: Path) -> YoutubeDL:
    base_opts: dict[str, object] = {
        "outtmpl": str(output_path),
        "quiet": True,
        "restrictfilenames": True,
        "nocheckcertificate": True,
        "noprogress": True,
        "nopart": True,
        "prefer_ffmpeg": True,
        "geo_bypass": True,
        "geo_bypass_country": "BR",
    }

    if format_ == "mp4":
        base_opts.update(
            {
                "format": "bv*+ba/best",
                "merge_output_format": "mp4",
            }
        )
    else:  # mp3
        base_opts.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    },
                ],
            }
        )

    return YoutubeDL(base_opts)


def download_media(url: str, format_: Literal["mp4", "mp3"]) -> DownloadResult:
    if format_ not in ALLOWED_FORMATS:
        raise ValueError("Formato solicitado não é suportado.")

    if not validate_url(url):
        raise ValueError("Informe uma URL válida do YouTube.")

    unique_id = uuid.uuid4().hex
    filename = f"{unique_id}.{format_}"
    output_path = DOWNLOAD_FOLDER / filename

    downloader = _build_downloader(format_, output_path)

    try:
        info = downloader.extract_info(url, download=True)
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Não foi possível baixar o vídeo no momento.") from exc

    # yt-dlp pode alterar extensão final (ex.: webm). Garantir renomeação
    final_path = _resolve_downloaded_file(output_path, format_)

    title = info.get("title") or ""
    duration = info.get("duration")

    return DownloadResult(
        filename=final_path.name,
        filepath=final_path,
        title=title,
        duration=duration if isinstance(duration, int) else None,
    )


def _resolve_downloaded_file(expected_path: Path, requested_format: str) -> Path:
    if expected_path.exists():
        return expected_path

    # Caso yt-dlp salve com outra extensão, buscar arquivo gerado
    pattern = expected_path.with_suffix("").name
    for file in DOWNLOAD_FOLDER.glob(f"{pattern}.*"):
        if requested_format == "mp3" and file.suffix.lower() != ".mp3":
            continue
        if requested_format == "mp4" and file.suffix.lower() not in {".mp4", ".m4v"}:
            continue
        # Renomear para a extensão esperada
        target = DOWNLOAD_FOLDER / f"{pattern}.{requested_format}"
        file.rename(target)
        return target

    raise RuntimeError("Falha ao localizar arquivo baixado.")

