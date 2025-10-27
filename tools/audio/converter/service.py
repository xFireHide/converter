import os
import subprocess
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

from core.settings import settings
from core.storage import RetentionPolicy, cleanup_retention_policies, ensure_directory
from imageio_ffmpeg import get_ffmpeg_exe
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = ensure_directory(settings.base_dir / "static" / "audio" / "converter" / "uploads")
CONVERTED_FOLDER = ensure_directory(settings.base_dir / "static" / "audio" / "converter" / "converted")

FILE_RETENTION_SECONDS = settings.file_retention_seconds
try:
    MAX_FILE_SIZE_MB = int(os.environ.get("AUDIO_MAX_FILE_SIZE_MB", "200"))
except (TypeError, ValueError):
    MAX_FILE_SIZE_MB = 200
else:
    if MAX_FILE_SIZE_MB <= 0:
        MAX_FILE_SIZE_MB = 200
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
FFMPEG_TIMEOUT_SECONDS = 10 * 60  # 10 minutes

ALLOWED_INPUT_EXTENSIONS = {
    "mp3",
    "wav",
    "ogg",
    "oga",
    "aac",
    "m4a",
    "flac",
    "alac",
    "aiff",
    "aif",
    "aifc",
    "opus",
    "amr",
    "wma",
    "ac3",
    "mp2",
    "mpc",
    "caf",
    "wv",
}

OUTPUT_FORMATS: Dict[str, Dict[str, object]] = {
    "mp3": {
        "label": "MP3 (CBR 192 kbps)",
        "params": ["-codec:a", "libmp3lame", "-b:a", "192k"],
    },
    "aac": {
        "label": "AAC (LC 192 kbps)",
        "params": ["-codec:a", "aac", "-b:a", "192k"],
    },
    "m4a": {
        "label": "M4A (AAC 192 kbps)",
        "params": ["-codec:a", "aac", "-b:a", "192k"],
    },
    "alac": {
        "label": "ALAC (sem perdas)",
        "params": ["-codec:a", "alac"],
    },
    "flac": {
        "label": "FLAC (sem perdas)",
        "params": ["-codec:a", "flac"],
    },
    "ogg": {
        "label": "OGG Vorbis (qualidade 5)",
        "params": ["-codec:a", "libvorbis", "-qscale:a", "5"],
    },
    "opus": {
        "label": "Opus (128 kbps)",
        "params": ["-codec:a", "libopus", "-b:a", "128k"],
    },
    "wav": {
        "label": "WAV PCM (16-bit)",
        "params": ["-codec:a", "pcm_s16le"],
    },
    "aiff": {
        "label": "AIFF PCM (16-bit)",
        "params": ["-codec:a", "pcm_s16be"],
    },
    "wma": {
        "label": "WMA (192 kbps)",
        "params": ["-codec:a", "wmav2", "-b:a", "192k"],
    },
    "ac3": {
        "label": "Dolby AC3 (192 kbps)",
        "params": ["-codec:a", "ac3", "-b:a", "192k"],
    },
    "mp2": {
        "label": "MP2 (192 kbps)",
        "params": ["-codec:a", "mp2", "-b:a", "192k"],
    },
    "caf": {
        "label": "CAF PCM (16-bit)",
        "params": ["-codec:a", "pcm_s16le"],
    },
}

OUTPUT_FORMAT_GROUPS: List[Tuple[str, List[Tuple[str, str]]]] = [
    (
        "Com perdas",
        [
            ("mp3", OUTPUT_FORMATS["mp3"]["label"]),
            ("aac", OUTPUT_FORMATS["aac"]["label"]),
            ("m4a", OUTPUT_FORMATS["m4a"]["label"]),
            ("ogg", OUTPUT_FORMATS["ogg"]["label"]),
            ("opus", OUTPUT_FORMATS["opus"]["label"]),
            ("wma", OUTPUT_FORMATS["wma"]["label"]),
            ("ac3", OUTPUT_FORMATS["ac3"]["label"]),
            ("mp2", OUTPUT_FORMATS["mp2"]["label"]),
        ],
    ),
    (
        "Sem perdas",
        [
            ("flac", OUTPUT_FORMATS["flac"]["label"]),
            ("alac", OUTPUT_FORMATS["alac"]["label"]),
            ("wav", OUTPUT_FORMATS["wav"]["label"]),
            ("aiff", OUTPUT_FORMATS["aiff"]["label"]),
            ("caf", OUTPUT_FORMATS["caf"]["label"]),
        ],
    ),
]

