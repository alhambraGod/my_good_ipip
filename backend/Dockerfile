# syntax=docker/dockerfile:1.7
# MindPrism backend — FastAPI on Python 3.11 slim
#
# Build:   docker build -f backend/Dockerfile -t mindprism-backend:latest backend/
# Run:     docker run --rm -p 3001:3001 -e DATABASE_URL=... mindprism-backend
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# WeasyPrint native deps + curl for healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz-subset0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps in a layer that only invalidates when requirements.txt changes.
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy app code last so code edits don't bust the deps layer.
COPY . /app

# Don't ship test artefacts to runtime.
RUN rm -rf /app/tests /app/htmlcov /app/.pytest_cache /app/scripts/__pycache__

# Run as a non-root user.
RUN groupadd -r mindprism && useradd -r -g mindprism mindprism \
    && mkdir -p /var/MindPrism/dev /var/MindPrism/prod /app/logs \
    && chown -R mindprism:mindprism /var/MindPrism /app
USER mindprism

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:3001/api/health || exit 1

# Production-ready: gunicorn + uvicorn workers. Worker count is overridable
# (the deploy scripts read GUNICORN_WORKERS / WEB_CONCURRENCY).
ENV GUNICORN_WORKERS=2 \
    GUNICORN_TIMEOUT=60 \
    GUNICORN_KEEPALIVE=5 \
    GUNICORN_BIND=0.0.0.0:3001

CMD ["sh", "-c", "exec gunicorn main:app \
        --bind ${GUNICORN_BIND} \
        --workers ${GUNICORN_WORKERS} \
        --worker-class uvicorn.workers.UvicornWorker \
        --timeout ${GUNICORN_TIMEOUT} \
        --keep-alive ${GUNICORN_KEEPALIVE} \
        --access-logfile - \
        --error-logfile -"]
