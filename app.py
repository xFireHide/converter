import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
)
from pdf_processor import process_pdf

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
PROCESSED_FOLDER = os.path.join(app.root_path, "processed")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/divisorpdf", methods=["GET", "POST"])
def pdf_divisor():
    error = None
    if request.method == "POST":
        pdf = request.files.get("pdf")
        if not pdf or not pdf.filename.lower().endswith(".pdf"):
            error = "Selecione um PDF válido."
            return render_template("pdf_divisor.html", error=error)

        input_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
        pdf.save(input_path)

        output_name = os.path.splitext(pdf.filename)[0] + "_processed.pdf"
        output_path = os.path.join(PROCESSED_FOLDER, output_name)

        try:
            process_pdf(input_path, output_path)
            return redirect(url_for("download_page", filename=output_name))
        except Exception as e:
            error = f"Erro ao processar o PDF: {e}"

    return render_template("pdf_divisor.html", error=error)


@app.route("/download/<filename>")
def download_page(filename):
    return render_template("result.html", filename=filename)


@app.route("/download/file/<filename>")
def serve_file(filename):
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)
