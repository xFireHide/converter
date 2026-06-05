"""Conversão de PDF para imagens (PNG/JPG/WEBP) ou Word (DOCX)."""
from __future__ import annotations

import io
from pathlib import Path

import fitz  # PyMuPDF

from .common import unique_output_path

NAME = "PDF"
DEFAULT_DPI = 144

INPUT_EXTENSIONS = {"pdf"}

OUTPUT_FORMAT_GROUPS = [
    (
        "Imagem (uma por página)",
        [
            ("png", "PNG"),
            ("jpg", "JPEG (JPG)"),
            ("webp", "WEBP"),
        ],
    ),
    (
        "Documento",
        [
            ("docx", "Word (DOCX)"),
        ],
    ),
]

_IMAGE_FORMATS = {"png", "jpg", "jpeg", "webp"}


def convert(input_path: Path, output_format: str, output_dir: Path, dpi: int = DEFAULT_DPI) -> list[Path]:
    fmt = output_format.lower()
    if fmt in _IMAGE_FORMATS:
        return _pdf_to_images(input_path, fmt, output_dir, dpi)
    if fmt == "docx":
        return [_pdf_to_docx(input_path, output_dir)]
    raise ValueError("Formato de saída não suportado.")


def _pdf_to_images(pdf_path: Path, fmt: str, output_dir: Path, dpi: int) -> list[Path]:
    from PIL import Image

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    outputs: list[Path] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    with fitz.open(pdf_path) as doc:
        page_count = doc.page_count
        width = max(3, len(str(page_count)))
        for index, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("ppm"))).convert("RGB")
            stem = f"{pdf_path.stem}_{index:0{width}d}"
            if fmt == "png":
                out = unique_output_path(output_dir, stem, "png")
                img.save(out, format="PNG")
            elif fmt in {"jpg", "jpeg"}:
                out = unique_output_path(output_dir, stem, "jpg")
                img.save(out, format="JPEG", quality=92)
            else:  # webp
                out = unique_output_path(output_dir, stem, "webp")
                img.save(out, format="WEBP", quality=90)
            outputs.append(out)
    return outputs


def _pdf_to_docx(pdf_path: Path, output_dir: Path) -> Path:
    from pdf2docx import Converter

    output_path = unique_output_path(output_dir, pdf_path.stem, "docx")
    converter = Converter(str(pdf_path))
    try:
        converter.convert(str(output_path))
    finally:
        converter.close()
    return output_path
