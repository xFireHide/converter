from pathlib import Path
import uuid

from flask import Blueprint, current_app, jsonify, request, url_for

from .service import (
    MAX_FILE_SIZE_MB,
    MAX_FILE_SIZE_BYTES,
    OUTPUT_FORMAT_GROUPS,
    SUPPORTED_OUTPUT_FORMATS,
    UPLOAD_FOLDER,
    allowed_file,
    cleanup_old_files,
    convert_image,
    validate_image,
)

bp = Blueprint("image_converter", __name__, url_prefix="/api/image")

def _save_upload(file_storage, destination: Path) -> None:
    """Persist the uploaded file and enforce size limits."""
    file_storage.save(str(destination))
    if destination.stat().st_size > MAX_FILE_SIZE_BYTES:
        destination.unlink(missing_ok=True)
        raise ValueError(
            f"Arquivo excede o limite de {MAX_FILE_SIZE_MB} MB. "
            "Envie uma imagem menor."
        )


@bp.post("/convert")
def convert():
    cleanup_old_files()
    files = request.files.getlist("images")
    target_format = (request.form.get("target_format") or request.args.get("target_format") or "").lower()
    if target_format not in SUPPORTED_OUTPUT_FORMATS:
        return jsonify({"status": "error", "message": "Formato de saída inválido."}), 400
    if not files:
        return jsonify({"status": "error", "message": "Nenhum arquivo foi enviado."}), 400

    upload_root = UPLOAD_FOLDER.resolve()
    converted = []
    errors = []
    for file in files:
        if not file or not file.filename:
            continue
        if not allowed_file(file.filename):
            errors.append({"file": file.filename, "message": "Extensão não permitida."})
            continue

        ext = file.filename.rsplit(".", 1)[1].lower()
        tmp_name = f"{uuid.uuid4().hex}.{ext}"
        tmp_path = (UPLOAD_FOLDER / tmp_name).resolve()
        if tmp_path.parent != upload_root:
            errors.append({"file": file.filename, "message": "Caminho de upload inválido."})
            continue

        try:
            _save_upload(file, tmp_path)
        except ValueError as exc:
            errors.append({"file": file.filename, "message": str(exc)})
            continue
        except Exception as exc:  # pragma: no cover - log unexpected issues
            current_app.logger.exception("Falha ao salvar upload: %s", exc)
            errors.append({"file": file.filename, "message": "Erro ao salvar o arquivo."})
            tmp_path.unlink(missing_ok=True)
            continue

        try:
            if not validate_image(tmp_path):
                errors.append({"file": file.filename, "message": "Arquivo inválido ou potencialmente malicioso."})
                continue
            conv_name = convert_image(tmp_path, target_format)
            download_url = url_for(
                "static",
                filename=f"image/converter/uploads/{conv_name}",
                _external=True,
            )
            converted.append({"file": conv_name, "url": download_url})
        except RuntimeError as exc:
            errors.append({"file": file.filename, "message": str(exc)})
        except Exception as exc:  # pragma: no cover - log unexpected issues
            current_app.logger.exception("Erro ao converter imagem: %s", exc)
            errors.append({"file": file.filename, "message": "Erro inesperado ao converter."})
        finally:
            tmp_path.unlink(missing_ok=True)

    if not converted:
        return jsonify({"status": "error", "errors": errors or "Falha ao converter arquivos."}), 400

    file_names = [item["file"] for item in converted]
    result_url = url_for(
        "image_converter_result",
        files=",".join(file_names),
        target=target_format,
        _external=True,
    )

    return jsonify({
        "status": "success",
        "target_format": target_format,
        "converted": converted,
        "errors": errors,
        "result_url": result_url,
    })
