# FileConverter

Aplicativo **desktop** (interface gráfica em tkinter) para converter arquivos em
lote. Inspirado na GUI do projeto *Image-to-SVG*: você adiciona vários arquivos,
escolhe a pasta de saída e o formato, e a conversão roda em paralelo com barra de
progresso e log.

## Conversores

| Tipo    | Entradas                                   | Saídas                                              |
|---------|--------------------------------------------|-----------------------------------------------------|
| Imagem  | PNG, JPG, WEBP, GIF, BMP, TIFF, HEIC, SVG… | PNG, JPG, WEBP, GIF, BMP, TIFF, ICO, PDF, AVIF…     |
| Áudio   | MP3, WAV, FLAC, AAC, M4A, OGG…             | MP3, AAC, M4A, OGG, OPUS, FLAC, ALAC, WAV, AIFF…    |
| Vídeo   | MP4, MOV, MKV, AVI, WEBM…                  | MP4, MKV, WEBM, MOV, AVI, HEVC, AV1, ProRes, GIF…   |
| PDF     | PDF                                        | PNG, JPG, WEBP (uma por página) ou DOCX (Word)      |

## Requisitos

- Python 3.10+ (com tkinter — já incluso no Python do macOS/Windows oficiais).
- **ffmpeg** para áudio/vídeo: vem empacotado via `imageio-ffmpeg`; se preferir,
  instale o do sistema (`brew install ffmpeg`).

## Como rodar

```bash
./run.sh
```

O script cria o ambiente virtual, instala as dependências e abre a interface.
Para rodar manualmente:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python gui.py
```

### Linha de comando (opcional)

```bash
python cli.py imagem png foto.jpg -o saida/
python cli.py audio  mp3 musica.flac
python cli.py video  mp4 clipe.mov -o convertidos/
python cli.py pdf    docx documento.pdf
```

## Formatos extras de imagem (opcionais)

Descomente em `requirements.txt` e reinstale para habilitar:

- `pillow-heif` → HEIC/HEIF
- `pillow-avif-plugin` → AVIF
- `cairosvg` → ler/converter SVG
