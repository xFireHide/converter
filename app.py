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
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

# --- Configuração do App ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,  # Limite de upload (8 MB)
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# Diretórios essenciais
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER

# Configuração dos Logs
logging.basicConfig(
    filename=os.path.join(LOGS_DIR, "security.log"),
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(message)s",
)

# --- Proteções ---
CSRFProtect(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["50 per hour"],
)

# --- Carregamento dinâmico dos Blueprints ---
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
            logging.warning(f"Blueprint não encontrado: {module_path} - {e}")


# --- Rotas principais ---
@app.route("/")
def home():
    return render_template("home.html")


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
    return "Arquivo muito grande! O limite é 8MB.", 413


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    logging.error(
        f"Erro HTTP {e.code}: {e.description} - IP={request.remote_addr}, User-Agent={request.user_agent}"
    )
    return render_template("error.html", error=e), e.code


@app.errorhandler(Exception)
def handle_generic_exception(e):
    logging.error(
        f"Erro inesperado: {e} - IP={request.remote_addr}, User-Agent={request.user_agent}"
    )
    return render_template("error.html", error=e), 500


# Context Processor
@app.context_processor
def inject_current_app():
    return {"current_app": current_app}


# Execução
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4666))
    app.run(host="0.0.0.0", port=port, debug=True)
