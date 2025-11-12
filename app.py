import importlib
import logging
import os
import secrets
from pathlib import Path
import click
from flask import (
    Flask,
    abort,
    current_app,
    flash,
    redirect,
    jsonify,
    render_template,
    request,
    Response,
    send_from_directory,
    session,
    url_for,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix
from core.settings import settings
from core.storage import RetentionPolicy, cleanup_retention_policies, ensure_directory
from tools.audio.converter.service import (
    ALLOWED_INPUT_EXTENSIONS as AUDIO_ALLOWED_INPUT_EXTENSIONS,
    MAX_FILE_SIZE_MB as AUDIO_MAX_FILE_SIZE_MB,
    OUTPUT_FORMAT_GROUPS as AUDIO_OUTPUT_FORMAT_GROUPS,
)
# Lazy import for background remover to speed up cold start
try:
    from tools.image.background_remover.service import (
        ALLOWED_EXTENSIONS as BACKGROUND_ALLOWED_EXTENSIONS,
        MAX_FILE_SIZE_MB as BACKGROUND_MAX_FILE_SIZE_MB,
    )
except ImportError:
    # Fallback if rembg is not available
    BACKGROUND_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
    BACKGROUND_MAX_FILE_SIZE_MB = 20
from tools.image.converter.service import (
    MAX_FILE_SIZE_MB as IMAGE_MAX_FILE_SIZE_MB,
    OUTPUT_FORMAT_GROUPS as IMAGE_OUTPUT_FORMAT_GROUPS,
)
from tools.video.converter.service import (
    ALLOWED_INPUT_EXTENSIONS as VIDEO_ALLOWED_INPUT_EXTENSIONS,
    MAX_FILE_SIZE_MB as VIDEO_MAX_FILE_SIZE_MB,
    OUTPUT_FORMAT_GROUPS as VIDEO_OUTPUT_FORMAT_GROUPS,
)
from tools.doc.pdf.converter.service import (
    CONVERTED_FOLDER as PDF_CONVERTER_OUTPUTS,
    IMAGE_FORMATS as PDF_IMAGE_FORMATS,
    SUPPORTED_FORMATS as PDF_SUPPORTED_FORMATS,
)
from tools.url.shortener.service import (
    get_click_count as url_shortener_get_click_count,
    get_url_details as url_shortener_get_url_details,
    init_db as url_shortener_init_db,
    shorten_url as url_shortener_shorten_url,
    validate_custom_code as url_shortener_validate_custom_code,
)

# --- Configuração do App ---
app = Flask(__name__)
# Only enable debug in development
app.config['DEBUG'] = os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes")
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

app.config.update(
    MAX_CONTENT_LENGTH=settings.max_upload_mb * 1024 * 1024,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# Respeita cabeçalhos de proxy (X-Forwarded-*) quando atrás de um proxy/reverso
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# Diretórios essenciais
BASE_DIR = settings.base_dir
LOGS_DIR = ensure_directory(settings.logs_dir)

UPLOAD_FOLDER = ensure_directory(settings.uploads_dir)
PROCESSED_FOLDER = ensure_directory(settings.processed_dir)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["PROCESSED_FOLDER"] = str(PROCESSED_FOLDER)

IMAGE_CONVERTER_UPLOADS = (settings.base_dir / "static" / "image" / "converter" / "uploads").resolve()
AUDIO_CONVERTER_OUTPUTS = (settings.base_dir / "static" / "audio" / "converter" / "converted").resolve()
VIDEO_CONVERTER_OUTPUTS = (settings.base_dir / "static" / "video" / "converter" / "converted").resolve()
BACKGROUND_REMOVER_OUTPUTS = (settings.base_dir / "static" / "image" / "background_remover" / "uploads").resolve()

# Configuração dos Logs
# Use stderr for Cloud Run compatibility
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),  # Use stderr/stdout instead of file
    ]
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)
storage_uri = os.environ.get("RATELIMIT_STORAGE_URI")
if storage_uri:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["50 per hour"],
        storage_uri=storage_uri,
    )
else:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["50 per hour"],
    )
limiter.init_app(app)

