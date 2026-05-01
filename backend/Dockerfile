FROM python:3.12-slim as builder

ARG SUBFINDER_VERSION=2.6.8
ARG HTTPX_VERSION=1.6.10
ARG NUCLEI_VERSION=3.3.8
ARG GAU_VERSION=2.2.4

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  unzip \
  && rm -rf /var/lib/apt/lists/*

# Download tools in single layer
RUN set -eux; \
  arch="$(dpkg --print-architecture)"; \
  case "$arch" in \
  amd64) goarch=amd64 ;; \
  arm64) goarch=arm64 ;; \
  *) exit 1 ;; \
  esac; \
  mkdir -p /tools; \
  curl -fL --retry 6 --retry-delay 5 --retry-all-errors \
  "https://github.com/projectdiscovery/subfinder/releases/download/v${SUBFINDER_VERSION}/subfinder_${SUBFINDER_VERSION}_linux_${goarch}.zip" \
  -o /tmp/subfinder.zip && unzip -oj /tmp/subfinder.zip subfinder -d /tools; \
  curl -fL --retry 6 --retry-delay 5 --retry-all-errors \
  "https://github.com/projectdiscovery/httpx/releases/download/v${HTTPX_VERSION}/httpx_${HTTPX_VERSION}_linux_${goarch}.zip" \
  -o /tmp/httpx.zip && unzip -oj /tmp/httpx.zip httpx -d /tools; \
  curl -fL --retry 6 --retry-delay 5 --retry-all-errors \
  "https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_${goarch}.zip" \
  -o /tmp/nuclei.zip && unzip -oj /tmp/nuclei.zip nuclei -d /tools; \
  curl -fL --retry 6 --retry-delay 5 --retry-all-errors \
  "https://github.com/lc/gau/releases/download/v${GAU_VERSION}/gau_${GAU_VERSION}_linux_${goarch}.tar.gz" \
  -o /tmp/gau.tar.gz && tar -xzf /tmp/gau.tar.gz -C /tools gau; \
  chmod +x /tools/*; \
  rm -rf /tmp/*.zip /tmp/*.tar.gz

# Python dependencies stage
FROM python:3.12-slim as dependencies

WORKDIR /tmp

COPY ./backend/requirements.txt .

# Install dependencies with pip-audit for security vulnerability scanning
RUN pip install --user --no-cache-dir --default-timeout=180 --retries=10 -r requirements.txt && \
    pip install --user --no-cache-dir pip-audit

# Final runtime image
FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1001 appuser

# Set Python path before any operations
ENV PATH=/home/appuser/.local/bin:$PATH \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Copy tools from builder
COPY --from=builder --chown=appuser:appuser /tools /usr/local/bin

# Copy Python dependencies
COPY --from=dependencies --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code (context root is repo root, not backend)
COPY --chown=appuser:appuser ./backend/app /app/app
COPY --chown=appuser:appuser ./backend/alembic /app/alembic
COPY --chown=appuser:appuser ./backend/alembic.ini /app/alembic.ini

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

# Support both API and worker modes via SERVICE_MODE environment variable
# Default: api (uvicorn server)
# Alternative: worker (celery worker), migrate (alembic migrations)
ENV SERVICE_MODE=api

# Shell form is required so ${PORT:-8000} is expanded by sh before exec.
# Do NOT convert to exec-form JSON array — Railway injects PORT at runtime.
CMD sh -c 'case "$SERVICE_MODE" in \
  worker) exec celery -A app.tasks.celery_app.celery_app worker -l info ;; \
  migrate) exec alembic upgrade head ;; \
  *) exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 4 ;; \
  esac'
