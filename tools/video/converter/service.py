import os
import subprocess
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

from core.settings import settings
from core.storage import RetentionPolicy, cleanup_retention_policies, ensure_directory
from werkzeug.utils import secure_filename

# Optional import for imageio_ffmpeg
try:
    from imageio_ffmpeg import get_ffmpeg_exe
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False
    def get_ffmpeg_exe():
        return "ffmpeg"  # Fallback to system ffmpeg

UPLOAD_FOLDER = ensure_directory(settings.base_dir / "static" / "video" / "converter" / "uploads")
CONVERTED_FOLDER = ensure_directory(settings.base_dir / "static" / "video" / "converter" / "converted")

FILE_RETENTION_SECONDS = settings.file_retention_seconds
try:
    MAX_FILE_SIZE_MB = int(os.environ.get("VIDEO_MAX_FILE_SIZE_MB", "500"))
except (TypeError, ValueError):
    MAX_FILE_SIZE_MB = 500
else:
    if MAX_FILE_SIZE_MB <= 0:
        MAX_FILE_SIZE_MB = 500
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
FFMPEG_TIMEOUT_SECONDS = 15 * 60  # 15 minutes per job

ALLOWED_INPUT_EXTENSIONS = {
    "264",
    "3g2",
    "3gp",
    "amv",
    "asf",
    "asx",
    "avi",
    "avchd",
    "bik",
    "drc",
    "divx",
    "dv",
    "f4v",
    "flv",
    "hevc",
    "h265",
    "m1v",
    "m2t",
    "m2ts",
    "m2v",
    "m4v",
    "mkv",
    "mod",
    "mov",
    "mp4",
    "mpeg",
    "mpg",
    "mpv",
    "mts",
    "mxf",
    "ogm",
    "ogv",
    "ogx",
    "ogg",
    "qt",
    "rm",
    "rmvb",
    "tod",
    "trp",
    "ts",
    "vob",
    "vro",
    "webm",
    "wmv",
    "y4m",
}

