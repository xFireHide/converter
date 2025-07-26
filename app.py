import os
import pkgutil
import importlib
import logging
import secrets
from flask import (
    Flask,
    render_template,
    send_from_directory,
    current_app,
    request,
    abort,
)
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- Flask App e Configs ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB limite upload
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


@app.context_processor
def inject_current_app():
    return {"current_app": current_app}


# Diretórios importantes
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Cria diretório logs seguro (fora de static)
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOGS_DIR, "security.log"),
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(message)s",
)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER

# --- Proteções ---
CSRFProtect(app)
limiter = Limiter(key_func=get_remote_address, default_limits=["50 per hour"])
limiter.init_app(app)

# --- Blueprints dinâmicos ---
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
if os.path.isdir(TOOLS_DIR):
    for finder, name, ispkg in pkgutil.iter_modules([TOOLS_DIR]):
        module_path = f"tools.{name}.routes"
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, "bp"):
                app.register_blueprint(module.bp)
                print(f"Blueprint registrada: {module.bp.name} ({module_path})")
        except ModuleNotFoundError as e:
            print(f"Não foi possível importar {module_path}: {e}")
        except Exception as ex:
            print(f"Erro inesperado ao importar {module_path}: {ex}")


# --- Headers extras para segurança ---
@app.after_request
def set_secure_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=63072000; includeSubDomains"
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")


# Download seguro
@app.route("/download/file/<filename>")
def serve_file(filename):
    # Só permite arquivos processados, bloqueia traversal
    folder = current_app.config["PROCESSED_FOLDER"]
    safe_path = os.path.join(folder, filename)
    if not os.path.isfile(safe_path):
        abort(404)
    return send_from_directory(folder, filename, as_attachment=True)


# Favicon to avoid 404 logs
@app.route("/favicon.ico")
def favicon():
    """Serve the application favicon."""
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


# Limita uploads por IP (opcional)
@app.errorhandler(413)
def file_too_large(e):
    return "Arquivo muito grande! O limite é 8MB.", 413

from werkzeug.exceptions import HTTPException, RequestEntityTooLarge


@app.errorhandler(Exception)
def handle_exception(e):
    """Central error handler that preserves status codes and logs events."""
    if isinstance(e, RequestEntityTooLarge):


# Loga uploads inválidos e erros
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge


@app.errorhandler(Exception)
def handle_exception(e):
    """Central error handler that preserves status codes and logs events."""
    if isinstance(e, RequestEntityTooLarge):
        logging.warning(
            f"Tentativa de upload acima do limite: IP={request.remote_addr}, Agent={request.user_agent}"
        )
        return e.description, e.code

    if isinstance(e, HTTPException):
        logging.error(
            f"Erro: {e} | IP={request.remote_addr}, Agent={request.user_agent}"
        )
        return e.description, e.code

    logging.error(
        f"Erro: {e} | IP={request.remote_addr}, Agent={request.user_agent}"
    )
    return str(e), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4666))
    app.run(host="0.0.0.0", port=port, debug=True)