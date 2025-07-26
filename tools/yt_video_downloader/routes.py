from flask import (
    Blueprint,
    render_template,
    request,
    send_from_directory,
    flash,
    redirect,
    url_for,
)
import logging
import os
import uuid
from urllib.error import HTTPError

from .service import handle_download

bp = Blueprint("yt_video_downloader", __name__, url_prefix="/yt_video_downloader")
DOWNLOAD_FOLDER = "static/yt_downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            flash("Por favor, insira o link do vídeo ou playlist.")
            return render_template("yt_video_downloader/index.html")

        try:
            # Cria pasta única para cada download
            folder_id = str(uuid.uuid4())
            folder_path = os.path.join(DOWNLOAD_FOLDER, folder_id)
            os.makedirs(folder_path, exist_ok=True)
            downloaded_files = handle_download(url, folder_path)
            if not downloaded_files:
                flash("Nenhum vídeo foi baixado.", "warning")
                return render_template("yt_video_downloader/index.html")

            # Exibe os links para download
            download_links = [
                url_for(".download_file", folder=folder_id, filename=f)
                for f in downloaded_files
            ]
            return render_template(
                "yt_video_downloader/index.html",
                download_links=download_links,
            )
        except HTTPError as e:
            logging.error(f"Erro HTTP ao baixar {url}: {e}")
            flash(
                "Não foi possível baixar o vídeo. Verifique o link e tente novamente.",
                "danger",
            )
            return render_template("yt_video_downloader/index.html")
        except Exception as e:
            logging.error(f"Erro inesperado ao baixar {url}: {e}")
            flash(
                "Ocorreu um erro ao processar sua solicitação.",
                "danger",
            )
            return render_template("yt_video_downloader/index.html")
    return render_template("yt_video_downloader/index.html")


@bp.route("/download/<folder>/<filename>")
def download_file(folder, filename):
    folder_path = os.path.join(DOWNLOAD_FOLDER, folder)
    return send_from_directory(folder_path, filename, as_attachment=True)
