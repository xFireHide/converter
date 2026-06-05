"""Conversores de arquivos do FileConverter.

Cada módulo de conversor expõe a mesma interface:

- ``NAME``: rótulo legível (ex.: "Imagem").
- ``INPUT_EXTENSIONS``: conjunto de extensões de entrada aceitas (sem ponto).
- ``OUTPUT_FORMAT_GROUPS``: lista de ``(grupo, [(valor, rótulo), ...])``.
- ``convert(input_path, output_format, output_dir) -> list[Path]``: converte e
  retorna os caminhos gerados.
"""
from __future__ import annotations

from . import audio, image, pdf, video

# Ordem de exibição na interface.
CONVERTERS = {
    image.NAME: image,
    audio.NAME: audio,
    video.NAME: video,
    pdf.NAME: pdf,
}

__all__ = ["CONVERTERS", "image", "audio", "video", "pdf"]
