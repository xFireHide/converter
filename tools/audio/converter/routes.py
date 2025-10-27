from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, url_for

from .service import (
    MAX_FILE_SIZE_MB,
    OUTPUT_FORMAT_GROUPS,
    SUPPORTED_OUTPUT_FORMATS,
    CONVERTED_FOLDER,
    allowed_file,
    cleanup_old_files,
    convert_audio,
    save_audio,
    validate_audio,
)

bp = Blueprint("audio_converter", __name__, url_prefix="/api/audio")


@bp.post("/convert")
def convert():
    cleanup_old_files()
    file = request.files.get("audio")
    output_format = (request.form.get("output_format") or request.args.get("to") or "").lower()

    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        return jsonify({"status": "error", "message": "Formato de saída inválido."}), 400

    if not file or not file.filename:
        return jsonify({"status": "error", "message": "Nenhum arquivo foi enviado."}), 400

    if not allowed_file(file.filename):
        return jsonify({"status": "error", "message": "Extensão de arquivo não permitida."}), 400

    saved_path: Path | None = None
    try:
        saved_path = save_audio(file)
        if not validate_audio(saved_path):
            return jsonify({"status": "error", "message": "Arquivo inválido ou potencialmente malicioso."}), 400
        filename = convert_audio(saved_path, output_format)
        result_url = url_for(
            "audio_converter_result",
            filename=filename,
            _external=True,
        )
        return jsonify({
            "status": "success",
            "target_format": output_format,
            "file": filename,
            "url": result_url,
        })
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:  # pragma: no cover
        current_app.logger.exception("Erro inesperado no conversor de áudio: %s", exc)
        return jsonify({"status": "error", "message": "Erro inesperado ao converter."}), 500
    finally:
        if saved_path is not None:
            saved_path.unlink(missing_ok=True)
