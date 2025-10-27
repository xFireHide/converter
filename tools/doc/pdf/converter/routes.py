from pathlib import Path
from flask import Blueprint, current_app, jsonify, request, url_for

from .service import (
    SUPPORTED_FORMATS,
    cleanup_old_files,
    convert_pdf,
    save_upload,
)

bp = Blueprint("pdf_converter", __name__, url_prefix="/api/doc/pdf")


@bp.post("/convert")
def convert():
    cleanup_old_files()
    file = request.files.get("pdf")
    target_format = (request.form.get("target_format") or request.args.get("target_format") or "png").lower()

    if not file or not file.filename:
        return jsonify({"status": "error", "message": "Nenhum arquivo PDF enviado."}), 400

    if target_format not in SUPPORTED_FORMATS:
        return jsonify({"status": "error", "message": "Formato de imagem não suportado."}), 400

    saved_path: Path | None = None
    try:
        saved_path = save_upload(file)
        filenames = convert_pdf(saved_path, target_format)
        downloads = [
            {
                "file": name,
                "url": url_for("static", filename=f"doc/pdf/converter/converted/{name}", _external=True),
            }
            for name in filenames
        ]
        result_url = url_for(
            "pdf_to_image_result",
            files=",".join(filenames),
            format=target_format,
        )
        return jsonify({
            "status": "success",
            "target_format": target_format,
            "converted": downloads,
            "page_count": len(downloads),
            "result_url": result_url,
            "files": filenames,
        })
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - fallback log
        current_app.logger.exception("Erro ao converter PDF em imagens: %s", exc)
        return jsonify({"status": "error", "message": "Falha ao converter o PDF."}), 500
    finally:
        if saved_path is not None:
            saved_path.unlink(missing_ok=True)