OUTPUT_FORMATS: Dict[str, Dict[str, object]] = {
    "mp4": {
        "label": "MP4 (H.264 + AAC)",
        "group": "Modernos",
        "params": [
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-map_metadata",
            "-1",
        ],
    },
    "m4v": {
        "label": "M4V (H.264 + AAC)",
        "group": "Modernos",
        "params": [
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-map_metadata",
            "-1",
        ],
    },
    "mkv": {
        "label": "MKV (H.264 + AAC)",
        "group": "Modernos",
        "params": [
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-map_metadata",
            "-1",
        ],
    },
    "webm": {
        "label": "WEBM (VP9 + Opus)",
        "group": "Modernos",
        "params": [
            "-c:v",
            "libvpx-vp9",
            "-b:v",
            "0",
            "-crf",
            "33",
            "-row-mt",
            "1",
            "-c:a",
            "libopus",
            "-b:a",
            "128k",
            "-map_metadata",
            "-1",
        ],
    },
    "webm_vp8": {
        "label": "WEBM (VP8 + Vorbis)",
        "group": "Abertos",
        "extension": "webm",
        "params": [
            "-c:v",
            "libvpx",
            "-b:v",
            "2500k",
            "-quality",
            "good",
            "-cpu-used",
            "0",
            "-c:a",
            "libvorbis",
            "-b:a",
            "160k",
            "-map_metadata",
            "-1",
        ],
    },
    "mp4_hevc": {
        "label": "MP4 (HEVC H.265 + AAC)",
        "group": "Alta eficiência",
        "extension": "mp4",
        "params": [
            "-c:v",
            "libx265",
            "-preset",
            "medium",
            "-crf",
            "28",
            "-tag:v",
            "hvc1",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-map_metadata",
            "-1",
        ],
    },
    "mp4_hevc_main10": {
        "label": "MP4 (HEVC 10-bit + AAC)",
        "group": "Alta eficiência",
        "extension": "mp4",
        "params": [
            "-c:v",
            "libx265",
            "-preset",
            "slow",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p10le",
            "-tag:v",
            "hvc1",
            "-x265-params",
            "profile=main10",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-map_metadata",
            "-1",
        ],
    },
    "mkv_av1": {
        "label": "MKV (AV1 + Opus)",
        "group": "Alta eficiência",
        "extension": "mkv",
        "params": [
            "-c:v",
            "libaom-av1",
            "-cpu-used",
            "4",
            "-crf",
            "30",
            "-b:v",
            "0",
            "-row-mt",
            "1",
            "-tiles",
            "2x2",
            "-c:a",
            "libopus",
            "-b:a",
            "128k",
            "-map_metadata",
            "-1",
        ],
    },
    "mp4_4k60": {
        "label": "MP4 4K60 (H.264 + AAC)",
        "group": "Modernos",
        "extension": "mp4",
        "params": [
            "-vf",
            "scale=3840:-2:flags=lanczos,fps=60",
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-profile:v",
            "high",
            "-level",
            "5.2",
            "-b:v",
            "18000k",
            "-maxrate",
            "24000k",
            "-bufsize",
            "36000k",
            "-c:a",
            "aac",
            "-b:a",
            "256k",
            "-map_metadata",
            "-1",
        ],
    },
    "mp4_lowlatency": {
        "label": "MP4 Baixa Latência (H.264)",
        "group": "Streaming",
        "extension": "mp4",
        "params": [
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-tune",
            "zerolatency",
            "-profile:v",
            "baseline",
            "-level",
            "3.1",
            "-pix_fmt",
            "yuv420p",
            "-b:v",
            "2500k",
            "-maxrate",
            "2500k",
            "-bufsize",
            "5000k",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-map_metadata",
            "-1",
        ],
    },
    "mov": {
        "label": "MOV (H.264 + AAC)",
        "group": "Compatibilidade",
        "params": [
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-map_metadata",
            "-1",
        ],
    },
    "mov_dnxhd": {
        "label": "MOV (DNxHD 145)",
        "group": "Broadcast",
        "extension": "mov",
        "params": [
            "-c:v",
            "dnxhd",
            "-b:v",
            "145M",
            "-pix_fmt",
            "yuv422p",
            "-c:a",
            "pcm_s16le",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-map_metadata",
            "-1",
        ],
    },
    "avi": {
        "label": "AVI (MPEG-4 + MP3)",
        "group": "Compatibilidade",
        "params": [
            "-c:v",
            "mpeg4",
            "-qscale:v",
            "5",
            "-c:a",
            "libmp3lame",
            "-q:a",
            "4",
            "-map_metadata",
            "-1",
        ],
    },
    "mpeg": {
        "label": "MPEG (MPEG-2 + MP2)",
        "group": "Compatibilidade",
        "params": [
            "-c:v",
            "mpeg2video",
            "-qscale:v",
            "5",
            "-c:a",
            "mp2",
            "-b:a",
            "192k",
            "-map_metadata",
            "-1",
        ],
    },
    "mpg": {
        "label": "MPG (MPEG-2 + MP2)",
        "group": "Compatibilidade",
        "params": [
            "-c:v",
            "mpeg2video",
            "-qscale:v",
            "5",
            "-c:a",
            "mp2",
            "-b:a",
            "192k",
            "-map_metadata",
            "-1",
        ],
    },
    "flv": {
        "label": "FLV (H.264 + AAC)",
        "group": "Legados",
        "params": [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "28",
            "-c:a",
            "aac",
            "-ar",
            "44100",
            "-b:a",
            "128k",
            "-f",
            "flv",
            "-map_metadata",
            "-1",
        ],
    },
    "wmv": {
        "label": "WMV (WMV2 + WMA)",
        "group": "Legados",
        "params": [
            "-c:v",
            "wmv2",
            "-b:v",
            "1500k",
            "-c:a",
            "wmav2",
            "-b:a",
            "192k",
            "-map_metadata",
            "-1",
        ],
    },
    "ts": {
        "label": "TS (H.264 + AAC)",
        "group": "Streaming",
        "params": [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-f",
            "mpegts",
            "-map_metadata",
            "-1",
        ],
    },
    "m2ts": {
        "label": "M2TS (H.264 + AAC)",
        "group": "Streaming",
        "params": [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-f",
            "mpegts",
            "-map_metadata",
            "-1",
        ],
    },
    "3gp": {
        "label": "3GP (H.264 + AAC)",
        "group": "Mobile",
        "params": [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "28",
            "-vf",
            "scale=320:-2",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "-ar",
            "22050",
            "-map_metadata",
            "-1",
        ],
    },
    "3g2": {
        "label": "3G2 (H.264 + AAC)",
        "group": "Mobile",
        "params": [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "28",
            "-vf",
            "scale=480:-2",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "-ar",
            "22050",
            "-map_metadata",
            "-1",
        ],
    },
    "ogv": {
        "label": "OGV (Theora + Vorbis)",
        "group": "Abertos",
        "params": [
            "-c:v",
            "libtheora",
            "-q:v",
            "7",
            "-c:a",
            "libvorbis",
            "-q:a",
            "5",
            "-map_metadata",
            "-1",
        ],
    },
    "ogg": {
        "label": "OGG (Theora + Vorbis)",
        "group": "Abertos",
        "params": [
            "-c:v",
            "libtheora",
            "-q:v",
            "7",
            "-c:a",
            "libvorbis",
            "-q:a",
            "5",
            "-map_metadata",
            "-1",
        ],
    },
    "gif": {
        "label": "GIF animado (480p @15fps)",
        "group": "Criativos",
        "params": [
            "-vf",
            "fps=15,scale=480:-2:flags=lanczos",
            "-loop",
            "0",
            "-an",
            "-f",
            "gif",
            "-map_metadata",
            "-1",
        ],
    },
    "mkv_lossless": {
        "label": "MKV (FFV1 + FLAC)",
        "group": "Arquivamento",
        "extension": "mkv",
        "params": [
            "-c:v",
            "ffv1",
            "-level",
            "3",
            "-coder",
            "1",
            "-context",
            "1",
            "-g",
            "1",
            "-slicecrc",
            "1",
            "-c:a",
            "flac",
            "-compression_level",
            "12",
            "-map_metadata",
            "-1",
        ],
    },
    "mxf": {
        "label": "MXF (MPEG-2 + PCM)",
        "group": "Profissional",
        "params": [
            "-c:v",
            "mpeg2video",
            "-b:v",
            "50000k",
            "-minrate",
            "50000k",
            "-maxrate",
            "50000k",
            "-bufsize",
            "3640k",
            "-c:a",
            "pcm_s16le",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-map_metadata",
            "-1",
        ],
    },
    "mxf_xdcamhd": {
        "label": "MXF (XDCAM HD422)",
        "group": "Broadcast",
        "extension": "mxf",
        "params": [
            "-c:v",
            "mpeg2video",
            "-b:v",
            "50000k",
            "-minrate",
            "50000k",
            "-maxrate",
            "50000k",
            "-bufsize",
            "3640k",
            "-flags",
            "+ildct+ilme",
            "-dc",
            "10",
            "-intra_vlc",
            "1",
            "-non_linear_q",
            "1",
            "-ps",
            "1",
            "-qmin",
            "1",
            "-c:a",
            "pcm_s16le",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-map_metadata",
            "-1",
        ],
    },
    "mov_prores": {
        "label": "MOV (ProRes 422 HQ)",
        "group": "Profissional",
        "extension": "mov",
        "params": [
            "-c:v",
            "prores_ks",
            "-profile:v",
            "3",
            "-pix_fmt",
            "yuv422p10le",
            "-vendor",
            "appl",
            "-c:a",
            "pcm_s16le",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-map_metadata",
            "-1",
        ],
    },
    "mov_hap": {
        "label": "MOV (Hap)",
        "group": "Criativos",
        "extension": "mov",
        "params": [
            "-c:v",
            "hap",
            "-c:a",
            "pcm_s16le",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-map_metadata",
            "-1",
        ],
    },
    "f4v": {
        "label": "F4V (H.264 + AAC)",
        "group": "Streaming",
        "params": [
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-map_metadata",
            "-1",
        ],
    },
    "vob": {
        "label": "VOB (MPEG-2 + AC3)",
        "group": "Legados",
        "params": [
            "-c:v",
            "mpeg2video",
            "-qscale:v",
            "5",
            "-c:a",
            "ac3",
            "-b:a",
            "192k",
            "-f",
            "vob",
            "-map_metadata",
            "-1",
        ],
    },
    "dv": {
        "label": "DV (DVCPRO)",
        "group": "Profissional",
        "params": [
            "-c:v",
            "dvvideo",
            "-c:a",
            "pcm_s16le",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-map_metadata",
            "-1",
        ],
    },
}

