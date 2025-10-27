import os
import uuid
from pathlib import Path

import fitz
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
    send_from_directory,
    url_for,
)
from app import limiter
from core.settings import settings
from core.storage import RetentionPolicy, cleanup_retention_policies

from .service import process_pdf


bp = Blueprint("pdf_divisor", __name__, url_prefix="/api/doc/pdf")

PDF_RETENTION_SECONDS = settings.file_retention_seconds


def _cleanup_pdf_folders() -> None:
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    processed_folder = Path(current_app.config["PROCESSED_FOLDER"])
    cleanup_retention_policies(
        [
            RetentionPolicy(upload_folder, PDF_RETENTION_SECONDS),
            RetentionPolicy(processed_folder, PDF_RETENTION_SECONDS),
        ]
    )


@bp.post("/divide")
@limiter.limit("100 per hour")
def divide():
    _cleanup_pdf_folders()
    pdf = request.files.get("pdf")
    if not pdf or not pdf.filename.lower().endswith(".pdf"):
        return jsonify({"status": "error", "message": "Selecione um arquivo PDF válido."}), 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    processed_folder = current_app.config["PROCESSED_FOLDER"]
    ext = ".pdf"
    filename = f"{uuid.uuid4()}{ext}"
    input_path = os.path.join(upload_folder, filename)
    pdf.save(input_path)
    try:
        with fitz.open(input_path) as doc:
            pass
    except Exception as e:
        current_app.logger.warning(f"Upload inválido: {request.remote_addr} - {e}")
        try:
            os.remove(input_path)
        except Exception:
            pass
        return jsonify({"status": "error", "message": "Arquivo PDF inválido ou corrompido."}), 400

    try:
        out_filename = f"{uuid.uuid4()}_processed.pdf"
        output_path = os.path.join(processed_folder, out_filename)
        process_pdf(input_path, output_path)
        current_app.logger.info(f"Upload feito: {request.remote_addr} - {filename}")
        download_url = url_for("pdf_divisor.download_file", filename=out_filename, _external=True)
        return jsonify({
            "status": "success",
            "file": out_filename,
            "url": download_url,
        })
    except Exception as e:
        current_app.logger.exception("Erro ao processar o PDF")
        return jsonify({"status": "error", "message": f"Erro ao processar o PDF: {e}"}), 500
    finally:
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except Exception:
            current_app.logger.warning("Falha ao remover arquivo temporário de upload")


@bp.route("/download/<filename>")
def download_file(filename):
    _cleanup_pdf_folders()
    processed_folder = current_app.config["PROCESSED_FOLDER"]
    return send_from_directory(processed_folder, filename, as_attachment=True)
