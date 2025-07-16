import os
from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint("short_cut", __name__, url_prefix="/shortcut")


@bp.route("/", methods=["GET", "POST"])
def index():
    error = None
    short_url = None

    if request.method == "POST":
        original = request.form.get("original_url", "").strip()
        if not original:
            error = "Digite uma URL válida."
        else:
            # Exemplo simples de “encurtador”
            # Aqui você pode chamar uma API externa ou implementar seu algoritmo
            key = abs(hash(original)) % (10**6)
            short_url = f"{request.host_url}r/{key}"

    return render_template(
        "short_cut.html",
        original_url=request.form.get("original_url", ""),
        short_url=short_url,
        error=error,
    )
