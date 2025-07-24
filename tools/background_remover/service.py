import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
from rembg import remove

UPLOAD_FOLDER = "static/background_remover/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image(path: str) -> bool:
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def remove_background(input_path: str) -> str:
    with open(input_path, "rb") as inp:
        input_bytes = inp.read()
        output_bytes = remove(input_bytes)
    output_filename = f"{uuid.uuid4().hex}.png"
    output_path = os.path.join(UPLOAD_FOLDER, secure_filename(output_filename))
    with open(output_path, "wb") as out:
        out.write(output_bytes)
    return output_filename
