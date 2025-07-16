from flask import Blueprint, render_template, request, redirect, url_for
from .processor import process_pdf

bp = Blueprint("pdf_divisor", __name__, url_prefix="/divisorpdf")


@bp.route("/", methods=["GET", "POST"])
def index():
    return render_template("pdf_divisor.html")
