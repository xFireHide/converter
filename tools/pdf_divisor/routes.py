from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    current_app,
    send_from_directory,
)
from .pdf_divisor import process_pdf
import os

bp = Blueprint("pdf_divisor", __name__, url_prefix="/divisorpdf")


@bp.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        pdf = request.files.get("pdf")
        if not pdf or not pdf.filename.lower().endswith(".pdf"):
            error = "Selecione um arquivo PDF válido."
            return render_template("pdf_divisor/index.html", error=error)

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        processed_folder = current_app.config["PROCESSED_FOLDER"]
        filename = pdf.filename
        input_path = os.path.join(upload_folder, filename)
        pdf.save(input_path)

        try:
            out_filename = os.path.splitext(filename)[0] + "_processed.pdf"
            output_path = os.path.join(processed_folder, out_filename)
            process_pdf(input_path, output_path)
            return redirect(url_for("pdf_divisor.result_page", filename=out_filename))
        except Exception as e:
            error = f"Erro ao processar o PDF: {e}"
            return render_template("pdf_divisor/index.html", error=error)
    return render_template("pdf_divisor/index.html", error=error)


@bp.route("/result/<filename>")
def result_page(filename):
    return render_template("pdf_divisor/result.html", filename=filename)


@bp.route("/download/<filename>")
def download_file(filename):
    processed_folder = current_app.config["PROCESSED_FOLDER"]
    return send_from_directory(processed_folder, filename, as_attachment=True)
