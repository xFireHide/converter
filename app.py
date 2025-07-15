from flask import Flask, render_template, request, redirect, url_for
import os
from pdf_processor import process_pdf

app = Flask(__name__)

UPLOAD_FOLDER   = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER,   exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        pdf = request.files.get('pdf')
        if not pdf or not pdf.filename.lower().endswith('.pdf'):
            error = "Selecione um arquivo PDF válido."
            return render_template('index.html', error=error)

        # Salva o PDF
        filename   = pdf.filename
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        pdf.save(input_path)

        # Define output
        name_base  = os.path.splitext(filename)[0]
        output_name = f"{name_base}_processed.pdf"
        output_path = os.path.join(PROCESSED_FOLDER, output_name)

        try:
            # Processa e gera processed file
            process_pdf(input_path, output_path)
            # Redireciona para rota de download, passando o nome do arquivo
            return redirect(url_for('download_page', filename=output_name))
        except Exception as e:
            error = f"Erro ao processar o PDF: {e}"

    return render_template('index.html', error=error)


@app.route('/download/<filename>')
def download_page(filename):
    """Mostra uma página com link para download do PDF processado."""
    file_url = url_for('static', filename=f"../{PROCESSED_FOLDER}/{filename}")
    # Observação: se não usar static, você pode servir via send_from_directory
    return render_template('result.html', filename=filename, file_url=file_url)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
