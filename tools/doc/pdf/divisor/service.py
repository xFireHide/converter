import fitz
import os


class PDFProcessor:
    def __init__(self, dpi=150, limite_branco=0.999, scale=2):
        self.dpi = dpi
        self.limite_branco = limite_branco
        # scale controla a resolução do pixmap ao checar branco vs conteúdo
        self.scale = max(1, int(scale))

    def is_area_branca(self, pagina, clip):
        # Usa escala baixa para acelerar a verificação de branco
        matrix = fitz.Matrix(self.scale, self.scale)
        pix = pagina.get_pixmap(colorspace=fitz.csGRAY, clip=clip, matrix=matrix)

        total = pix.width * pix.height
        if total == 0:
            return True

        # Considera pixels "não brancos" abaixo de 250 (0-255)
        non_white_pixels = 0
        sample_bytes = pix.samples
        for value in sample_bytes:
            if value < 250:
                non_white_pixels += 1

        return (non_white_pixels / total) < (1 - self.limite_branco)

    def processar_pdf(self, input_path, output_path):
        novo_pdf = fitz.open()
        stats = {"original": 0, "novas": 0}

        try:
            with fitz.open(input_path) as doc:
                stats["original"] = len(doc)
                for pagina in doc:
                    self._processar_pagina(pagina, novo_pdf)

            if novo_pdf.page_count > 0:
                # Otimizações de tamanho e limpeza
                novo_pdf.save(output_path, deflate=True, garbage=4)
                stats["novas"] = novo_pdf.page_count
                return True, stats
            return False, "PDF resultante vazio"

        except Exception as e:
            return False, f"Erro: {e}"

        finally:
            novo_pdf.close()

    def _processar_pagina(self, pagina, novo_pdf):
        rect = pagina.rect
        largura, altura = rect.width, rect.height

        quadrantes = [
            fitz.Rect(0, 0, largura / 2, altura / 2),
            fitz.Rect(largura / 2, 0, largura, altura / 2),
            fitz.Rect(0, altura / 2, largura / 2, altura),
            fitz.Rect(largura / 2, altura / 2, largura, altura),
        ]

        for q in quadrantes:
            # Só cria nova página se houver conteúdo perceptível no quadrante
            if not self.is_area_branca(pagina, q):
                nova_pag = novo_pdf.new_page(width=q.width, height=q.height)
                nova_pag.show_pdf_page(nova_pag.rect, pagina.parent, pagina.number, clip=q)


def process_pdf(input_path, output_path=None):
    """
    Processa o PDF de input_path e retorna o caminho do arquivo processado.
    Se output_path não for especificado, salva em input_path_processed.pdf.
    """
    if output_path is None:
        base, _ = os.path.splitext(input_path)
        output_path = f"{base}_processed.pdf"

    processor = PDFProcessor()
    sucesso, resultado = processor.processar_pdf(input_path, output_path)
    if not sucesso:
        raise RuntimeError(f"Falha ao processar PDF: {resultado}")
    return output_path
