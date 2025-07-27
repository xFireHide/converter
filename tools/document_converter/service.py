import os, uuid, subprocess
from pdf2docx import Converter
from ebooklib import epub
from reportlab.pdfgen import canvas

UPLOAD_FOLDER = "static/document_converter/uploads"
CONVERTED_FOLDER = "static/document_converter/converted"
ALLOWED_EXTENSIONS = {"pdf", "epub"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)


def is_allowed(filename, extension):
    return filename.lower().endswith(extension)


def save_file(file):
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return filepath


def pdf_to_word(input_path):
    output_filename = f"{uuid.uuid4()}.docx"
    output_path = os.path.join(CONVERTED_FOLDER, output_filename)
    cv = Converter(input_path)
    cv.convert(output_path)
    cv.close()
    return output_filename


def epub_to_pdf(input_path):
    output_filename = f"{uuid.uuid4()}.pdf"
    output_path = os.path.join(CONVERTED_FOLDER, output_filename)
    book = epub.read_epub(input_path)
    c = canvas.Canvas(output_path)
    y = 800
    for item in book.get_items():
        if item.get_type() == epub.EpubHtml:
            text = item.get_body_content().decode("utf-8")
            for line in text.splitlines():
                c.drawString(50, y, line[:100])
                y -= 12
                if y < 40:
                    c.showPage()
                    y = 800
    c.save()
    return output_filename


def epub_to_mobi(input_path):
    output_filename = f"{uuid.uuid4()}.mobi"
    output_path = os.path.join(CONVERTED_FOLDER, output_filename)
    subprocess.run(["ebook-convert", input_path, output_path])
    return output_filename
