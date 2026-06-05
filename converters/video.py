"""Conversão de vídeo entre formatos/codecs usando ffmpeg."""
from __future__ import annotations

from pathlib import Path

from .common import run_ffmpeg, unique_output_path

NAME = "Vídeo"
FFMPEG_TIMEOUT_SECONDS = 30 * 60

INPUT_EXTENSIONS = {
    "264", "3g2", "3gp", "amv", "asf", "asx", "avi", "avchd", "bik", "drc",
    "divx", "dv", "f4v", "flv", "hevc", "h265", "m1v", "m2t", "m2ts", "m2v",
    "m4v", "mkv", "mod", "mov", "mp4", "mpeg", "mpg", "mpv", "mts", "mxf",
    "ogm", "ogv", "ogx", "ogg", "qt", "rm", "rmvb", "tod", "trp", "ts", "vob",
    "vro", "webm", "wmv", "y4m",
}

_FORMATS: dict[str, dict] = {
    "mp4": {"label": "MP4 (H.264 + AAC)", "group": "Modernos",
            "params": ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-map_metadata", "-1"]},
    "m4v": {"label": "M4V (H.264 + AAC)", "group": "Modernos", "extension": "m4v",
            "params": ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-map_metadata", "-1"]},
    "mkv": {"label": "MKV (H.264 + AAC)", "group": "Modernos",
            "params": ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", "192k", "-map_metadata", "-1"]},
    "webm": {"label": "WEBM (VP9 + Opus)", "group": "Modernos",
             "params": ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "33", "-row-mt", "1", "-c:a", "libopus", "-b:a", "128k", "-map_metadata", "-1"]},
    "webm_vp8": {"label": "WEBM (VP8 + Vorbis)", "group": "Abertos", "extension": "webm",
                 "params": ["-c:v", "libvpx", "-b:v", "2500k", "-quality", "good", "-cpu-used", "0", "-c:a", "libvorbis", "-b:a", "160k", "-map_metadata", "-1"]},
    "mp4_hevc": {"label": "MP4 (HEVC H.265 + AAC)", "group": "Alta eficiência", "extension": "mp4",
                 "params": ["-c:v", "libx265", "-preset", "medium", "-crf", "28", "-tag:v", "hvc1", "-c:a", "aac", "-b:a", "160k", "-map_metadata", "-1"]},
    "mp4_hevc_main10": {"label": "MP4 (HEVC 10-bit + AAC)", "group": "Alta eficiência", "extension": "mp4",
                        "params": ["-c:v", "libx265", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p10le", "-tag:v", "hvc1", "-x265-params", "profile=main10", "-c:a", "aac", "-b:a", "192k", "-map_metadata", "-1"]},
    "mkv_av1": {"label": "MKV (AV1 + Opus)", "group": "Alta eficiência", "extension": "mkv",
                "params": ["-c:v", "libaom-av1", "-cpu-used", "4", "-crf", "30", "-b:v", "0", "-row-mt", "1", "-tiles", "2x2", "-c:a", "libopus", "-b:a", "128k", "-map_metadata", "-1"]},
    "mp4_4k60": {"label": "MP4 4K60 (H.264 + AAC)", "group": "Modernos", "extension": "mp4",
                 "params": ["-vf", "scale=3840:-2:flags=lanczos,fps=60", "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-level", "5.2", "-b:v", "18000k", "-maxrate", "24000k", "-bufsize", "36000k", "-c:a", "aac", "-b:a", "256k", "-map_metadata", "-1"]},
    "mp4_lowlatency": {"label": "MP4 Baixa Latência (H.264)", "group": "Streaming", "extension": "mp4",
                       "params": ["-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency", "-profile:v", "baseline", "-level", "3.1", "-pix_fmt", "yuv420p", "-b:v", "2500k", "-maxrate", "2500k", "-bufsize", "5000k", "-c:a", "aac", "-b:a", "128k", "-map_metadata", "-1"]},
    "mov": {"label": "MOV (H.264 + AAC)", "group": "Compatibilidade",
            "params": ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", "192k", "-map_metadata", "-1"]},
    "mov_dnxhd": {"label": "MOV (DNxHD 145)", "group": "Broadcast", "extension": "mov",
                  "params": ["-c:v", "dnxhd", "-b:v", "145M", "-pix_fmt", "yuv422p", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", "-map_metadata", "-1"]},
    "avi": {"label": "AVI (MPEG-4 + MP3)", "group": "Compatibilidade",
            "params": ["-c:v", "mpeg4", "-qscale:v", "5", "-c:a", "libmp3lame", "-q:a", "4", "-map_metadata", "-1"]},
    "mpeg": {"label": "MPEG (MPEG-2 + MP2)", "group": "Compatibilidade",
             "params": ["-c:v", "mpeg2video", "-qscale:v", "5", "-c:a", "mp2", "-b:a", "192k", "-map_metadata", "-1"]},
    "mpg": {"label": "MPG (MPEG-2 + MP2)", "group": "Compatibilidade",
            "params": ["-c:v", "mpeg2video", "-qscale:v", "5", "-c:a", "mp2", "-b:a", "192k", "-map_metadata", "-1"]},
    "flv": {"label": "FLV (H.264 + AAC)", "group": "Legados",
            "params": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-c:a", "aac", "-ar", "44100", "-b:a", "128k", "-f", "flv", "-map_metadata", "-1"]},
    "wmv": {"label": "WMV (WMV2 + WMA)", "group": "Legados",
            "params": ["-c:v", "wmv2", "-b:v", "1500k", "-c:a", "wmav2", "-b:a", "192k", "-map_metadata", "-1"]},
    "ts": {"label": "TS (H.264 + AAC)", "group": "Streaming",
           "params": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k", "-f", "mpegts", "-map_metadata", "-1"]},
    "m2ts": {"label": "M2TS (H.264 + AAC)", "group": "Streaming",
             "params": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k", "-f", "mpegts", "-map_metadata", "-1"]},
    "3gp": {"label": "3GP (H.264 + AAC)", "group": "Mobile",
            "params": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-vf", "scale=320:-2", "-c:a", "aac", "-b:a", "96k", "-ar", "22050", "-map_metadata", "-1"]},
    "3g2": {"label": "3G2 (H.264 + AAC)", "group": "Mobile",
            "params": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-vf", "scale=480:-2", "-c:a", "aac", "-b:a", "96k", "-ar", "22050", "-map_metadata", "-1"]},
    "ogv": {"label": "OGV (Theora + Vorbis)", "group": "Abertos",
            "params": ["-c:v", "libtheora", "-q:v", "7", "-c:a", "libvorbis", "-q:a", "5", "-map_metadata", "-1"]},
    "gif": {"label": "GIF animado (480p @15fps)", "group": "Criativos",
            "params": ["-vf", "fps=15,scale=480:-2:flags=lanczos", "-loop", "0", "-an", "-f", "gif", "-map_metadata", "-1"]},
    "mkv_lossless": {"label": "MKV (FFV1 + FLAC)", "group": "Arquivamento", "extension": "mkv",
                     "params": ["-c:v", "ffv1", "-level", "3", "-coder", "1", "-context", "1", "-g", "1", "-slicecrc", "1", "-c:a", "flac", "-compression_level", "12", "-map_metadata", "-1"]},
    "mov_prores": {"label": "MOV (ProRes 422 HQ)", "group": "Profissional", "extension": "mov",
                   "params": ["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-vendor", "appl", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", "-map_metadata", "-1"]},
    "f4v": {"label": "F4V (H.264 + AAC)", "group": "Streaming",
            "params": ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-map_metadata", "-1"]},
    "vob": {"label": "VOB (MPEG-2 + AC3)", "group": "Legados",
            "params": ["-c:v", "mpeg2video", "-qscale:v", "5", "-c:a", "ac3", "-b:a", "192k", "-f", "vob", "-map_metadata", "-1"]},
    "dv": {"label": "DV (DVCPRO)", "group": "Profissional",
           "params": ["-c:v", "dvvideo", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", "-map_metadata", "-1"]},
}

_GROUP_ORDER = [
    "Modernos", "Alta eficiência", "Compatibilidade", "Streaming", "Mobile",
    "Abertos", "Legados", "Profissional", "Broadcast", "Arquivamento", "Criativos",
]
_grouped: dict[str, list[tuple[str, str]]] = {}
for _key, _cfg in _FORMATS.items():
    _grouped.setdefault(_cfg["group"], []).append((_key, _cfg["label"]))
OUTPUT_FORMAT_GROUPS = [
    (g, sorted(_grouped[g], key=lambda i: i[0])) for g in _GROUP_ORDER if g in _grouped
]


def convert(input_path: Path, output_format: str, output_dir: Path) -> list[Path]:
    fmt = output_format.lower()
    if fmt not in _FORMATS:
        raise ValueError("Formato de saída inválido.")
    cfg = _FORMATS[fmt]
    ext = cfg.get("extension", fmt)
    output_path = unique_output_path(output_dir, input_path.stem, ext)
    run_ffmpeg(input_path, cfg["params"], output_path, timeout=FFMPEG_TIMEOUT_SECONDS)
    return [output_path]
