# tools/nova_funcionalidade/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
import subprocess
from pytube import Playlist

bp = Blueprint("nova_funcionalidade", __name__, url_prefix="/nova_funcionalidade")


@bp.route("/", methods=["GET", "POST"])
def index():
    msg = None
    legendas_baixadas = []

    if request.method == "POST":
        playlist_url = request.form.get("playlist_url", "").strip()
        if not playlist_url:
            flash("Por favor, cole o link da playlist.", "warning")
            return render_template(
                "nova_funcionalidade/index.html", legendas_baixadas=[]
            )

        output_dir = "legendas"
        os.makedirs(output_dir, exist_ok=True)
        try:
            playlist = Playlist(playlist_url)
            total_videos = len(playlist.video_urls)
            if total_videos == 0:
                flash("Nenhum vídeo encontrado na playlist.", "danger")
                return render_template(
                    "nova_funcionalidade/index.html", legendas_baixadas=[]
                )

            for url in playlist.video_urls:
                try:
                    subprocess.run(
                        [
                            "yt-dlp",
                            "--write-auto-sub",
                            "--sub-lang",
                            "pt",
                            "--skip-download",
                            "--output",
                            f"{output_dir}/%(title)s.%(ext)s",
                            url,
                        ],
                        check=True,
                        capture_output=True,
                    )
                    legendas_baixadas.append(url)
                except Exception as e:
                    print(f"Erro ao baixar legenda de {url}: {e}")
            flash(
                f"Legendas baixadas de {len(legendas_baixadas)}/{total_videos} vídeos.",
                "success",
            )
        except Exception as e:
            flash(f"Erro ao processar playlist: {e}", "danger")
    return render_template(
        "nova_funcionalidade/index.html", legendas_baixadas=legendas_baixadas
    )
