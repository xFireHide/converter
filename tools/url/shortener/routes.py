from flask import Blueprint, jsonify, request, redirect, url_for

from .service import (
    shorten_url,
    get_original_url,
    get_click_count,
    init_db,
    validate_custom_code,
)


bp = Blueprint("url_shortener", __name__, url_prefix="/api/url")


init_db()


@bp.post("/shorten")
def shorten():
    payload = request.get_json(silent=True) or request.form
    original_url = (payload.get("url") if payload else None) or request.form.get("url")
    custom_code = (payload.get("code") if payload else None) or request.form.get("code")

    if not original_url:
        return jsonify({"status": "error", "message": "Campo 'url' é obrigatório."}), 400

    desired_code: str | None = None
    if custom_code:
        desired_code = validate_custom_code(custom_code)

    try:
        code = shorten_url(original_url, desired_code)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    result_url = url_for("url_shortener_result", code=code, _external=True)
    click_count = get_click_count(code)
    return jsonify({
        "status": "success",
        "code": code,
        "short_url": result_url,
        "click_count": click_count,
    })


@bp.get("/stats/<code>")
def stats(code):
    count = get_click_count(code)
    return jsonify({"code": code, "click_count": count})


@bp.get("/r/<code>")
def redirect_short(code):
    original_url = get_original_url(code)
    if original_url:
        return redirect(original_url)
    return jsonify({"status": "error", "message": "Link não encontrado ou expirado."}), 404
