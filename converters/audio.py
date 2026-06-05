"""Conversão de áudio entre formatos usando ffmpeg."""
from __future__ import annotations

from pathlib import Path

from .common import run_ffmpeg, unique_output_path

NAME = "Áudio"
FFMPEG_TIMEOUT_SECONDS = 10 * 60

INPUT_EXTENSIONS = {
    "mp3", "wav", "ogg", "oga", "aac", "m4a", "flac", "alac", "aiff", "aif",
    "aifc", "opus", "amr", "wma", "ac3", "mp2", "mpc", "caf", "wv",
}

_FORMATS: dict[str, dict] = {
    "mp3": {"label": "MP3 (CBR 192 kbps)", "params": ["-codec:a", "libmp3lame", "-b:a", "192k"]},
    "aac": {"label": "AAC (LC 192 kbps)", "params": ["-codec:a", "aac", "-b:a", "192k"]},
    "m4a": {"label": "M4A (AAC 192 kbps)", "params": ["-codec:a", "aac", "-b:a", "192k"]},
    "alac": {"label": "ALAC (sem perdas)", "params": ["-codec:a", "alac"]},
    "flac": {"label": "FLAC (sem perdas)", "params": ["-codec:a", "flac"]},
    "ogg": {"label": "OGG Vorbis (qualidade 5)", "params": ["-codec:a", "libvorbis", "-qscale:a", "5"]},
    "opus": {"label": "Opus (128 kbps)", "params": ["-codec:a", "libopus", "-b:a", "128k"]},
    "wav": {"label": "WAV PCM (16-bit)", "params": ["-codec:a", "pcm_s16le"]},
    "aiff": {"label": "AIFF PCM (16-bit)", "params": ["-codec:a", "pcm_s16be"]},
    "wma": {"label": "WMA (192 kbps)", "params": ["-codec:a", "wmav2", "-b:a", "192k"]},
    "ac3": {"label": "Dolby AC3 (192 kbps)", "params": ["-codec:a", "ac3", "-b:a", "192k"]},
    "mp2": {"label": "MP2 (192 kbps)", "params": ["-codec:a", "mp2", "-b:a", "192k"]},
    "caf": {"label": "CAF PCM (16-bit)", "params": ["-codec:a", "pcm_s16le"]},
}

OUTPUT_FORMAT_GROUPS = [
    ("Com perdas", [(k, _FORMATS[k]["label"]) for k in ("mp3", "aac", "m4a", "ogg", "opus", "wma", "ac3", "mp2")]),
    ("Sem perdas", [(k, _FORMATS[k]["label"]) for k in ("flac", "alac", "wav", "aiff", "caf")]),
]


def convert(input_path: Path, output_format: str, output_dir: Path) -> list[Path]:
    fmt = output_format.lower()
    if fmt not in _FORMATS:
        raise ValueError("Formato de saída inválido.")
    output_path = unique_output_path(output_dir, input_path.stem, fmt)
    params = ["-vn", *_FORMATS[fmt]["params"]]
    run_ffmpeg(input_path, params, output_path, timeout=FFMPEG_TIMEOUT_SECONDS)
    return [output_path]
