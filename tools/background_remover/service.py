import os
import uuid
import io
from werkzeug.utils import secure_filename
from PIL import Image, ImageFilter
from rembg import remove, new_session

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
    """Remove the background from an image using a higher quality model."""
    with open(input_path, "rb") as inp:
        input_bytes = inp.read()

    # Use the more general IS-Net model with alpha matting to reduce artifacts
    session = new_session(model_name="isnet-general-use")
    output_bytes = remove(
        input_bytes,
        session=session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=5,
    )

    # refine the mask to avoid losing important details
    image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
    mask = image.split()[-1]
    mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    image.putalpha(mask)

    output_filename = f"{uuid.uuid4().hex}.png"
    output_path = os.path.join(UPLOAD_FOLDER, secure_filename(output_filename))
    image.save(output_path)
    return output_filename
