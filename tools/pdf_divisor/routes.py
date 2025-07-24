from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    current_app,
    send_from_directory,
)
from .service import process_pdf
import os
import uuid
import fitz
from app import limiter


bp = Blueprint("pdf_divisor", __name__, url_prefix="/divisorpdf")


@bp.route("/", methods=["GET", "POST"])
@limiter.limit("100 per hour")
def index():
    error = None
    if request.method == "POST":
        pdf = request.files.get("pdf")
        # 1. Só aceita PDF por extensão
        if not pdf or not pdf.filename.lower().endswith(".pdf"):
            error = "Selecione um arquivo PDF válido."
            return render_template("pdf_divisor/index.html", error=error)

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        processed_folder = current_app.config["PROCESSED_FOLDER"]
        # 2. Gera nome aleatório
        filename = f"{uuid.uuid4()}.pdf"
        input_path = os.path.join(upload_folder, filename)
        pdf.save(input_path)

        # 3. Tenta abrir com fitz (PyMuPDF) para validar o arquivo
        try:
            with fitz.open(input_path) as doc:
                pass
        except Exception as e:
            # 4. Loga tentativa inválida e remove arquivo perigoso
            current_app.logger.warning(f"Upload inválido: {request.remote_addr} - {e}")
            error = "Arquivo PDF inválido ou corrompido."
            try:
                os.remove(input_path)
            except Exception:
                pass
            return render_template("pdf_divisor/index.html", error=error)

        try:
            out_filename = f"{uuid.uuid4()}_processed.pdf"
            output_path = os.path.join(processed_folder, out_filename)
            process_pdf(input_path, output_path)
            # Loga upload válido
            current_app.logger.info(f"Upload feito: {request.remote_addr} - {filename}")
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
