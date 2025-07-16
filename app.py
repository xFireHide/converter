import os
import pkgutil
import importlib
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

# Diretórios para upload e arquivos processados
UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
PROCESSED_FOLDER = os.path.join(app.root_path, "processed")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)


@app.route("/")
def home():
    """Página inicial do site."""
    return render_template("home.html")


# Registra automaticamente todas as ferramentas dentro da pasta tools
TOOLS_DIR = os.path.join(app.root_path, "tools")
for finder, name, ispkg in pkgutil.iter_modules([TOOLS_DIR]):
    module = importlib.import_module(f"tools.{name}.routes")
    if hasattr(module, "bp"):
        app.register_blueprint(module.bp)


@app.route("/download/file/<filename>")
def serve_file(filename):
    """Serve arquivos processados como anexo."""
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
