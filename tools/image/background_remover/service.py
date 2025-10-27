import io
import os
import uuid
from pathlib import Path

from core.settings import settings
from core.storage import RetentionPolicy, cleanup_retention_policies, ensure_directory
from PIL import (
    Image,
    ImageChops,
    ImageFile,
    ImageFilter,
    ImageOps,
    UnidentifiedImageError,
)
try:
    import numpy as np
    from scipy.ndimage import binary_closing, binary_dilation
except Exception:  # pragma: no cover - dependências opcionais
    np = None
    binary_dilation = binary_closing = None
from rembg import remove, new_session
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = ensure_directory(settings.base_dir / "static" / "image" / "background_remover" / "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}
FILE_RETENTION_SECONDS = settings.file_retention_seconds
try:
    MAX_FILE_SIZE_MB = int(os.environ.get("BACKGROUND_MAX_FILE_SIZE_MB", "20"))
except (TypeError, ValueError):
    MAX_FILE_SIZE_MB = 20
else:
    if MAX_FILE_SIZE_MB <= 0:
        MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000

ImageFile.LOAD_TRUNCATED_IMAGES = False
if Image.MAX_IMAGE_PIXELS is None or Image.MAX_IMAGE_PIXELS > MAX_IMAGE_PIXELS:
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

_SESSIONS: dict[str, object] = {}


def _get_session(model_name: str = "isnet-general-use"):
    session = _SESSIONS.get(model_name)
    if session is None:
        session = new_session(model_name=model_name)
        _SESSIONS[model_name] = session
    return session


def cleanup_old_files(retention_seconds: int = FILE_RETENTION_SECONDS) -> None:
    cleanup_retention_policies([RetentionPolicy(UPLOAD_FOLDER, retention_seconds)])


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _verify_dimensions(img: Image.Image) -> bool:
    width, height = img.size
    return width * height <= MAX_IMAGE_PIXELS


def validate_image(path: str | Path) -> bool:
    file_path = Path(path)
    try:
        if not file_path.exists() or not file_path.is_file():
            return False
        if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return False
    except OSError:
        return False

    try:
        with Image.open(file_path) as img:
            img.verify()

        with Image.open(file_path) as img:
            img.load()
            if not _verify_dimensions(img):
                return False
        return True
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        return False


def _mask_coverage(mask: Image.Image) -> float:
    histogram = mask.histogram()
    total_pixels = mask.size[0] * mask.size[1]
    non_zero = total_pixels - histogram[0]
    return non_zero / float(total_pixels or 1)


def _refine_mask(mask: Image.Image) -> Image.Image:
    refined = mask.filter(ImageFilter.MaxFilter(size=7))
    refined = refined.filter(ImageFilter.MinFilter(size=3))
    refined = refined.filter(ImageFilter.MedianFilter(size=3))
    refined = refined.filter(ImageFilter.GaussianBlur(radius=1.4))
    refined = ImageOps.autocontrast(refined)
    refined = refined.point(lambda p: 0 if p < 4 else p)
    return refined


def _combine_masks(masks: list[Image.Image]) -> Image.Image:
    if not masks:
        raise ValueError("Nenhuma máscara disponível para combinar.")
    merged = masks[0].copy()
    for extra in masks[1:]:
        merged = ImageChops.lighter(merged, extra)
    merged = merged.filter(ImageFilter.MedianFilter(size=3))
    merged = merged.filter(ImageFilter.GaussianBlur(radius=0.6))
    return merged


def _expand_mask(mask: Image.Image, steps: int = 3) -> Image.Image:
    expanded = mask.copy()
    for _ in range(max(1, steps)):
        expanded = expanded.filter(ImageFilter.MaxFilter(size=5))
    expanded = expanded.filter(ImageFilter.GaussianBlur(radius=2.2))
    expanded = ImageOps.autocontrast(expanded)
    expanded = expanded.point(lambda p: 0 if p < 2 else min(255, int(p * 1.05)))
    return expanded


def _heal_mask(mask: Image.Image, radius: int = 5, iterations: int = 1) -> Image.Image:
    if np is None or binary_dilation is None:
        return mask
    arr = np.array(mask, dtype=np.uint8)
    bool_mask = arr > 0
    if not bool_mask.any():
        return mask

    structure = np.ones((radius, radius), dtype=bool)
    dilated = binary_dilation(bool_mask, structure=structure, iterations=iterations)
    closed = binary_closing(dilated, structure=structure, iterations=iterations)
    healed = np.where(closed, 255, arr)
    return Image.fromarray(healed.astype(np.uint8), mode="L")


def _bright_halo_mask(image: Image.Image) -> Image.Image:
    hsv = image.convert("HSV")
    h, s, v = hsv.split()

    luminance = image.convert("L")
    color_mask = s.point(lambda p: 255 if p <= 60 else 0)
    white_mask = luminance.point(lambda p: 255 if p >= 220 else 0)

    halo = ImageChops.lighter(color_mask, white_mask)
    halo = halo.filter(ImageFilter.GaussianBlur(radius=2.0))
    halo = ImageOps.autocontrast(halo)
    halo = halo.point(lambda p: 0 if p < 25 else p)
    halo = halo.filter(ImageFilter.MedianFilter(size=3))
    return halo


def _edge_emphasis(mask: Image.Image) -> Image.Image:
    expanded = mask.filter(ImageFilter.MaxFilter(size=5))
    eroded = mask.filter(ImageFilter.MinFilter(size=5))
    edge = ImageChops.subtract(expanded, eroded)
    edge = edge.filter(ImageFilter.GaussianBlur(radius=1.0))
    edge = ImageOps.autocontrast(edge)
    edge = edge.point(lambda p: 0 if p < 8 else p)
    return edge


def remove_background(input_path: str | Path) -> str:
    """Remove o fundo de uma imagem usando modelo rembg otimizado."""
    file_path = Path(input_path)

    with file_path.open("rb") as inp:
        input_bytes = inp.read(MAX_FILE_SIZE_BYTES + 1)
    if len(input_bytes) > MAX_FILE_SIZE_BYTES:
        raise RuntimeError(f"Arquivo excede o limite de {MAX_FILE_SIZE_MB} MB.")

    image = Image.open(io.BytesIO(input_bytes)).convert("RGBA")
    image = ImageOps.exif_transpose(image)

    attempt_configs = [
        {
            "model": "isnet-general-use",
            "alpha_matting": True,
            "alpha_matting_foreground_threshold": 250,
            "alpha_matting_background_threshold": 5,
            "alpha_matting_erode_size": 1,
        },
        {
            "model": "isnet-general-use",
            "alpha_matting": True,
            "alpha_matting_foreground_threshold": 240,
            "alpha_matting_background_threshold": 15,
            "alpha_matting_erode_size": 0,
        },
        {
            "model": "isnet-general-use",
            "alpha_matting": True,
            "alpha_matting_foreground_threshold": 230,
            "alpha_matting_background_threshold": 25,
            "alpha_matting_erode_size": 0,
        },
        {
            "model": "isnet-anime",
            "alpha_matting": False,
        },
    ]

    evaluated_masks: list[tuple[Image.Image, float]] = []

    for config in attempt_configs:
        config = config.copy()
        model = config.pop("model", "isnet-general-use")
        session = _get_session(model)
        try:
            mask_bytes = remove(
                input_bytes,
                session=session,
                only_mask=True,
                **config,
            )
        except Exception:
            continue

        mask = Image.open(io.BytesIO(mask_bytes)).convert("L")
        coverage = _mask_coverage(mask)

        if coverage <= 0.02:
            continue

        evaluated_masks.append((mask, coverage))

        if len(evaluated_masks) >= 2 and 0.12 <= coverage <= 0.98:
            break

    if not evaluated_masks:
        raise RuntimeError("Não foi possível gerar máscara confiável para a imagem.")

    evaluated_masks.sort(key=lambda item: item[1], reverse=True)
    selected_masks = [item[0] for item in evaluated_masks[:4]]
    merged_mask = _combine_masks(selected_masks)
    refined_mask = _refine_mask(merged_mask)

    halo_mask = _bright_halo_mask(image)
    edge_mask = _edge_emphasis(refined_mask)
    halo_detail = ImageChops.multiply(halo_mask, edge_mask)

    halo_boost = halo_detail.filter(ImageFilter.MaxFilter(size=7))
    halo_boost = halo_boost.filter(ImageFilter.GaussianBlur(radius=1.0))
    merged_with_halo = ImageChops.lighter(refined_mask, halo_boost)

    expanded_mask = _expand_mask(merged_with_halo, steps=4)
    safety_mask = refined_mask.filter(ImageFilter.MaxFilter(size=5))
    safety_mask = safety_mask.filter(ImageFilter.GaussianBlur(radius=0.8))

    combined_mask = ImageChops.lighter(merged_with_halo, expanded_mask)
    combined_mask = ImageChops.lighter(combined_mask, safety_mask)
    combined_mask = combined_mask.filter(ImageFilter.MedianFilter(size=3))
    combined_mask = combined_mask.point(lambda p: 0 if p < 2 else min(255, p))
    combined_mask = _heal_mask(combined_mask, radius=5, iterations=1)

    final_coverage = _mask_coverage(combined_mask)
    if final_coverage > 0.985:
        combined_mask = refined_mask

    image.putalpha(combined_mask)

    output_filename = secure_filename(f"{uuid.uuid4().hex}.png")
    output_path = (UPLOAD_FOLDER / output_filename).resolve()
    if output_path.parent != UPLOAD_FOLDER:
        raise RuntimeError("Destino de saída inválido.")
    image.save(str(output_path), "PNG")
    return output_filename
