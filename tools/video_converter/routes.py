from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
import uuid

from .service import is_allowed, save_video, convert_video

bp = Blueprint("video_converter", __name__, url_prefix="/video_converter")


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("video")
        output_format = request.form.get("output_format", "").lower()
        if not file or not is_allowed(file.filename):
            flash("Arquivo de vídeo inválido.", "danger")
            return redirect(request.url)
        if not output_format:
            flash("Formato de saída não informado.", "danger")
            return redirect(request.url)
        input_path = save_video(file)
        try:
            filename = convert_video(input_path, output_format)
            flash("Vídeo convertido com sucesso!", "success")
            return redirect(url_for("video_converter.result_page", filename=filename))
        except Exception as e:
            flash("Erro ao converter o vídeo.", "danger")
            print(e)
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
    return render_template("video_converter/index.html")


@bp.route("/result/<filename>")
def result_page(filename):
    return render_template("video_converter/result.html", filename=filename)
