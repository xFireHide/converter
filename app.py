import os
import pkgutil
import importlib
from flask import Flask, render_template, send_from_directory

# Inicializa o Flask
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


# Descobre e registra automaticamente cada ferramenta em tools/
TOOLS_DIR = os.path.join(app.root_path, "tools")
if os.path.isdir(TOOLS_DIR):
    for finder, name, ispkg in pkgutil.iter_modules([TOOLS_DIR]):
        module = importlib.import_module(f"tools.{name}")
        # Cada módulo em tools/ deve expor um Blueprint chamado 'bp'
        if hasattr(module, "bp"):
            app.register_blueprint(module.bp)


@app.route("/download/file/<filename>")
def serve_file(filename):
    """Serve qualquer arquivo processado como anexo."""
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
