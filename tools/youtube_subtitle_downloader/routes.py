from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
)
import os
import uuid

from .service import (
    sanitize_url,
    process_url,
    get_video_urls,
    get_available_languages,
)

bp = Blueprint(
    "youtube_subtitle_downloader",
    __name__,
    url_prefix="/youtube_subtitle_downloader",
)


@bp.route("/", methods=["GET", "POST"])
def index():
    legendas_baixadas = []
    download_link = None
    languages = []
    yt_url = ""

    if request.method == "POST":
        yt_url = request.form.get("yt_url", "")
        selected_lang = request.form.get("lang")
        url = sanitize_url(yt_url)
        if not url:
            flash("Por favor, forneça uma URL válida do YouTube.", "danger")
            return render_template(
                "youtube_subtitle_downloader/index.html",
                legendas_baixadas=[],
                download_link=None,
                languages=[],
                yt_url=yt_url,
            )

        video_urls = get_video_urls(url)
        if not selected_lang:
            languages = get_available_languages(video_urls)
            if not languages:
                flash("Nenhuma legenda disponível nos vídeos.", "warning")
            return render_template(
                "youtube_subtitle_downloader/index.html",
                legendas_baixadas=[],
                download_link=None,
                languages=languages,
                yt_url=yt_url,
            )

        legendas_baixadas, zip_path, tmp_dir = process_url(url, selected_lang)
        try:
            if zip_path:
                download_token = str(uuid.uuid4())
                request.environ.setdefault("downloads", {})[download_token] = zip_path
                download_link = url_for(
                    "youtube_subtitle_downloader.download", token=download_token
                )
                flash(
                    f"Legendas baixadas de {len(legendas_baixadas)}/{len(legendas_baixadas)} vídeos.",
                    "success",
                )
            else:
                flash("Nenhuma legenda encontrada no idioma selecionado.", "warning")
        finally:
            pass

    return render_template(
        "youtube_subtitle_downloader/index.html",
        legendas_baixadas=legendas_baixadas,
        download_link=download_link,
        languages=languages,
        yt_url=yt_url,
    )


@bp.route("/download/<token>")
def download(token):
    downloads = request.environ.get("downloads", {})
    zip_path = downloads.get(token)
    if zip_path and os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True, download_name="legendas.zip")
    flash("Arquivo de download expirado ou inválido.", "danger")
    return redirect(url_for("youtube_subtitle_downloader.index"))
