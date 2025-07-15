import fitz
import os


class PDFProcessor:
    def __init__(self, dpi=150, limite_branco=0.999):
        self.dpi = dpi
        self.limite_branco = limite_branco

    def is_area_branca(self, pagina, clip):
        pix = pagina.get_pixmap(
            dpi=self.dpi, colorspace=fitz.csGRAY, clip=clip, matrix=fitz.Matrix(2, 2)
        )

        total = pix.width * pix.height
        if total == 0:
            return True

        nao_brancos = sum(1 for p in pix.samples if p < 250)
        return (nao_brancos / total) < (1 - self.limite_branco)

    def processar_pdf(self, input_path, output_path):
        novo_pdf = fitz.open()
        stats = {"original": 0, "novas": 0}

        try:
            with fitz.open(input_path) as doc:
                stats["original"] = len(doc)
                for pagina in doc:
                    self._processar_pagina(pagina, novo_pdf)

            if novo_pdf.page_count > 0:
                novo_pdf.save(output_path, deflate=True, garbage=4)
                stats["novas"] = novo_pdf.page_count
                return (True, stats)
            return (False, "PDF resultante vazio")

        except Exception as e:
            return (False, f"Erro: {str(e)}")
        finally:
            novo_pdf.close()

    def _processar_pagina(self, pagina, novo_pdf):
        rect = pagina.rect
        largura = rect.width
        altura = rect.height

        # Divisão fixa em 4 quadrantes
        quadrantes = [
            fitz.Rect(0, 0, largura / 2, altura / 2),
            fitz.Rect(largura / 2, 0, largura, altura / 2),
            fitz.Rect(0, altura / 2, largura / 2, altura),
            fitz.Rect(largura / 2, altura / 2, largura, altura),
        ]

        # Adicionar quadrantes com conteúdo
        for q in quadrantes:
            if not self.is_area_branca(pagina, q):
                nova_pag = novo_pdf.new_page(width=q.width, height=q.height)
                nova_pag.show_pdf_page(
                    nova_pag.rect, pagina.parent, pagina.number, clip=q
                )
