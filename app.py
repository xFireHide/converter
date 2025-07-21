import os
import pkgutil
import importlib
from flask import Flask, render_template, send_from_directory, current_app


app = Flask(__name__)


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)


TOOLS_DIR = os.path.join(BASE_DIR, "tools")
if os.path.isdir(TOOLS_DIR):
    for finder, name, ispkg in pkgutil.iter_modules([TOOLS_DIR]):
        module_path = f"tools.{name}.routes"
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, "bp"):
                app.register_blueprint(module.bp)
        except ModuleNotFoundError:
            continue


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/download/file/<filename>")
def serve_file(filename):
    folder = current_app.config["PROCESSED_FOLDER"]
    return send_from_directory(folder, filename, as_attachment=True)


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
