import os
from flask import Blueprint, render_template, request, redirect, url_for
from pdf_processor import process_pdf

# Blueprint para o divisor de PDF
bp = Blueprint("pdf_divisor", __name__, url_prefix="/divisorpdf")

# Diretórios de upload e processados (compartilhados com app)
BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed")

# Garante que as pastas existam
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)


@bp.route("/", methods=["GET", "POST"])
def index():
    """
    Página do divisor de PDF: upload e processamento.
    """
    error = None
    if request.method == "POST":
        # Valida e salva o PDF enviado
        pdf = request.files.get("pdf")
        if not pdf or not pdf.filename.lower().endswith(".pdf"):
            error = "Selecione um arquivo PDF válido."
            return render_template("pdf_divisor.html", error=error)

        filename = pdf.filename
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        pdf.save(input_path)

        try:
            # Processa o PDF; se output_path não for passado, usa padrão
            output_path = process_pdf(input_path)
            out_filename = os.path.basename(output_path)
            # Redireciona para página de download
            return redirect(url_for("pdf_divisor.download_page", filename=out_filename))
        except Exception as e:
            error = f"Erro ao processar o PDF: {e}"
            return render_template("pdf_divisor.html", error=error)

    # GET ou erro
    return render_template("pdf_divisor.html", error=error)


@bp.route("/download/<filename>")
def download_page(filename):
    """
    Página de resultado com link para baixar o PDF gerado.
    """
    return render_template("result.html", filename=filename)
