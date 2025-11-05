from flask import Blueprint, current_app, jsonify, request, url_for

from .service import ALLOWED_FORMATS, cleanup_old_files, download_media, validate_url

bp = Blueprint("video_downloader", __name__, url_prefix="/api/video")


@bp.post("/download")
def download():
    cleanup_old_files()

    data = request.get_json(silent=True) or {}
    url = (data.get("url") or request.form.get("url") or "").strip()
    target_format = (data.get("format") or request.form.get("format") or "mp4").lower()

    if target_format not in ALLOWED_FORMATS:
        return jsonify({"status": "error", "message": "Formato inválido. Escolha MP4 ou MP3."}), 400

    if not validate_url(url):
        return jsonify({"status": "error", "message": "Informe uma URL válida do YouTube."}), 400

    try:
        result = download_media(url, target_format)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:  # pragma: no cover
        current_app.logger.exception("Falha ao baixar mídia do YouTube")
        return jsonify({"status": "error", "message": "Erro inesperado ao baixar o conteúdo."}), 500

    file_url = url_for(
        "static",
        filename=f"video/downloader/downloads/{result.filename}",
        _external=True,
    )

    page_url = url_for(
        "video_downloader_result",
        filename=result.filename,
        title=result.title,
        _external=True,
    )

    return jsonify(
        {
            "status": "success",
            "file": result.filename,
            "download_url": file_url,
            "page_url": page_url,
            "title": result.title,
            "duration": result.duration,
            "format": target_format,
        }
    )

