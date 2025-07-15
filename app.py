from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from pdf_processor import process_pdf

app = Flask(__name__)

UPLOAD_FOLDER    = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER,    exist_ok=True)
os.makedirs(PROCESSED_FOLDER,  exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        pdf = request.files.get('pdf')
        if not pdf or not pdf.filename.lower().endswith('.pdf'):
            error = "Selecione um arquivo PDF válido."
            return render_template('index.html', error=error)

        # Salva o PDF
        filename    = pdf.filename
        input_path  = os.path.join(UPLOAD_FOLDER, filename)
        pdf.save(input_path)

        # Define output
        base_name    = os.path.splitext(filename)[0]
        output_name  = f"{base_name}_processed.pdf"
        output_path  = os.path.join(PROCESSED_FOLDER, output_name)

        try:
            process_pdf(input_path, output_path)
            # Redireciona para a página de download
            return redirect(url_for('download_page', filename=output_name))
        except Exception as e:
            error = f"Erro ao processar o PDF: {e}"

    return render_template('index.html', error=error)


@app.route('/download-page/<filename>')
def download_page(filename):
    """
    Página de resultado com links de:
     - Baixar: /download-file/<filename>
     - Voltar: /
    """
    return render_template('result.html', filename=filename)


@app.route('/download-file/<filename>')
def download_file(filename):
    """
    Serve o arquivo processado como attachment.
    """
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
