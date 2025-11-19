import os
import uuid
from io import BytesIO
from pathlib import Path
from typing import List, Tuple

from core.settings import settings
from core.storage import RetentionPolicy, cleanup_retention_policies, ensure_directory
from PIL import Image, ImageFile, UnidentifiedImageError
from werkzeug.utils import secure_filename

# Plugins opcionais
try:
    import pillow_heif  # type: ignore

    pillow_heif.register_heif_opener()
except Exception:
    pillow_heif = None

try:
    import pillow_avif  # type: ignore  # plugin registra automaticamente
except Exception:
    pillow_avif = None

try:
    import cairosvg  # type: ignore
except Exception:
    cairosvg = None


UPLOAD_FOLDER = ensure_directory(settings.base_dir / "static" / "image" / "converter" / "uploads")

FILE_RETENTION_SECONDS = settings.file_retention_seconds
try:
    MAX_FILE_SIZE_MB = int(os.environ.get("IMAGE_MAX_FILE_SIZE_MB", "20"))
except (TypeError, ValueError):
    MAX_FILE_SIZE_MB = 20
else:
    if MAX_FILE_SIZE_MB <= 0:
        MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000

SUPPORTED_INPUT_EXTENSIONS = {
    "apng",
    "avif",
    "bmp",
    "cur",
    "dds",
    "eps",
    "fli",
    "flc",
    "gif",
    "hdr",
    "heic",
    "heif",
    "icns",
    "ico",
    "im",
    "j2k",
    "jp2",
    "jpg",
    "jpeg",
    "jfif",
    "pbm",
    "pcd",
    "pcx",
    "pgm",
    "png",
    "pnm",
    "psd",
    "sgi",
    "svg",
    "tga",
    "tif",
    "tiff",
    "webp",
    "xbm",
    "xpm",
}

OUTPUT_FORMAT_GROUPS: List[Tuple[str, List[Tuple[str, str]]]] = [
    (
        "Comuns",
        [
            ("png", "PNG"),
            ("jpg", "JPEG (JPG)"),
            ("webp", "WEBP"),
            ("gif", "GIF"),
            ("bmp", "BMP"),
        ],
    ),
    (
        "Avançados",
        [
            ("tiff", "TIFF"),
            ("ico", "ICO (multi-resolução)"),
            ("pdf", "PDF (uma imagem por página)"),
            ("avif", "AVIF (requer pillow-avif-plugin)"),
            ("heic", "HEIC (requer pillow-heif)"),
            ("jp2", "JPEG 2000 (JP2)"),
            ("j2k", "JPEG 2000 (J2K)"),
            ("tga", "TGA"),
            ("xpm", "XPM"),
            ("pcx", "PCX"),
            ("eps", "EPS"),
            ("icns", "ICNS (ícone macOS)"),
            ("hdr", "HDR (Radiance)"),
            ("sgi", "SGI (RGB)"),
            ("xbm", "XBM (bitmap X11)"),
        ],
    ),
    (
        "Formatos brutos",
        [
            ("ppm", "PPM"),
            ("pgm", "PGM"),
            ("pbm", "PBM"),
            ("pnm", "PNM"),
        ],
    ),
]

_supported_output_formats = {
    value for _, options in OUTPUT_FORMAT_GROUPS for value, _ in options
}
_supported_output_formats.update({"jpeg"})
SUPPORTED_OUTPUT_FORMATS = frozenset(_supported_output_formats)

ImageFile.LOAD_TRUNCATED_IMAGES = False
if Image.MAX_IMAGE_PIXELS is None or Image.MAX_IMAGE_PIXELS > MAX_IMAGE_PIXELS:
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def allowed_file(filename: str) -> bool:
    """Check for an allowed extension before touching the filesystem."""
    if not filename or "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in SUPPORTED_INPUT_EXTENSIONS


def cleanup_old_files(retention_seconds: int = FILE_RETENTION_SECONDS) -> None:
    """Remove converted files older than the configured retention period."""
    cleanup_retention_policies([RetentionPolicy(UPLOAD_FOLDER, retention_seconds)])


def validate_image(path: str | Path) -> bool:
    """Validate image integrity and guard against decompression bombs."""
    file_path = Path(path)
    try:
        if not file_path.exists() or not file_path.is_file():
            return False
        if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return False
    except OSError:
        return False

    extension = file_path.suffix.lower().lstrip(".")
    if extension == "svg":
        if cairosvg is None:
            return False
        try:
            _render_svg_to_png_bytes(file_path)
            return True
        except Exception:
            return False

    try:
        with Image.open(file_path) as img:
            img.verify()

        with Image.open(file_path) as img:
            img.load()
            width, height = img.size
            if width * height > MAX_IMAGE_PIXELS:
                return False
            detected_format = (img.format or "").lower()
            if detected_format and detected_format not in SUPPORTED_INPUT_EXTENSIONS:
                return False
        return True
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        return False


