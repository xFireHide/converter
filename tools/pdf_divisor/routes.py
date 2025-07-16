from flask import Blueprint, render_template, request, redirect, url_for
from .pdf_divisor import process_pdf  # Import relativo

bp = Blueprint("pdf_divisor", __name__, url_prefix="/divisorpdf")


@bp.route("/", methods=["GET", "POST"])
def index():
    return render_template("pdf_divisor.html")
