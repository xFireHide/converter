# Base image
FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies separately to leverage Docker layer cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt && \
    echo "=== Installed packages ===" && \
    pip list | grep -E "(imageio|moviepy|click)" && \
    echo "=== Testing imports ===" && \
    python -c "import imageio_ffmpeg; print('imageio_ffmpeg import successful')" && \
    python -c "import click; print('click import successful')"

# Copy source
COPY . .

# Test app import (will fail build if import fails)
RUN echo "=== Testing app import ===" && \
    python -c "import sys; sys.path.append('.'); from app import app; print('App import successful'); print('App name:', app.name)" || (echo "=== App import FAILED ===" && exit 1)

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads /app/processed /app/static/image/converter/uploads /app/static/audio/converter/converted /app/static/video/converter/converted /app/static/image/background_remover/uploads

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Gunicorn server
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
