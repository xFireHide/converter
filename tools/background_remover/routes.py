from flask import Blueprint, render_template, request, flash
from werkzeug.utils import secure_filename
from PIL import Image
import os
import uuid

bp = Blueprint("background_remover", __name__, url_prefix="/background_remover")

UPLOAD_FOLDER = "static/background_remover/uploads"
ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "bmp",
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image(path):
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def remove_background(input_path, tolerance=30):
    """Remove a cor de fundo predominante (canto superior esquerdo)."""
    with Image.open(input_path).convert("RGBA") as img:
        datas = list(img.getdata())
        bg_color = datas[0][:3]
        result = []
        for item in datas:
            if all(abs(item[i] - bg_color[i]) <= tolerance for i in range(3)):
                result.append((255, 255, 255, 0))
            else:
                result.append(item)
        img.putdata(result)
        output_filename = f"{uuid.uuid4().hex}.png"
        output_path = os.path.join(UPLOAD_FOLDER, secure_filename(output_filename))
        img.save(output_path, "PNG")
    return output_filename


@bp.route("/", methods=["GET", "POST"])
def index():
    image = None
    if request.method == "POST":
        file = request.files.get("image")
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            tmp_name = f"{uuid.uuid4().hex}.{ext}"
            tmp_path = os.path.join(UPLOAD_FOLDER, secure_filename(tmp_name))
            file.save(tmp_path)
            if validate_image(tmp_path):
                try:
                    out_file = remove_background(tmp_path)
                    image = out_file
                    flash("Fundo removido com sucesso!", "success")
                except Exception:
                    flash("Erro ao processar a imagem.", "danger")
                finally:
                    os.remove(tmp_path)
            else:
                os.remove(tmp_path)
                flash("Arquivo de imagem inválido.", "danger")
        else:
            flash("Nenhum arquivo enviado ou extensão não suportada.", "danger")
    return render_template("background_remover/index.html", image=image)
