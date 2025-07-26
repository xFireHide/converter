from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import uuid

from .service import (
    UPLOAD_FOLDER,
    allowed_file,
    validate_image,
    remove_background,
)

bp = Blueprint("background_remover", __name__, url_prefix="/background_remover")


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("image")
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            tmp_name = f"{uuid.uuid4().hex}.{ext}"
            tmp_path = os.path.join(UPLOAD_FOLDER, secure_filename(tmp_name))
            file.save(tmp_path)
            if validate_image(tmp_path):
                try:
                    out_file = remove_background(tmp_path)
                    flash("Fundo removido com sucesso!", "success")
                    return redirect(
                        url_for("background_remover.result_page", filename=out_file)
                    )
                except Exception as e:
                    print(e)
                    flash("Erro ao processar a imagem.", "danger")
                finally:
                    os.remove(tmp_path)
            else:
                os.remove(tmp_path)
                flash("Arquivo de imagem inválido.", "danger")

    return render_template("background_remover/index.html")


@bp.route("/result/<filename>")
def result_page(filename):
    return render_template("background_remover/result.html", filename=filename)
