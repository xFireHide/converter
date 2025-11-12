# FireTools

FireTools is a Flask application that bundles several media and document utilities behind a single JSON API and a unified web UI. Each tool lives in `tools/` as an independent blueprint (loaded automatically on startup) so converters can be enabled, updated or isolated without touching the rest of the stack.

## Highlights

- ✅ PDF utilities: split pages into quadrants or convert entire documents to DOCX/PNG/JPG/WEBP.
- 🎨 Image helpers: format conversion and background removal powered by `rembg`.
- 🔊 Audio & 🎥 video converters with pre-defined format groups (FFmpeg via `imageio-ffmpeg`).
- 🔗 URL shortener with click tracking and result history by session.
- 🌐 Bilingual front-end (PT/EN) driven by a lightweight `i18n.js` toggle.
- ♻️ Automatic cleanup of uploads/outputs based on retention policies.

The default upload limit is **200&nbsp;MB** and processed files are deleted after one hour; both values can be adjusted through environment variables.

## Requirements

- Python 3.11+ (the project currently runs on Python 3.13 in development)
- `pip` / `venv`
- FFmpeg (optional at runtime — bundled via `imageio-ffmpeg`, but installing the system binary improves performance)
- Google Cloud CLI (only for deployment)

## Getting Started

1. Clone the repository and create a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install backend dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Launch the development server:

   ```bash
   python app.py
   ```

   The app listens on `http://127.0.0.1:4666` by default. Use `FLASK_ENV=development` or a process manager (e.g. `flask --app app --debug run`) if you prefer auto‑reloads.

4. Open the browser at `http://127.0.0.1:4666/` — the navbar exposes all enabled tools and the language toggle.

## Quick Validation

You can run a basic smoke test straight from Python to ensure blueprints load and the PDF converter works:

```bash
./venv/bin/python - <<'PY'
from app import app
client = app.test_client()
with app.test_request_context():
    print('Blueprints:', sorted(app.blueprints))

pdf = open('test.pdf', 'rb')
resp = client.post(
    '/api/doc/pdf/convert',
    data={'pdf': (pdf, 'test.pdf'), 'target_format': 'docx'},
    content_type='multipart/form-data'
)
print('PDF->DOCX status:', resp.status_code, resp.json.get('status'))
PY
```

## Environment Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | random | Session/CSRF protection; always set in production. |
| `PORT` | `4666` | Port used by `python app.py`. |
| `MAX_UPLOAD_MB` | `200` | Global upload limit enforced by Flask. |
| `FILE_RETENTION_SECONDS` | `3600` | Time before uploaded/processed files are deleted. |
| `IMAGE_MAX_FILE_SIZE_MB` / `AUDIO_MAX_FILE_SIZE_MB` / `VIDEO_MAX_FILE_SIZE_MB` / `BACKGROUND_MAX_FILE_SIZE_MB` | tool defaults | Optional per-tool overrides. |
| `RATELIMIT_STORAGE_URI` | in-memory | Configure Flask-Limiter storage (Redis/Memcached) for production use. |

Export these variables (or configure them in Cloud Run) before launching the app.

## Tool Summary

| Route | Blueprint | Description |
|-------|-----------|-------------|
| `/pdf_to_image/` | `pdf_converter` | Upload a PDF and generate DOCX or image files. |
| `/pdf_divisor/` | `pdf_divisor` | Split each page into four quadrants. |
| `/image_converter/` | `image_converter` | Convert images across popular/advanced formats. |
| `/background_remover/` | `background_remover` | Remove background with AI (rembg). |
| `/audio_converter/` | `audio_converter` | Convert audio files (bitrate-aware presets). |
| `/video_converter/` | `video_converter` | Convert videos with curated FFmpeg groups. |
| `/url_shortener/` | `url_shortener` | Shorten URLs, allow custom codes and view stats. |

Each route has a matching API namespace (`/api/...`) for programmatic use.

## API Examples

All endpoints respond with JSON. Example: convert an image to WebP.

```bash
curl -F "images=@photo.jpg" -F "target_format=webp" \
  http://localhost:4666/api/image/convert
```

Successful responses include `"status": "success"` and tool-specific fields such as download URLs or file lists. Errors respond with `"status": "error"` plus an explanatory message.

## Housekeeping

- Automatic cleanup runs on startup; trigger it manually with:

  ```bash
  flask --app app cleanup
  ```

- Temporary files live in `uploads/` and processed assets in `static/<tool>/...`. Review retention values before deploying to production.

## Deployment Guide

### 1. Prepare the container

The root `Dockerfile` and `cloudbuild.yaml` are ready for Cloud Build/Run. Build and deploy in one step:

```bash
gcloud builds submit --config cloudbuild.yaml
```

The provided configuration builds the image and deploys it to Cloud Run as `firetools` (region `us-central1`).

Alternatively, build manually:

```bash
docker build -t gcr.io/PROJECT_ID/firetools .
docker push gcr.io/PROJECT_ID/firetools
gcloud run deploy firetools \
  --image gcr.io/PROJECT_ID/firetools \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

Remember to set all required environment variables inside the Cloud Run service (`SECRET_KEY`, size limits, rate-limit backend, etc.).

### 2. Post-deploy checklist

- Verify the PDF converter (DOCX + PNG) using a sample file.
- Confirm audio/video conversions — FFmpeg must be available in the runtime image.
- Exercise the URL shortener (custom code + history + stats endpoint).
- Switch the UI language toggle to ensure `/static/js/i18n-en.json` loads correctly.
- Inspect logs for rate-limit storage warnings and configure `RATELIMIT_STORAGE_URI` if needed.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'flask'`** – activate the virtual environment or install dependencies with `pip install -r requirements.txt`.
- **FFmpeg errors during video/audio conversion** – install a system FFmpeg binary or adjust `PATH` so `imageio-ffmpeg` can locate it.
- **Rate limiting resets between requests** – configure a persistent backend for Flask-Limiter using `RATELIMIT_STORAGE_URI` (e.g. Redis connection string).
- **Large files rejected** – increase `MAX_UPLOAD_MB` and the relevant per-tool limit (`IMAGE_MAX_FILE_SIZE_MB`, etc.).

---

FireTools is under active development. Contributions, issue reports and deployment feedback are welcome!
