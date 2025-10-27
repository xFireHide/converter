import io
import os
import uuid
from pathlib import Path

import fitz
from PIL import Image
from pdf2docx import Converter

from core.settings import settings
from core.storage import RetentionPolicy, cleanup_retention_policies, ensure_directory

CONVERTED_FOLDER = ensure_directory(settings.base_dir / "static" / "doc" / "pdf" / "converter" / "converted")
UPLOAD_FOLDER = ensure_directory(settings.base_dir / "uploads" / "pdf_converter")

FILE_RETENTION_SECONDS = settings.file_retention_seconds
IMAGE_FORMATS = {"png", "jpg", "jpeg", "webp"}
DOCUMENT_FORMATS = {"docx"}
SUPPORTED_FORMATS = IMAGE_FORMATS | DOCUMENT_FORMATS
DEFAULT_DPI = 144


def cleanup_old_files(retention_seconds: int = FILE_RETENTION_SECONDS) -> None:
    cleanup_retention_policies([
        RetentionPolicy(CONVERTED_FOLDER, retention_seconds),
        RetentionPolicy(UPLOAD_FOLDER, retention_seconds),
    ])


def save_upload(file_storage) -> Path:
    extension = Path(file_storage.filename or "").suffix.lower() or ".pdf"
    filename = f"{uuid.uuid4().hex}{extension}"
    destination = (UPLOAD_FOLDER / filename).resolve()
    if destination.parent != UPLOAD_FOLDER:
        raise ValueError("Caminho de upload inválido.")
    file_storage.save(destination)
    return destination


def convert_pdf(pdf_path: Path, target_format: str, dpi: int = DEFAULT_DPI) -> list[str]:
    if target_format not in SUPPORTED_FORMATS:
        raise ValueError("Formato de saída não suportado.")

    if target_format in IMAGE_FORMATS:
        return _convert_pdf_to_images(pdf_path, target_format, dpi)

    if target_format == "docx":
        output_name = _convert_pdf_to_docx(pdf_path)
        return [output_name]

    raise ValueError("Formato de saída não suportado.")


def _convert_pdf_to_images(pdf_path: Path, target_format: str, dpi: int) -> list[str]:
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    filenames: list[str] = []
    with fitz.open(pdf_path) as doc:
        for index, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("ppm"))).convert("RGB")
            if target_format == "png":
                output_name = f"{uuid.uuid4().hex}_{index:03d}.png"
                output_path = CONVERTED_FOLDER / output_name
                img.save(output_path, format="PNG")
            elif target_format in {"jpg", "jpeg"}:
                output_name = f"{uuid.uuid4().hex}_{index:03d}.jpg"
                output_path = CONVERTED_FOLDER / output_name
                img.save(output_path, format="JPEG", quality=92)
            else:  # webp
                output_name = f"{uuid.uuid4().hex}_{index:03d}.webp"
                output_path = CONVERTED_FOLDER / output_name
                img.save(output_path, format="WEBP", quality=90)
            filenames.append(output_name)
    return filenames


def _convert_pdf_to_docx(pdf_path: Path) -> str:
    output_name = f"{uuid.uuid4().hex}.docx"
    output_path = CONVERTED_FOLDER / output_name
    converter = Converter(str(pdf_path))
    try:
        converter.convert(str(output_path))
    finally:
        converter.close()
    return output_name
