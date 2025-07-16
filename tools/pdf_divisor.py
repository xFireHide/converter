import os
from flask import Blueprint, render_template, request, redirect, url_for
from tools.pdf_processor import process_pdf

bp = Blueprint("pdf_divisor", __name__, url_prefix="/divisorpdf")

BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)


@bp.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        pdf = request.files.get("pdf")
        if not pdf or not pdf.filename.lower().endswith(".pdf"):
            error = "Selecione um arquivo PDF válido."
            return render_template("pdf_divisor.html", error=error)

        filename = pdf.filename
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        pdf.save(input_path)

        output_path = os.path.join(
            PROCESSED_FOLDER, f"{os.path.splitext(filename)[0]}_processed.pdf"
        )

        try:
            process_pdf(input_path, output_path)
            out_filename = os.path.basename(output_path)
            return redirect(url_for("pdf_divisor.download_page", filename=out_filename))
        except Exception as e:
            error = f"Erro ao processar o PDF: {e}"
            return render_template("pdf_divisor.html", error=error)

    return render_template("pdf_divisor.html", error=error)


@bp.route("/download/<filename>")
def download_page(filename):
    return render_template("result.html", filename=filename)
