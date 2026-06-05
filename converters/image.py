"""Conversão de imagens entre formatos usando Pillow."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageFile, UnidentifiedImageError

from .common import unique_output_path

# Plugins opcionais — habilitam formatos extras se estiverem instalados.
try:
    import pillow_heif  # type: ignore

    pillow_heif.register_heif_opener()
except Exception:  # noqa: BLE001
    pillow_heif = None

try:
    import pillow_avif  # type: ignore  # noqa: F401 — registra ao importar
except Exception:  # noqa: BLE001
    pillow_avif = None

try:
    import cairosvg  # type: ignore
except Exception:  # noqa: BLE001
    cairosvg = None

NAME = "Imagem"
MAX_IMAGE_PIXELS = 50_000_000

INPUT_EXTENSIONS = {
    "apng", "avif", "bmp", "cur", "dds", "eps", "fli", "flc", "gif", "hdr",
    "heic", "heif", "icns", "ico", "im", "j2k", "jp2", "jpg", "jpeg", "jfif",
    "pbm", "pcd", "pcx", "pgm", "png", "pnm", "psd", "sgi", "svg", "tga",
    "tif", "tiff", "webp", "xbm", "xpm",
}

OUTPUT_FORMAT_GROUPS = [
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

SUPPORTED_OUTPUT_FORMATS = {value for _, opts in OUTPUT_FORMAT_GROUPS for value, _ in opts} | {"jpeg"}

ImageFile.LOAD_TRUNCATED_IMAGES = False
if Image.MAX_IMAGE_PIXELS is None or Image.MAX_IMAGE_PIXELS > MAX_IMAGE_PIXELS:
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def _reject_external_references(url: str, *args, **kwargs):
    raise ValueError("Referências externas não são permitidas em arquivos SVG.")


def _render_svg_to_png_bytes(path: Path) -> bytes:
    if cairosvg is None:
        raise RuntimeError("Para converter SVG, instale o pacote 'cairosvg'.")
    return cairosvg.svg2png(
        bytestring=path.read_bytes(),
        url_fetcher=_reject_external_references,
    )


def _open_image(path: Path) -> Image.Image:
    if path.suffix.lower().lstrip(".") == "svg":
        return Image.open(BytesIO(_render_svg_to_png_bytes(path))).convert("RGBA")
    return Image.open(path)


def convert(input_path: Path, output_format: str, output_dir: Path) -> list[Path]:
    fmt = output_format.lower()
    if fmt not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError("Formato de saída inválido.")

    try:
        with _open_image(input_path) as img:
            img.load()
            save_kwargs: dict = {}
            ext = fmt
            pillow_format = fmt.upper()

            if fmt in ("jpg", "jpeg"):
                pillow_format, ext = "JPEG", "jpg"
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
                pillow_format, ext = "TIFF", "tiff"
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
                save_kwargs.update({"compression": "tiff_lzw"})
            elif fmt == "ico":
                pillow_format = "ICO"
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                save_kwargs.update({"sizes": [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]})
            elif fmt == "icns":
                pillow_format, ext = "ICNS", "icns"
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                save_kwargs.update({"sizes": [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256)]})
            elif fmt == "pdf":
                pillow_format, ext = "PDF", "pdf"
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
                pillow_format, ext = "JPEG2000", "jp2"
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
                pillow_format, ext = "HDR", "hdr"
                img = img.convert("RGB")
            elif fmt == "sgi":
                pillow_format, ext = "SGI", "sgi"
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
            elif fmt == "xbm":
                pillow_format, ext = "XBM", "xbm"
                if img.mode != "1":
                    img = img.convert("1")

            output_path = unique_output_path(output_dir, input_path.stem, ext)
            img.save(output_path, pillow_format, **save_kwargs)
        return [output_path]
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError, RuntimeError) as exc:
        raise RuntimeError(f"Falha ao converter: {exc}") from exc
