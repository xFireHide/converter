"""CLI simples do FireConverter.

Exemplos:
    python cli.py imagem png foto.jpg -o saida/
    python cli.py audio mp3 musica.flac
    python cli.py video mp4 clipe.mov -o convertidos/
    python cli.py pdf docx documento.pdf
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from converters import CONVERTERS

# aliases sem acento para a linha de comando
_ALIASES = {"imagem": "Imagem", "audio": "Áudio", "video": "Vídeo", "pdf": "PDF"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Conversor de arquivos (imagem, áudio, vídeo, PDF).")
    parser.add_argument("tipo", choices=sorted(_ALIASES), help="categoria de conversão")
    parser.add_argument("formato", help="formato de saída (ex.: png, mp3, mp4, docx)")
    parser.add_argument("arquivos", nargs="+", type=Path, help="arquivos de entrada")
    parser.add_argument("-o", "--output", type=Path, default=Path.cwd(), help="pasta de saída")
    args = parser.parse_args(argv)

    module = CONVERTERS[_ALIASES[args.tipo]]
    output_dir = args.output.expanduser().resolve()

    failures = 0
    for src in args.arquivos:
        src = src.expanduser().resolve()
        try:
            outputs = module.convert(src, args.formato, output_dir)
            print(f"OK: {src.name} → {', '.join(o.name for o in outputs)}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"ERRO: {src.name}: {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
