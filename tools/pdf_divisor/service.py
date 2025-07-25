import fitz
import os


class PDFProcessor:␊
    def __init__(self, dpi=100, limite_branco=0.999):
        self.dpi = dpi␊
        self.limite_branco = limite_branco␊

    def is_area_branca(self, pagina, clip):
        pix = pagina.get_pixmap(
            dpi=self.dpi,
            colorspace=fitz.csGRAY,
            clip=clip,
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
                return True, stats
            return False, "PDF resultante vazio"

        except Exception as e: