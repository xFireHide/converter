# tools/pdf_divisor/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from .pdf_divisor import process_pdf  # Certifique-se que esse import está correto!
import os

bp = Blueprint("pdf_divisor", __name__, url_prefix="/divisorpdf")


@bp.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        pdf = request.files.get("pdf")
        if not pdf or not pdf.filename.lower().endswith(".pdf"):
            error = "Selecione um arquivo PDF válido."
            return render_template("pdf_divisor.html", error=error)

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        processed_folder = current_app.config["PROCESSED_FOLDER"]
        filename = pdf.filename
        input_path = os.path.join(upload_folder, filename)
        pdf.save(input_path)

        try:
            output_path = process_pdf(input_path)
            out_filename = os.path.basename(output_path)
            return redirect(url_for("pdf_divisor.download_page", filename=out_filename))
        except Exception as e:
            error = f"Erro ao processar o PDF: {e}"
            return render_template("pdf_divisor.html", error=error)
    # GET ou erro
    return render_template("pdf_divisor.html", error=error)


@bp.route("/download/<filename>")
def download_page(filename):
    return render_template("result.html", filename=filename)
