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
import subprocess
import tempfile
import re
import uuid
import zipfile
from pytube import Playlist

bp = Blueprint(
    "youtube_subtitle_downloader",
    __name__,
    url_prefix="/youtube_subtitle_downloader",
)

# Configurações de segurança
MAX_VIDEOS = 50
# Aceita qualquer URL do YouTube para vídeo ou playlist
ALLOWED_YT_URL = re.compile(
    r"^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\/.*$"
)


def sanitize_url(url):
    """Limpa espaços e verifica se a URL parece ser do YouTube."""
    url = url.strip()
    if not ALLOWED_YT_URL.match(url):
        return None
    return url


@bp.route("/", methods=["GET", "POST"])
def index():
    legendas_baixadas = []
    download_link = None

    if request.method == "POST":
        yt_url = request.form.get("yt_url", "")
        url = sanitize_url(yt_url)
        if not url:
            flash("Por favor, forneça uma URL válida do YouTube.", "danger")
            return render_template(
                "youtube_subtitle_downloader/index.html",
                legendas_baixadas=[],
                download_link=None,
            )

        # Pasta temporária única por requisição
        tmp_dir = tempfile.mkdtemp(prefix="yt_legendas_")
        zip_path = os.path.join(tmp_dir, "legendas.zip")

        try:
            if "list=" in url:
                playlist = Playlist(url)
                video_urls = playlist.video_urls[:MAX_VIDEOS]
            else:
                video_urls = [url]
            if not video_urls:
                flash("Nenhum vídeo encontrado.", "danger")
                return render_template(
                    "youtube_subtitle_downloader/index.html",
                    legendas_baixadas=[],
                    download_link=None,
                )

            for idx, vurl in enumerate(video_urls):
                try:
                    # Baixar legenda automática com yt-dlp, idioma pt
                    subprocess.run(
                        [
                            "yt-dlp",
                            "--write-auto-sub",
                            "--sub-lang",
                            "pt",
                            "--skip-download",
                            "--output",
                            os.path.join(tmp_dir, "%(title)s.%(ext)s"),
                            vurl,
                        ],
                        check=True,
                        timeout=90,  # Limite de tempo por vídeo (segundos)
                        stdout=subprocess.DEVNULL,  # Não expõe saída
                        stderr=subprocess.DEVNULL,
                    )
@@ -99,43 +103,43 @@ def index():
            # Compacta as legendas para download
            legendas_files = [
                f
                for f in os.listdir(tmp_dir)
                if f.endswith(".vtt") or f.endswith(".srt")
            ]
            if legendas_files:
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for filename in legendas_files:
                        zipf.write(os.path.join(tmp_dir, filename), arcname=filename)
                # Gera um identificador para download
                download_token = str(uuid.uuid4())
                # Salva caminho do arquivo temporário usando o token (implementação básica)
                # Em produção, usar cache, banco ou armazenamento próprio (Redis, DB, etc)
                request.environ.setdefault("downloads", {})[download_token] = zip_path
                download_link = url_for(
                    "youtube_subtitle_downloader.download", token=download_token
                )
                flash(
                    f"Legendas baixadas de {len(legendas_baixadas)}/{len(video_urls)} vídeos.",
                    "success",
                )
            else:
                flash("Nenhuma legenda em português encontrada nos vídeos.", "warning")
        except Exception:
            flash("Ocorreu um erro inesperado ao processar o link.", "danger")
        # Limpeza do diretório temporário seria ideal após o download.
    return render_template(
        "youtube_subtitle_downloader/index.html",
        legendas_baixadas=legendas_baixadas,
        download_link=download_link,
    )


@bp.route("/download/<token>")
def download(token):
    downloads = request.environ.get("downloads", {})
    zip_path = downloads.get(token)
    if zip_path and os.path.exists(zip_path):
        # O nome do arquivo baixado será 'legendas.zip'
        return send_file(zip_path, as_attachment=True, download_name="legendas.zip")
    flash("Arquivo de download expirado ou inválido.", "danger")
    return redirect(url_for(".index"))