SUPPORTED_OUTPUT_FORMATS = frozenset(OUTPUT_FORMATS.keys())

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
CONVERTED_FOLDER.mkdir(parents=True, exist_ok=True)


def allowed_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_INPUT_EXTENSIONS


def cleanup_old_files(retention_seconds: int = FILE_RETENTION_SECONDS) -> None:
    cleanup_retention_policies(
        [
            RetentionPolicy(UPLOAD_FOLDER, retention_seconds),
            RetentionPolicy(CONVERTED_FOLDER, retention_seconds),
        ]
    )


def save_audio(file_storage) -> Path:
    original_ext = Path(file_storage.filename).suffix.lower().lstrip(".")
    if not original_ext:
        raise ValueError("Extensão de arquivo ausente.")
    safe_name = secure_filename(f"{uuid.uuid4().hex}.{original_ext}")
    destination = (UPLOAD_FOLDER / safe_name).resolve()
    if destination.parent != UPLOAD_FOLDER:
        raise ValueError("Caminho de upload inválido.")
    file_storage.save(str(destination))
    if destination.stat().st_size > MAX_FILE_SIZE_BYTES:
        destination.unlink(missing_ok=True)
        raise ValueError(
            f"Arquivo excede o limite de {MAX_FILE_SIZE_MB} MB. Envie um áudio menor."
        )
    return destination


def validate_audio(path: Path) -> bool:
    try:
        if not path.exists() or not path.is_file():
            return False
        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return False
    except OSError:
        return False

    ffmpeg_path = Path(get_ffmpeg_exe()).resolve()
    ffprobe_path = ffmpeg_path.with_name("ffprobe")

    probe_cmd: List[str]
    if ffprobe_path.exists():
        probe_cmd = [
            str(ffprobe_path),
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
        try:
            result = subprocess.run(
                probe_cmd,
                capture_output=True,
                check=True,
                text=True,
                timeout=20,
            )
            stream_types = {line.strip() for line in result.stdout.splitlines() if line.strip()}
            return "audio" in stream_types
        except (subprocess.SubprocessError, ValueError):
            return False

    fallback_cmd = [
        str(ffmpeg_path),
        "-v",
        "error",
        "-i",
        str(path),
        "-f",
        "null",
        "-",
    ]
    try:
        subprocess.run(
            fallback_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=30,
        )
        return True
    except subprocess.SubprocessError:
        return False


def convert_audio(input_path: Path, output_format: str) -> str:
    fmt = output_format.lower()
    if fmt not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError("Formato de saída inválido.")

    params = list(OUTPUT_FORMATS[fmt]["params"])
    output_filename = secure_filename(f"{uuid.uuid4().hex}.{fmt}")
    output_path = (CONVERTED_FOLDER / output_filename).resolve()
    if output_path.parent != CONVERTED_FOLDER:
        raise RuntimeError("Destino inválido para o arquivo convertido.")

    ffmpeg_exe = get_ffmpeg_exe()
    cmd = [ffmpeg_exe, "-y", "-i", str(input_path), "-vn"] + params + [str(output_path)]

    try:
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
    except subprocess.CalledProcessError as exc:
        output_path.unlink(missing_ok=True)
        raise RuntimeError(
            "Falha ao converter o arquivo de áudio. Verifique se o arquivo é válido."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        output_path.unlink(missing_ok=True)
        raise RuntimeError("Conversão excedeu o tempo máximo permitido.") from exc

    return output_filename
