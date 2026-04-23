# =============================================================================
# services/crawler/Dockerfile
# =============================================================================
# Multi-stage build for the Argus crawler service.
# Installs Playwright + Chromium for rendering JavaScript-heavy pages.
# =============================================================================

# --- Stage 1: Build dependencies ---
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Runtime ---
FROM python:3.12-slim

WORKDIR /app

# System deps required by Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Non-root user for security
RUN useradd --create-home appuser

# Install Playwright browsers as appuser so the cache lands in the right home dir
USER appuser
RUN playwright install chromium

COPY . .

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

ENTRYPOINT ["python", "-m", "crawler.main"]