def _render_svg_to_png_bytes(path: Path) -> bytes:
    if cairosvg is None:
        raise RuntimeError("Para converter SVG, instale o pacote 'cairosvg'.")
    with path.open("rb") as svg_file:
        svg_data = svg_file.read(MAX_FILE_SIZE_BYTES + 1)
    if len(svg_data) > MAX_FILE_SIZE_BYTES:
        raise RuntimeError("Arquivo SVG excede o limite permitido.")
    return cairosvg.svg2png(
        bytestring=svg_data,
        url_fetcher=_reject_external_references,
    )


def _reject_external_references(url: str, *args, **kwargs):
    raise ValueError("Referências externas não são permitidas em arquivos SVG.")


def _open_image_with_fallback(path: Path) -> Image.Image:
    extension = path.suffix.lower().lstrip(".")
    if extension == "svg":
        png_bytes = _render_svg_to_png_bytes(path)
        return Image.open(BytesIO(png_bytes)).convert("RGBA")
    return Image.open(path)


def convert_image(input_path: str | Path, target_format: str) -> str:
    file_path = Path(input_path)
    fmt = target_format.lower()
    if fmt not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError("Formato de saída inválido.")

    try:
        with _open_image_with_fallback(file_path) as img:
            img.load()
            save_kwargs: dict = {}
            ext = fmt
            pillow_format = fmt.upper()

            if fmt in ("jpg", "jpeg"):
                pillow_format = "JPEG"
                ext = "jpg"
                img = img.convert("RGB")
                save_kwargs.update({"quality": 90, "optimize": True, "progressive": True})
            elif fmt == "png":
                pillow_format = "PNG"
                if img.mode == "P":
                    img = img.convert("RGBA")
                save_kwargs.update({"optimize": True})
            elif fmt == "webp":
                pillow_format = "WEBP"
                save_kwargs.update({"quality": 90, "method": 6})
            elif fmt == "gif":
                pillow_format = "GIF"
                if img.mode not in ("P", "L"):
                    img = img.convert("P", palette=Image.ADAPTIVE, colors=256)
            elif fmt == "bmp":
                pillow_format = "BMP"
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
            elif fmt in ("tif", "tiff"):
                pillow_format = "TIFF"
                ext = "tiff"
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
                save_kwargs.update({"compression": "tiff_lzw"})
            elif fmt == "ico":
                pillow_format = "ICO"
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                save_kwargs.update(
                    {"sizes": [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]}
                )
            elif fmt == "icns":
                pillow_format = "ICNS"
                ext = "icns"
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                save_kwargs.update(
                    {"sizes": [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256)]}
                )
            elif fmt == "pdf":
                pillow_format = "PDF"
                ext = "pdf"
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
            elif fmt in {"ppm", "pgm", "pbm", "pnm"}:
                pillow_format = "PPM"
                if fmt == "pgm":
                    img = img.convert("L")
                elif fmt == "pbm":
                    img = img.convert("1")
                else:
                    img = img.convert("RGB")
            elif fmt in ("jp2", "j2k"):
                pillow_format = "JPEG2000"
                ext = "jp2"
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
            elif fmt == "tga":
                pillow_format = "TGA"
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA")
            elif fmt == "heic":
                if pillow_heif is None:
                    raise RuntimeError("Para salvar HEIC, instale 'pillow-heif'.")
                pillow_format = "HEIF"
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
            elif fmt == "avif":
                if pillow_avif is None:
                    raise RuntimeError("Para salvar AVIF, instale 'pillow-avif-plugin'.")
                pillow_format = "AVIF"
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
                save_kwargs.update({"quality": 50})
            elif fmt == "xpm":
                pillow_format = "XPM"
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
            elif fmt == "pcx":
                pillow_format = "PCX"
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
            elif fmt == "eps":
                pillow_format = "EPS"
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
            elif fmt == "hdr":
                pillow_format = "HDR"
                ext = "hdr"
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
                elif img.mode == "RGBA":
                    img = img.convert("RGB")
            elif fmt == "sgi":
                pillow_format = "SGI"
                ext = "sgi"
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
            elif fmt == "xbm":
                pillow_format = "XBM"
                ext = "xbm"
                if img.mode != "1":
                    img = img.convert("1")
            else:
                pillow_format = fmt.upper()

            output_filename = secure_filename(f"{uuid.uuid4().hex}.{ext}")
            output_path = UPLOAD_FOLDER / output_filename
            img.save(output_path, pillow_format, **save_kwargs)
        return output_filename
    except (
        UnidentifiedImageError,
        Image.DecompressionBombError,
        OSError,
        ValueError,
        RuntimeError,
    ) as exc:
        raise RuntimeError(f"Falha ao converter: {exc}") from exc
