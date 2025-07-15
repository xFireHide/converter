import logging
from flask import Flask, render_template, request, send_file
import os
from pdf_processor import process_pdf

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    app.logger.debug(f"Requisição {request.method} em /")
    if request.method == 'POST':
        pdf = request.files.get('pdf')
        if not pdf or not pdf.filename.lower().endswith('.pdf'):
            error = "Selecione um arquivo PDF válido."
            app.logger.debug("Arquivo inválido ou não enviado.")
            return render_template('index.html', error=error)

        # Salva o PDF enviado
        input_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
        pdf.save(input_path)
        app.logger.debug(f"Arquivo salvo em {input_path}")

        # Define saída
        nome_base, _ = os.path.splitext(pdf.filename)
        output_path = os.path.join(PROCESSED_FOLDER, f"{nome_base}_processed.pdf")
        app.logger.debug(f"Chamando process_pdf em {input_path}, saída em {output_path}")

        try:
            result_file = process_pdf(input_path, output_path)
            app.logger.debug(f"process_pdf retornou {result_file}")
            return send_file(result_file, as_attachment=True)
        except Exception as e:
            error = f"Erro ao processar o PDF: {e}"
            app.logger.error(error)

    return render_template('index.html', error=error)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
