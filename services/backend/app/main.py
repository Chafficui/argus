# =============================================================================
# app/main.py
# =============================================================================
# The entry point of the FastAPI application.
# This is what uvicorn runs: uvicorn app.main:app
#
# Here we:
#   1. Create the FastAPI app
#   2. Configure middleware (CORS, logging, metrics)
#   3. Register all routers (sources, search, chat)
#   4. Define startup/shutdown lifecycle hooks
# =============================================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
import structlog

import httpx
from sqlalchemy import text

from app.core.config import get_settings
from app.db.database import init_db, AsyncSessionLocal
from app.services.storage import storage_service
from app.services.vector_store import vector_store
from app.api.routes import sources, search

log = structlog.get_logger()
settings = get_settings()


# =============================================================================
# LIFESPAN — code that runs on startup and shutdown
# This is where we initialize DB connections, download models, etc.
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    log.info("Starting Argus backend", version=settings.app_version)

    # Initialize database
    await init_db()

    # Initialize MinIO buckets
    await storage_service.ensure_buckets()

    # Connect to Milvus and ensure collection exists
    vector_store.connect()

    log.info("Argus backend ready")

    yield  # ← app runs here (handles requests)

    # --- SHUTDOWN ---
    log.info("Shutting down Argus backend")


# =============================================================================
# APP CREATION
# =============================================================================

app = FastAPI(
    title="Argus API",
    description="Enterprise AI Research Platform — self-hosted RAG and source monitoring",
    version=settings.app_version,
    # Only show interactive docs in dev (security: don't expose API schema in prod)
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    lifespan=lifespan,
)


# =============================================================================
# MIDDLEWARE
# Middleware wraps every request — think of it as layers around the app.
# Request flows in: CORS → Logging → your route handler
# Response flows out: your route handler → Logging → CORS
# =============================================================================

# CORS (Cross-Origin Resource Sharing)
# Without this, the browser blocks requests from the React frontend (different port)
# to the FastAPI backend — even on the same machine.
# This is a browser security feature. We explicitly allow our frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    # Vite dev server
        "http://localhost:3000",    # Alternative dev port
        f"http://{settings.environment == 'production' and 'argus.local' or 'localhost'}",
    ],
    allow_credentials=True,        # Allow cookies and Authorization headers
    allow_methods=["*"],           # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],           # Allow Authorization header etc.
)


# =============================================================================
# PROMETHEUS METRICS
# The Instrumentator automatically creates a /metrics endpoint.
# It tracks: request count, request duration, response sizes — per endpoint.
# Prometheus scrapes this every 15s and stores the time series.
# Grafana then visualizes it.
# =============================================================================

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# =============================================================================
# ROUTERS
# Each router handles a group of related endpoints.
# We prefix them so the full URL is e.g. /api/sources/
# =============================================================================

app.include_router(sources.router, prefix="/api/sources")
app.include_router(search.router, prefix="/api/search")
# app.include_router(chat.router, prefix="/api/chat")


# =============================================================================
# HEALTH CHECKS
# K8s uses these (defined in our Helm deployment.yaml):
#   /health       → livenessProbe  (is the app alive?)
#   /health/ready → readinessProbe (is the app ready for traffic?)
# =============================================================================

@app.get("/health", tags=["health"])
async def health():
    """Basic liveness check — if this responds, the process is running."""
    return {"status": "ok", "version": settings.app_version}


@app.get("/health/ready", tags=["health"])
async def health_ready():
    """
    Readiness check — only returns 200 if all dependencies are reachable.
    K8s stops sending traffic to this pod if this fails.
    """
    checks = {}

    # Postgres
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e}"

    # Milvus
    try:
        if vector_store.collection is not None:
            _ = vector_store.collection.num_entities
            checks["milvus"] = "ok"
        else:
            checks["milvus"] = "error: not connected"
    except Exception as e:
        checks["milvus"] = f"error: {e}"

    # Ollama
    try:
        resp = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
        resp.raise_for_status()
        checks["ollama"] = "ok"
    except Exception as e:
        checks["ollama"] = f"error: {e}"

    if any(v != "ok" for v in checks.values()):
        raise HTTPException(
            status_code=503,
            detail={"status": "not ready", "dependencies": checks},
        )

    return {"status": "ready", "dependencies": checks}
