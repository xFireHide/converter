import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image

UPLOAD_FOLDER = "static/image_converter/uploads"
ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "bmp",
    "tiff",
    "tif",
    "ico",
    "ppm",
    "pgm",
    "pbm",
    "pnm",
    "svg",
    "dds",
    "heic",
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image(path):
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def convert_image(input_path, target_format):
    """Converte a imagem para o formato especificado."""
    with Image.open(input_path) as img:
        fmt = target_format.lower()
        if fmt in ("jpg", "jpeg"):
            img = img.convert("RGB")
            fmt = "JPEG"
            ext = "jpg"
        else:
            fmt = fmt.upper()
            ext = target_format.lower()
        output_filename = f"{uuid.uuid4().hex}.{ext}"
        output_path = os.path.join(UPLOAD_FOLDER, secure_filename(output_filename))
        img.save(output_path, fmt)
    return output_filename
