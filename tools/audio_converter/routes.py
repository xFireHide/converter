from flask import Blueprint, render_template, request, redirect, url_for, flash
import os

from .service import is_allowed, save_audio, convert_audio

bp = Blueprint("audio_converter", __name__, url_prefix="/audio_converter")


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("audio")
        output_format = request.form.get("output_format", "").lower()
        if not file or not is_allowed(file.filename):
            flash("Arquivo de áudio inválido.", "danger")
            return redirect(request.url)
        if not output_format:
            flash("Formato de saída não informado.", "danger")
            return redirect(request.url)
        input_path = save_audio(file)
        try:
            filename = convert_audio(input_path, output_format)
            flash("Áudio convertido com sucesso!", "success")
            return redirect(url_for("audio_converter.result_page", filename=filename))
        except Exception as e:
            flash("Erro ao converter o áudio.", "danger")
            print(e)
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
    return render_template("audio_converter/index.html")


@bp.route("/result/<filename>")
def result_page(filename):
    return render_template("audio_converter/result.html", filename=filename)
