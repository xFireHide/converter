from flask import Flask, render_template, request, send_file
import os
from pdf_processor import process_pdf

app = Flask(__name__)

# Pastas de upload e de arquivos processados
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        pdf = request.files.get('pdf')
        # Validação básica
        if not pdf or not pdf.filename.lower().endswith('.pdf'):
            error = "Selecione um arquivo PDF válido."
            return render_template('index.html', error=error)

        # Salva o PDF enviado
        input_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
        pdf.save(input_path)

        # Define caminho de saída com sufixo "_processed.pdf"
        nome_base, _ = os.path.splitext(pdf.filename)
        output_path = os.path.join(PROCESSED_FOLDER, f"{nome_base}_processed.pdf")

        try:
            # Processa e retorna o caminho do arquivo gerado
            result_file = process_pdf(input_path, output_path)
            return send_file(result_file, as_attachment=True)
        except Exception as e:
            error = f"Erro ao processar o PDF: {e}"

    return render_template('index.html', error=error)

if __name__ == '__main__':
    # Usa variável de ambiente PORT se disponível (ex: no Render)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
