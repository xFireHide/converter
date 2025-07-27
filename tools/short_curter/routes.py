from flask import Blueprint, render_template, request, redirect, flash, url_for

# Support running this file directly by adjusting the import path
if __package__ is None or __package__ == "":
    import os
    import sys

    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    )
    from tools.short_curter.service import (
        shorten_url,
        get_original_url,
        get_click_count,
        init_db,
    )
else:
    from .service import (
        shorten_url,
        get_original_url,
        get_click_count,
        init_db,
    )


bp = Blueprint("short_curter", __name__, url_prefix="/short_curter")


init_db()


@bp.route("/", methods=["GET", "POST"])
def index():
    short_url = None
    click_count = None
    if request.method == "POST":
        original_url = request.form.get("url")
        if original_url:
            code = shorten_url(original_url)
            short_url = url_for(
                "short_curter.redirect_short", code=code, _external=True
            )
            click_count = get_click_count(code)
    return render_template(
        "short_curter/index.html", short_url=short_url, click_count=click_count
    )
    return render_template("short_curter/index.html", short_url=short_url)
