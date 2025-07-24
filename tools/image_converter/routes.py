from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import uuid
from .service import allowed_file, validate_image, convert_image, UPLOAD_FOLDER

bp = Blueprint("image_converter", __name__, url_prefix="/image_converter")

UPLOAD_FOLDER = "static/image_converter/uploads"


OUTPUT_FORMATS = {"png", "jpg", "jpeg", "webp", "gif", "bmp"}


@bp.route("/", methods=["GET", "POST"])
def index():
    images = []
    if request.method == "POST":
        files = request.files.getlist("images")
        target_format = request.form.get("target_format", "").lower()
        if target_format not in OUTPUT_FORMATS:
            flash("Formato de saída inválido.", "danger")
            return redirect(request.url)
        if not files or files == [None]:
            flash("No files were uploaded.", "danger")
            return redirect(request.url)
        for file in files:
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit(".", 1)[1].lower()
                tmp_name = f"{uuid.uuid4().hex}.{ext}"
                tmp_path = os.path.join(UPLOAD_FOLDER, secure_filename(tmp_name))
                file.save(tmp_path)
                if validate_image(tmp_path):
                    try:
                        conv_name = convert_image(tmp_path, target_format)
                        images.append(conv_name)
                    except Exception:
                        flash(f"Erro ao converter {file.filename}.", "danger")
                    finally:
                        os.remove(tmp_path)
                else:
                    os.remove(tmp_path)
        if not images:
            flash("No valid images were uploaded.", "danger")
            return redirect(request.url)
        flash(
            f"{len(images)} image(s) converted to {target_format.upper()} successfully!",
            "success",
        )
        return redirect(
            url_for("image_converter.result_page", filenames=",".join(images))
        )
    return render_template("image_converter/index.html")


@bp.route("/result")
def result_page():
    filenames = request.args.get("filenames", "")
    images = [f for f in filenames.split(",") if f]
    if not images:
        flash("Nenhuma imagem para exibir.", "danger")
        return redirect(url_for("image_converter.index"))
    return render_template("image_converter/result.html", images=images)