OUTPUT_FORMAT_GROUPS: List[Tuple[str, List[Tuple[str, str]]]] = []
_grouped: Dict[str, List[Tuple[str, str]]] = {}
for key, config in OUTPUT_FORMATS.items():
    label = config["label"]
    group = config["group"]
    _grouped.setdefault(group, []).append((key, label))
for group in [
    "Modernos",
    "Alta eficiência",
    "Compatibilidade",
    "Streaming",
    "Mobile",
    "Abertos",
    "Legados",
    "Profissional",
    "Broadcast",
    "Arquivamento",
    "Criativos",
]:
    if group in _grouped:
        OUTPUT_FORMAT_GROUPS.append((group, sorted(_grouped[group], key=lambda item: item[0])))

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


def save_video(file_storage) -> Path:
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
            f"Arquivo excede o limite de {MAX_FILE_SIZE_MB} MB. Envie um vídeo menor."
        )
    return destination


def validate_video(path: Path) -> bool:
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
                timeout=30,
            )
            stream_types = {line.strip() for line in result.stdout.splitlines() if line.strip()}
            return "video" in stream_types
        except (subprocess.SubprocessError, ValueError):
            return False

    # Fallback: attempt to decode a single frame to confirm video stream
    fallback_cmd = [
        str(ffmpeg_path),
        "-v",
        "error",
        "-i",
        str(path),
        "-map",
        "0:v:0",
        "-frames:v",
        "1",
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
            timeout=45,
        )
        return True
    except subprocess.SubprocessError:
        return False


def convert_video(input_path: Path, output_format: str) -> str:
    fmt = output_format.lower()
    if fmt not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError("Formato de saída inválido.")

    config = OUTPUT_FORMATS[fmt]
    params = config["params"]
    extension = config.get("extension", fmt)
    output_filename = secure_filename(f"{uuid.uuid4().hex}.{extension}")
    output_path = (CONVERTED_FOLDER / output_filename).resolve()
    if output_path.parent != CONVERTED_FOLDER:
        raise RuntimeError("Destino inválido para o arquivo convertido.")

    ffmpeg_exe = get_ffmpeg_exe()
    cmd = [ffmpeg_exe, "-y", "-i", str(input_path)] + list(params) + [str(output_path)]

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
            "Falha ao converter o vídeo. Verifique se o arquivo é válido e tente novamente."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        output_path.unlink(missing_ok=True)
        raise RuntimeError("Conversão excedeu o tempo máximo permitido.") from exc

    return output_filename
