from flask import Flask, render_template, request, send_file
import os
from pdf_processor import process_pdf

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pdf = request.files['pdf']
        if pdf and pdf.filename.endswith('.pdf'):
            caminho_pdf = os.path.join(UPLOAD_FOLDER, pdf.filename)
            pdf.save(caminho_pdf)

            try:
                resultado = process_pdf(caminho_pdf)
                return send_file(resultado, as_attachment=True)
            except Exception as e:
                return f"Erro ao processar o PDF: {str(e)}"
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)