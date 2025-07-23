from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from PIL import Image
import os
import uuid

bp = Blueprint("image_converter", __name__, url_prefix="/image_converter")

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


@bp.route("/", methods=["GET", "POST"])
def index():
    images = []
    if request.method == "POST":
        files = request.files.getlist("images")
        if not files or files == [None]:
            flash("No files were uploaded.", "danger")
            return redirect(request.url)
        for file in files:
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit(".", 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{ext}"
                filepath = os.path.join(UPLOAD_FOLDER, secure_filename(unique_filename))
                file.save(filepath)
                if validate_image(filepath):
                    images.append(unique_filename)
                else:
                    os.remove(filepath)
        if not images:
            flash("No valid images were uploaded.", "danger")
        else:
            flash(f"{len(images)} image(s) uploaded successfully!", "success")
    return render_template("image_converter/index.html", images=images)