# --- Carregamento dinâmico dos Blueprints ---
TOOLS_DIR = Path(BASE_DIR) / "tools"
if TOOLS_DIR.is_dir():
    for routes_path in sorted(TOOLS_DIR.rglob("routes.py")):
        relative = routes_path.with_suffix("").relative_to(BASE_DIR)
        module_path = ".".join(relative.parts)
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, "bp"):
                app.register_blueprint(module.bp)
                logging.info("Blueprint registrada: %s (%s)", module.bp.name, module_path)
        except ModuleNotFoundError as e:
            logging.warning("Blueprint não encontrado: %s - %s", module_path, e)

url_shortener_init_db()

# Log successful startup
logging.info("FireTools application initialized successfully")
logging.info("All blueprints loaded and registered")
logging.info("Optional imports handled gracefully")

# --- Rotas principais ---
def _generate_csrf_token() -> str:
    """Store a CSRF token in the session for template usage."""
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_hex(16)
        session["_csrf_token"] = token
    return token


def _remember_short_code(code: str) -> None:
    history = session.get("shortener_codes", []) or []
    if code in history:
        history.remove(code)
    history.insert(0, code)
    session["shortener_codes"] = history[:20]


@app.route("/health")
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({"status": "healthy", "service": "firetools"})


@app.route("/ads.txt")
def ads_txt():
    """Serve ads.txt for Google AdSense verification"""
    return send_from_directory(".", "ads.txt", mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    """Serve sitemap.xml for search engine indexing"""
    from datetime import datetime
    
    base_url = request.url_root.rstrip('/')
    if not base_url.startswith('http'):
        # Fallback if we can't determine the scheme
        base_url = 'https://firetools.site'
    
    sitemap_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{base_url}/pdf_divisor/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/pdf_to_image/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/image_converter/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/video_converter/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/audio_converter/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/background_remover/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/url_shortener/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{base_url}/privacy</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
  <url>
    <loc>{base_url}/terms</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>'''
    
    return Response(sitemap_content, mimetype='application/xml')


@app.route("/robots.txt")
def robots():
    """Serve robots.txt for search engine crawlers"""
    robots_path = Path(app.root_path) / "robots.txt"
    if not robots_path.exists():
        abort(404)
    return send_from_directory(str(robots_path.parent), robots_path.name, mimetype="text/plain")


@app.route("/")
def home():
    meta = {
        "title": "FireTools - Ferramentas Online",
        "description": "Conversores gratuitos de PDF, imagem, áudio, vídeo e removedor de fundo.",
        "keywords": "ferramentas online, conversor pdf, conversor imagem, conversor video",
    }
    return render_template("home.html", meta=meta)

# --- Rotas para Templates ---
@app.route("/pdf_divisor/")
def pdf_divisor_index():
    meta = {
        "title": "Divisor de PDF - FireTools",
        "description": "Divida páginas de PDF em quadrantes menores de forma rápida e segura.",
        "keywords": "dividir pdf, pdf quadrantes",
    }
    return render_template("doc/pdf/divisor/index.html", meta=meta)


@app.route("/pdf_divisor/result/<path:filename>")
def pdf_divisor_result(filename: str):
    safe_name = os.path.basename(filename)
    if safe_name != filename:
        abort(404)
    processed_folder = current_app.config["PROCESSED_FOLDER"]
    file_path = os.path.join(processed_folder, safe_name)
    if not os.path.isfile(file_path):
        abort(404)
    return render_template("doc/pdf/divisor/result.html", filename=safe_name)


@app.route("/pdf_to_image/")
def pdf_to_image_index():
    meta = {
        "title": "Converter PDF - FireTools",
        "description": "Converta PDFs em DOCX editáveis ou exporte páginas como imagens PNG, JPG ou WEBP.",
        "keywords": "converter pdf, pdf para docx, pdf para imagem",
    }
    requested_format = (request.args.get("target_format") or request.args.get("format") or "docx").lower()
    if requested_format not in PDF_SUPPORTED_FORMATS:
        requested_format = "docx"
    return render_template("doc/pdf/converter/index.html", meta=meta, requested_format=requested_format)


@app.route("/pdf_to_image/result/")
def pdf_to_image_result():
    files_param = request.args.get("files", "")
    if not files_param:
        abort(404)

    filenames: list[str] = []
    seen: set[str] = set()
    for raw_name in files_param.split(","):
        candidate = os.path.basename(raw_name.strip())
        if not candidate or candidate in seen:
            continue
        candidate_path = (PDF_CONVERTER_OUTPUTS / candidate).resolve()
        if candidate_path.parent != PDF_CONVERTER_OUTPUTS or not candidate_path.is_file():
            continue
        seen.add(candidate)
        filenames.append(candidate)

    if not filenames:
        abort(404)

    downloads = [
        {
            "file": name,
            "url": url_for("static", filename=f"doc/pdf/converter/converted/{name}"),
        }
        for name in filenames
    ]

    target_format = request.args.get("format", "").lower()
    if target_format not in PDF_SUPPORTED_FORMATS:
        target_format = ""
    is_image_format = target_format in PDF_IMAGE_FORMATS if target_format else False

    meta = {
        "title": "PDF convertido - FireTools",
        "description": "Baixe os arquivos gerados a partir do seu PDF no formato selecionado.",
        "keywords": "pdf convertido, download pdf docx, download imagens pdf",
    }

    return render_template(
        "doc/pdf/converter/result.html",
        meta=meta,
        converted=downloads,
        target_format=target_format,
        page_count=len(filenames),
        is_image_format=is_image_format,
    )

@app.route("/video_converter/result/<path:filename>")
def video_converter_result(filename: str):
    safe_name = os.path.basename(filename)
    if safe_name != filename:
        abort(404)
    candidate_path = (VIDEO_CONVERTER_OUTPUTS / safe_name).resolve()
    if candidate_path.parent != VIDEO_CONVERTER_OUTPUTS or not candidate_path.is_file():
        abort(404)
    return render_template("video/converter/result.html", filename=safe_name)


@app.route("/audio_converter/result/<path:filename>")
def audio_converter_result(filename: str):
    safe_name = os.path.basename(filename)
    if safe_name != filename:
        abort(404)
    candidate_path = (AUDIO_CONVERTER_OUTPUTS / safe_name).resolve()
    if candidate_path.parent != AUDIO_CONVERTER_OUTPUTS or not candidate_path.is_file():
        abort(404)
    return render_template("audio/converter/result.html", filename=safe_name)

@app.route("/background_remover/result/<path:filename>")
def background_remover_result(filename: str):
    safe_name = os.path.basename(filename)
    if safe_name != filename:
        abort(404)
    candidate_path = (BACKGROUND_REMOVER_OUTPUTS / safe_name).resolve()
    if candidate_path.parent != BACKGROUND_REMOVER_OUTPUTS or not candidate_path.is_file():
        abort(404)
    return render_template("image/background_remover/result.html", filename=safe_name)

@app.route("/url_shortener/result/<code>")
def url_shortener_result(code: str):
    short_url = url_for("url_shortener.redirect_short", code=code, _external=True)
    _remember_short_code(code)
    history_codes = session.get("shortener_codes", []) or []
    history = []
    for stored_code in history_codes:
        details = url_shortener_get_url_details(stored_code)
        if not details:
            continue
        history.append({
            "code": stored_code,
            "short_url": url_for("url_shortener.redirect_short", code=stored_code, _external=True),
            "original_url": details["original_url"],
            "click_count": details["click_count"],
            "stats_url": url_for("url_shortener.stats", code=stored_code),
            "is_current": stored_code == code,
        })
    click_count = next((item["click_count"] for item in history if item["code"] == code), url_shortener_get_click_count(code))
    meta = {
        "title": "URL Encurtada - FireTools",
        "description": "Compartilhe o link curto gerado e acompanhe os cliques em tempo real.",
        "keywords": "encurtador url, estatísticas de cliques, link curto",
    }
    return render_template(
        "url/shortener/result.html",
        code=code,
        short_url=short_url,
        click_count=click_count,
        meta=meta,
        history=history,
    )

@app.route("/image_converter/")
def image_converter_index():
    meta = {
        "title": "Conversor de Imagem - FireTools",
        "description": "Converta imagens entre diferentes formatos com qualidade preservada.",
        "keywords": "conversor imagem, jpg, png, webp"
    }
    requested_to = request.args.get("target_format")
    return render_template(
        "image/converter/index.html",
        meta=meta,
        max_file_size_mb=IMAGE_MAX_FILE_SIZE_MB,
        output_format_groups=IMAGE_OUTPUT_FORMAT_GROUPS,
        requested_to=requested_to,
        images=None,
    )


@app.route("/image_converter/result/")
def image_converter_result():
    files_param = request.args.get("files", "")
    if not files_param:
        abort(404)

    unique_files = []
    seen = set()
    for raw_name in files_param.split(","):
        candidate = os.path.basename(raw_name.strip())
        if not candidate or candidate in seen:
            continue
        candidate_path = (IMAGE_CONVERTER_UPLOADS / candidate).resolve()
        if IMAGE_CONVERTER_UPLOADS not in candidate_path.parents or not candidate_path.exists():
            continue
        seen.add(candidate)
        unique_files.append(candidate)

    if not unique_files:
        abort(404)

    meta = {
        "title": "Imagens Convertidas - FireTools",
        "description": "Baixe as imagens convertidas com facilidade logo após o processamento.",
        "keywords": "download imagem convertida, conversor de imagem",
    }
    return render_template(
        "image/converter/result.html",
        meta=meta,
        images=unique_files,
        target_format=request.args.get("target", ""),
    )

@app.route("/image_converter/result/<path:filename>")
def image_converter_result_legacy(filename: str):
    safe_name = os.path.basename(filename)
    if safe_name != filename:
        abort(404)

    candidate_path = (IMAGE_CONVERTER_UPLOADS / safe_name).resolve()
    if (
        IMAGE_CONVERTER_UPLOADS not in candidate_path.parents
        or not candidate_path.exists()
    ):
        abort(404)

    target = request.args.get("target", "")
    return redirect(
        url_for(
            "image_converter_result",
            files=safe_name,
            target=target,
        )
    )

@app.route("/video_converter/")
def video_converter_index():
    meta = {
        "title": "Conversor de Vídeo - FireTools",
        "description": "Converta vídeos para formatos populares com presets otimizados.",
        "keywords": "conversor video, mp4, avi, mov"
    }
    requested_to = request.args.get("output_format")
    return render_template(
        "video/converter/index.html",
        meta=meta,
        max_file_size_mb=VIDEO_MAX_FILE_SIZE_MB,
        output_format_groups=VIDEO_OUTPUT_FORMAT_GROUPS,
        requested_to=requested_to,
        allowed_extensions=", ".join(sorted(VIDEO_ALLOWED_INPUT_EXTENSIONS)),
    )


@app.route("/audio_converter/")
def audio_converter_index():
    meta = {
        "title": "Conversor de Áudio - FireTools",
        "description": "Converta arquivos de áudio entre diferentes formatos.",
        "keywords": "conversor audio, mp3, wav, flac"
    }
    requested_to = request.args.get("output_format")
    return render_template(
        "audio/converter/index.html",
        meta=meta,
        max_file_size_mb=AUDIO_MAX_FILE_SIZE_MB,
        output_format_groups=AUDIO_OUTPUT_FORMAT_GROUPS,
        requested_to=requested_to,
        allowed_extensions=", ".join(sorted(AUDIO_ALLOWED_INPUT_EXTENSIONS)),
    )

@app.route("/background_remover/")
def background_remover_index():
    meta = {
        "title": "Removedor de Fundo - FireTools",
        "description": "Remova o fundo de imagens automaticamente com IA.",
        "keywords": "remover fundo, background remover, ia"
    }
    return render_template(
        "image/background_remover/index.html",
        meta=meta,
        max_file_size_mb=BACKGROUND_MAX_FILE_SIZE_MB,
        allowed_extensions=", ".join(sorted(BACKGROUND_ALLOWED_EXTENSIONS)),
    )

@app.route("/url_shortener/", methods=["GET", "POST"])
def url_shortener_index():
    meta = {
        "title": "Encurtador de URL - FireTools",
        "description": "Encurte URLs longas de forma rápida e segura.",
        "keywords": "encurtador url, shortener, link curto"
    }
    if request.method == "POST":
        original_url = (request.form.get("url") or "").strip()
        custom_code = (request.form.get("code") or "").strip()
        desired_code = None
        if not original_url:
            flash("Informe uma URL válida para encurtar.", "danger")
        else:
            if custom_code:
                try:
                    desired_code = url_shortener_validate_custom_code(custom_code)
                except ValueError as exc:
                    flash(str(exc), "danger")
                    return redirect(url_for("url_shortener_index"))
            try:
                code = url_shortener_shorten_url(original_url, desired_code)
                _remember_short_code(code)
                flash("URL encurtada com sucesso!", "success")
                return redirect(url_for("url_shortener_result", code=code))
            except Exception as exc:
                current_app.logger.exception("Erro ao encurtar URL: %s", exc)
                flash("Não foi possível encurtar a URL no momento.", "danger")

    return render_template(
        "url/shortener/index.html",
        meta=meta,
    )


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/auto-politica-de-privacidade")
@app.route("/politica-de-privacidade")
def auto_privacy():
    """Serve the auto-generated privacy policy HTML"""
    templates_path = Path(app.root_path) / "templates"
    return send_from_directory(str(templates_path), "auto-politica-de-privacidade.html", mimetype="text/html")


@app.route("/auto-termos-de-servico")
@app.route("/termos-de-servico")
def auto_terms():
    """Serve the auto-generated terms of service HTML"""
    templates_path = Path(app.root_path) / "templates"
    return send_from_directory(str(templates_path), "auto-termos-de-servico.html", mimetype="text/html")


@app.route("/files/<path:filename>")
def serve_file(filename):
    folder = current_app.config["PROCESSED_FOLDER"]
    safe_path = os.path.join(folder, filename)
    if not os.path.isfile(safe_path):
        abort(404)
    return send_from_directory(folder, filename, as_attachment=True)


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


# --- Tratamento de erros ---
@app.errorhandler(RequestEntityTooLarge)
def file_too_large(e):
    logging.warning(
        f"Upload excedeu limite: IP={request.remote_addr}, User-Agent={request.user_agent}"
    )
    limit_mb = app.config.get("MAX_CONTENT_LENGTH", 0) // (1024 * 1024)
    return jsonify({"error": "Arquivo muito grande", "limit_mb": limit_mb}), 413


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    logging.error(
        f"Erro HTTP {e.code}: {e.description} - IP={request.remote_addr}, User-Agent={request.user_agent}"
    )
    return jsonify({"error": e.description, "code": e.code}), e.code


@app.errorhandler(Exception)
def handle_generic_exception(e):
    logging.error(
        f"Erro inesperado: {e} - IP={request.remote_addr}, User-Agent={request.user_agent}"
    )
    return jsonify({"error": "Erro interno do servidor"}), 500


# Context Processor
@app.context_processor
def inject_current_app():
    return {
        "current_app": current_app,
        "global_max_upload_mb": settings.max_upload_mb,
        "global_file_retention_seconds": settings.file_retention_seconds,
        "csrf_token": _generate_csrf_token,
    }


# Security Headers
@app.after_request
def set_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    # Política permissiva mínima para evitar quebrar integrações; ajuste conforme necessário
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    return response


def _run_global_cleanup() -> None:
    """Executa limpeza dos diretórios compartilhados e específicos das ferramentas."""
    policies = [
        RetentionPolicy(UPLOAD_FOLDER, settings.file_retention_seconds),
        RetentionPolicy(PROCESSED_FOLDER, settings.file_retention_seconds),
    ]
    cleanup_retention_policies(policies)

    try:
        from tools.image.converter.service import cleanup_old_files as cleanup_images

        cleanup_images()
    except Exception as exc:  # pragma: no cover - logging de debug
        logging.getLogger(__name__).debug("Falha ao limpar imagens: %s", exc, exc_info=exc)

    try:
        from tools.audio.converter.service import cleanup_old_files as cleanup_audio

        cleanup_audio()
    except Exception as exc:  # pragma: no cover
        logging.getLogger(__name__).debug("Falha ao limpar áudios: %s", exc, exc_info=exc)

    try:
        from tools.video.converter.service import cleanup_old_files as cleanup_videos

        cleanup_videos()
    except Exception as exc:  # pragma: no cover
        logging.getLogger(__name__).debug("Falha ao limpar vídeos: %s", exc, exc_info=exc)

    try:
        from tools.image.background_remover.service import cleanup_old_files as cleanup_backgrounds

        cleanup_backgrounds()
    except Exception as exc:  # pragma: no cover
        logging.getLogger(__name__).debug("Falha ao limpar fundos: %s", exc, exc_info=exc)


if settings.cleanup_on_startup:
    _run_global_cleanup()


@app.cli.command("cleanup")
def cleanup_command():
    """Remove arquivos expirados de uploads e diretórios de saída."""
    _run_global_cleanup()
    click.echo("Limpeza concluída.")


# Execução
if __name__ == "__main__":
    # Prefer running via gunicorn in Cloud Run; this block is for local dev
    port = int(os.environ.get("PORT", 8080))
    debug_env = os.environ.get("DEBUG", "").lower()
    debug = debug_env in ("1", "true", "yes", "on")
    print(f"Starting Flask app on port {port}, debug={debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)
