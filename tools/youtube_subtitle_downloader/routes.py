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
    cleanup_tmp_dir,
)

bp = Blueprint(
    "youtube_subtitle_downloader",
    __name__,
    url_prefix="/youtube_subtitle_downloader",
)

# Armazena dados temporários de cada download
# token -> {"zip_path": str, "tmp_dir": str, "urls": list[str]}
DOWNLOADS: dict[str, dict] = {}


@bp.route("/", methods=["GET", "POST"])
def index():
    legendas_baixadas = []
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
                languages=languages,
                yt_url=yt_url,
            )

        legendas_baixadas, zip_path, tmp_dir = process_url(url, selected_lang)
        if zip_path:
            download_token = str(uuid.uuid4())
            DOWNLOADS[download_token] = {
                "zip_path": zip_path,
                "tmp_dir": tmp_dir,
                "urls": legendas_baixadas,
                "total": len(video_urls),
            }
            flash(
                f"Legendas baixadas de {len(legendas_baixadas)}/{len(video_urls)} vídeos.",
                "success",
            )
            return redirect(
                url_for("youtube_subtitle_downloader.result_page", token=download_token)
            )
        else:
            cleanup_tmp_dir(tmp_dir)
            flash("Nenhuma legenda encontrada no idioma selecionado.", "warning")

    return render_template(
        "youtube_subtitle_downloader/index.html",
        legendas_baixadas=legendas_baixadas,
        languages=languages,
        yt_url=yt_url,
    )


@bp.route("/download/<token>")
def download(token):
    data = DOWNLOADS.pop(token, None)
    if data:
        zip_path = data.get("zip_path")
        tmp_dir = data.get("tmp_dir")
        if os.path.exists(zip_path):
            resp = send_file(zip_path, as_attachment=True, download_name="legendas.zip")
            cleanup_tmp_dir(tmp_dir)
            return resp
    flash("Arquivo de download expirado ou inválido.", "danger")
    return redirect(url_for("youtube_subtitle_downloader.index"))


@bp.route("/result/<token>")
def result_page(token):
    data = DOWNLOADS.get(token)
    if not data:
        flash("Arquivo de download expirado ou inválido.", "danger")
        return redirect(url_for("youtube_subtitle_downloader.index"))

    download_link = url_for("youtube_subtitle_downloader.download", token=token)
    legendas_baixadas = data.get("urls", [])
    total = data.get("total", len(legendas_baixadas))
    return render_template(
        "youtube_subtitle_downloader/result.html",
        legendas_baixadas=legendas_baixadas,
        download_link=download_link,
        total=total,
    )
