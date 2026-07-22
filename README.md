# FireConverter

## Web version (Netlify)

A static web version lives in [`web/`](web/) — batch conversion running 100% client-side
(Canvas for images, pdf.js for PDF, ffmpeg.wasm for audio/video). No server, files never
leave the browser.

**Deploy to Netlify** — pick one:

- **Git**: push this repo and import it on [app.netlify.com](https://app.netlify.com).
  `netlify.toml` already sets `publish = "web"`; no build command needed.
- **Drag & drop**: drop the `web/` folder on https://app.netlify.com/drop.
- **CLI**: `netlify deploy --prod --dir web`

Run locally: `python3 -m http.server -d web 8000` → http://localhost:8000

## Desktop app

Desktop app (tkinter GUI) for **batch file conversion**. Add multiple files, pick
the output folder and format — conversion runs in parallel with a progress bar and log.

## Converters

| Type  | Inputs                                     | Outputs                                          |
|-------|--------------------------------------------|--------------------------------------------------|
| Image | PNG, JPG, WEBP, GIF, BMP, TIFF, HEIC, SVG… | PNG, JPG, WEBP, GIF, BMP, TIFF, ICO, PDF, AVIF…  |
| Audio | MP3, WAV, FLAC, AAC, M4A, OGG…             | MP3, AAC, M4A, OGG, OPUS, FLAC, ALAC, WAV, AIFF… |
| Video | MP4, MOV, MKV, AVI, WEBM…                  | MP4, MKV, WEBM, MOV, AVI, HEVC, AV1, ProRes, GIF…|
| PDF   | PDF                                        | PNG/JPG/WEBP (one per page) or DOCX              |

## Requirements

- Python 3.10+ with tkinter (bundled in the official macOS/Windows Python).
- **ffmpeg** for audio/video: bundled via `imageio-ffmpeg` (or use `brew install ffmpeg`).

## Run

```bash
./run.sh        # creates the venv, installs deps, opens the GUI
```

Manually:

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python gui.py
```

### CLI (optional)

```bash
python cli.py image png photo.jpg -o out/
python cli.py audio mp3 song.flac
python cli.py video mp4 clip.mov -o converted/
python cli.py pdf   docx document.pdf
```

Optional image formats — uncomment in `requirements.txt` and reinstall:
`pillow-heif` (HEIC/HEIF), `pillow-avif-plugin` (AVIF), `cairosvg` (SVG).
