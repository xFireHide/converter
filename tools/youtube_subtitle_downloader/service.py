import os
import shutil
import subprocess
import uuid
import tempfile
import zipfile
import json
from typing import List, Tuple, Set
from pytube import Playlist

MAX_VIDEOS = 50


def sanitize_url(url: str) -> str | None:
    """Limpa espaços e verifica se a URL parece ser do YouTube."""
    url = url.strip()
    if not url.startswith("http") or "youtube" not in url:
        return None
    return url


def get_video_urls(url: str) -> List[str]:
    if "list=" in url:
        playlist = Playlist(url)
        return playlist.video_urls[:MAX_VIDEOS]
    return [url]


def get_available_languages(video_urls: List[str]) -> List[str]:
    """Retorna a lista unificada de idiomas de legenda disponíveis."""
    languages: Set[str] = set()
    for vurl in video_urls:
        try:
            result = subprocess.run(
                ["yt-dlp", "-j", "--skip-download", vurl],
                check=True,
                timeout=60,
                capture_output=True,
                text=True,
            )
            data = json.loads(result.stdout)
            languages.update(data.get("subtitles", {}).keys())
            languages.update(data.get("automatic_captions", {}).keys())
        except Exception:
            pass
    return sorted(languages)


def download_subtitles(
    video_urls: List[str], tmp_dir: str, lang: str
) -> Tuple[List[str], str | None]:
    legendas_baixadas = []
    for idx, vurl in enumerate(video_urls):
        try:
            subprocess.run(
                [
                    "yt-dlp",
                    "--write-auto-sub",
                    "--sub-lang",
                    lang,
                    "--skip-download",
                    "--output",
                    os.path.join(tmp_dir, "%(title)s.%(ext)s"),
                    vurl,
                ],
                check=True,
                timeout=90,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            legendas_baixadas.append(vurl)
        except Exception:
            pass
    legendas_files = [
        f for f in os.listdir(tmp_dir) if f.endswith(".vtt") or f.endswith(".srt")
    ]
    zip_path = None
    if legendas_files:
        zip_path = os.path.join(tmp_dir, "legendas.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for filename in legendas_files:
                zipf.write(os.path.join(tmp_dir, filename), arcname=filename)
    return legendas_baixadas, zip_path


def process_url(url: str, lang: str) -> Tuple[List[str], str | None, str]:
    tmp_dir = tempfile.mkdtemp(prefix="yt_legendas_")
    video_urls = get_video_urls(url)
    if not video_urls:
        return [], None, tmp_dir
    legendas_baixadas, zip_path = download_subtitles(video_urls, tmp_dir, lang)
    return legendas_baixadas, zip_path, tmp_dir


def cleanup_tmp_dir(path: str) -> None:
    """Remove o diretório temporário utilizado para downloads."""
    try:
        shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass
