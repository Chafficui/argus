# =============================================================================
# Dockerfile — Backend
# =============================================================================
# A Dockerfile defines how to build a container image.
# Think of it as a recipe: start with a base, add ingredients step by step.
#
# MULTI-STAGE BUILD:
# We use two stages — "builder" and "runtime".
# Why? The builder needs compilers and build tools (big).
# The runtime only needs the compiled output (small).
# Final image is ~200MB instead of ~800MB.
# Smaller images = faster deployments, less attack surface.
# =============================================================================

# ---- Stage 1: Builder ----
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies (needed to compile some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first — Docker caches this layer.
# If requirements.txt hasn't changed, Docker skips the pip install step.
# This makes rebuilds much faster when you only change application code.
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Stage 2: Runtime ----
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install only runtime system dependencies (no compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \       
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

# Create a non-root user — security best practice
# Running as root inside a container is dangerous: if the app is compromised,
# the attacker has root access to the container filesystem.
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

# Document which port the app listens on (informational only — doesn't open the port)
EXPOSE 8000

# Health check — Docker itself will mark the container as unhealthy if this fails
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# The command that starts the app
# uvicorn: the ASGI server (like Node.js for Python async apps)
# --host 0.0.0.0: listen on all interfaces (required inside container)
# --workers 2: 2 worker processes (adjust based on CPU cores)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
