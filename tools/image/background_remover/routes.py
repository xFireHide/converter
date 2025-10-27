import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, url_for
from werkzeug.utils import secure_filename

from .service import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    UPLOAD_FOLDER,
    allowed_file,
    cleanup_old_files,
    remove_background,
    validate_image,
)

bp = Blueprint("background_remover", __name__, url_prefix="/api/image")


@bp.post("/background/remove")
def remove():
    cleanup_old_files()
    upload_root = UPLOAD_FOLDER.resolve()
    file = request.files.get("image")
    if not file or not file.filename:
        return jsonify({"status": "error", "message": "Nenhuma imagem foi enviada."}), 400

    if not allowed_file(file.filename):
        return jsonify({"status": "error", "message": "Formato de arquivo não suportado."}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    tmp_name = f"{uuid.uuid4().hex}.{ext}"
    tmp_path = (UPLOAD_FOLDER / secure_filename(tmp_name)).resolve()
    if tmp_path.parent != upload_root:
        return jsonify({"status": "error", "message": "Caminho de upload inválido."}), 400

    file.save(str(tmp_path))
    if tmp_path.stat().st_size > MAX_FILE_SIZE_BYTES:
        tmp_path.unlink(missing_ok=True)
        return jsonify({"status": "error", "message": f"Arquivo excede o limite de {MAX_FILE_SIZE_MB} MB."}), 400

    if not validate_image(str(tmp_path)):
        tmp_path.unlink(missing_ok=True)
        return jsonify({"status": "error", "message": "Arquivo inválido ou corrompido."}), 400

    try:
        out_file = remove_background(str(tmp_path))
        result_url = url_for(
            "background_remover_result",
            filename=out_file,
            _external=True,
        )
        return jsonify({
            "status": "success",
            "file": out_file,
            "url": result_url,
        })
    except RuntimeError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:
        current_app.logger.exception("Erro ao processar imagem para remoção de fundo")
        return jsonify({"status": "error", "message": "Erro inesperado ao processar a imagem."}), 500
    finally:
        tmp_path.unlink(missing_ok=True)
