"""Helpers compartilhados pelos conversores (saída de arquivos e ffmpeg)."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Sequence


def unique_output_path(output_dir: Path, stem: str, ext: str) -> Path:
    """Monta um caminho de saída em ``output_dir`` sem sobrescrever arquivos.

    Usa ``<stem>.<ext>`` e, em caso de colisão, ``<stem>_1.<ext>``, etc.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ext = ext.lstrip(".")
    candidate = output_dir / f"{stem}.{ext}"
    counter = 1
    while candidate.exists():
        candidate = output_dir / f"{stem}_{counter}.{ext}"
        counter += 1
    return candidate


def get_ffmpeg_exe() -> str:
    """Retorna o caminho do ffmpeg (imageio-ffmpeg empacotado ou do sistema)."""
    try:
        from imageio_ffmpeg import get_ffmpeg_exe as _bundled

        return _bundled()
    except Exception:
        return shutil.which("ffmpeg") or "ffmpeg"


def run_ffmpeg(
    input_path: Path,
    params: Sequence[str],
    output_path: Path,
    *,
    timeout: int,
    pre_input: Sequence[str] = (),
) -> None:
    """Executa o ffmpeg de ``input_path`` para ``output_path``.

    ``params`` são as opções de codificação; ``pre_input`` são opções aplicadas
    antes do ``-i`` (raramente necessárias). Levanta ``RuntimeError`` em falha.
    """
    cmd = [
        get_ffmpeg_exe(),
        "-y",
        *pre_input,
        "-i",
        str(input_path),
        *params,
        str(output_path),
    ]
    try:
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as exc:
        output_path.unlink(missing_ok=True)
        detail = ""
        if exc.stderr:
            detail = exc.stderr.decode("utf-8", "replace").strip().splitlines()[-1:]
            detail = detail[0] if detail else ""
        raise RuntimeError(
            f"Falha na conversão. Verifique se o arquivo é válido. {detail}".strip()
        ) from exc
    except subprocess.TimeoutExpired as exc:
        output_path.unlink(missing_ok=True)
        raise RuntimeError("Conversão excedeu o tempo máximo permitido.") from exc
