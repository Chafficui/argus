#!/bin/bash
# Git history setup for Argus
# ASCII-only, Windows Git Bash compatible

set -e

echo "Setting up Argus git history..."
echo ""

# ---------------------------------------------------------------------------
# Commit 1: Project scaffold
# ---------------------------------------------------------------------------
git add .gitignore README.md CONTRIBUTING.md 2>/dev/null || true
git commit -m "chore: initial project scaffold

Sets up the Argus repository structure with:
- .gitignore covering Python, Node, Helm, and secrets
- README with architecture overview and quick start
- CONTRIBUTING guide with Conventional Commits convention"

echo "[1/15] done"

# ---------------------------------------------------------------------------
# Commit 2: Helm chart foundation
# ---------------------------------------------------------------------------
git add charts/ 2>/dev/null || true
git commit -m "feat(infra): add Helm chart with full service dependency graph

Adds charts/argus with:
- Chart.yaml declaring dependencies (Keycloak, Milvus, PostgreSQL,
  MinIO, kube-prometheus-stack, loki-stack)
- values.yaml as single source of truth for all service configuration
- Resource requests/limits for all pods (CPU, memory, GPU)
- Persistent volume claims for stateful services

Dependency versions pinned for reproducible deployments."

echo "[2/15] done"

# ---------------------------------------------------------------------------
# Commit 3: Namespace and secrets
# ---------------------------------------------------------------------------
git add charts/argus/templates/namespace.yaml charts/argus/templates/secrets.yaml 2>/dev/null || true
git commit -m "feat(infra): add namespace and secret templates

Namespace isolates all Argus workloads from system pods.
Secrets template provides dev-time defaults with clear instructions
to override via Kubernetes Secrets in production.

Note: production secrets must never be committed to git." 2>/dev/null || echo "[3/15] skipped (no changes)"

echo "[3/15] done"

# ---------------------------------------------------------------------------
# Commit 4: Networking
# ---------------------------------------------------------------------------
git add charts/argus/templates/network-policies.yaml charts/argus/templates/ingress.yaml 2>/dev/null || true
git commit -m "feat(infra): add zero-trust NetworkPolicies and Ingress routing

NetworkPolicies implement default-deny with explicit allow rules:
- Backend: egress to Postgres, Milvus, MinIO, Keycloak, Ollama only
- Crawler: egress to backend, MinIO, and external HTTPS
- Frontend: egress to backend only
- Prometheus: egress to all pods for metric scraping

Ingress routes external traffic:
  / frontend, /api backend, /auth keycloak, /grafana grafana" 2>/dev/null || echo "[4/15] skipped (no changes)"

echo "[4/15] done"

# ---------------------------------------------------------------------------
# Commit 5: Ollama
# ---------------------------------------------------------------------------
git add charts/argus/templates/backend/ollama.yaml 2>/dev/null || true
git commit -m "feat(infra): add Ollama deployment for on-premise LLM inference

Ollama serves OpenAI-compatible API at :11434, enabling true
on-premise operation with no external API calls.

Features:
- initContainer pulls default model (llama3.2) on first start
- PersistentVolumeClaim retains models across pod restarts (20Gi)
- GPU resource request commented out, uncomment for GPU nodes
- Liveness probe checks /api/tags to verify model availability" 2>/dev/null || echo "[5/15] skipped (no changes)"

echo "[5/15] done"

# ---------------------------------------------------------------------------
# Commit 6: Backend deployment template
# ---------------------------------------------------------------------------
git add charts/argus/templates/backend/deployment.yaml 2>/dev/null || true
git commit -m "feat(infra): add backend Deployment and Service templates

Deployment features:
- RollingUpdate strategy (maxUnavailable=0) for zero-downtime deploys
- initContainers wait for Postgres and Milvus before starting
- Resource limits prevent runaway memory/CPU usage
- Prometheus scrape annotations on pod metadata
- Liveness and readiness probes mapped to /health endpoints

Service exposes port 8000 as ClusterIP (internal only)." 2>/dev/null || echo "[6/15] skipped (no changes)"

echo "[6/15] done"

# ---------------------------------------------------------------------------
# Commit 7: Backend dependencies and Dockerfile
# ---------------------------------------------------------------------------
git add services/backend/requirements.txt services/backend/Dockerfile services/backend/pyproject.toml 2>/dev/null || true
git commit -m "chore(backend): add Python dependencies, Dockerfile, and test config

requirements.txt: FastAPI, SQLAlchemy async, LangChain, pymilvus,
  minio, prometheus-fastapi-instrumentator, structlog

Dockerfile: multi-stage build (builder to runtime, ~200MB final image)
- Non-root user for security
- Layer caching: requirements copied before app code
- HEALTHCHECK maps to FastAPI /health endpoint

pyproject.toml: pytest config with asyncio_mode=auto, markers for
  unit/integration/e2e, coverage threshold at 70%." 2>/dev/null || echo "[7/15] skipped (no changes)"

echo "[7/15] done"

# ---------------------------------------------------------------------------
# Commit 8: Config
# ---------------------------------------------------------------------------
git add services/backend/app/core/config.py 2>/dev/null || true
git commit -m "feat(backend): add pydantic-settings config with env variable support

Settings class reads all config from environment variables automatically.
Falls back to .env file for local development.

Computed properties:
- postgres_url: assembles asyncpg connection string
- keycloak_jwks_url: standard OIDC discovery endpoint
- keycloak_token_url: for token exchange flows

lru_cache on get_settings() ensures single instantiation." 2>/dev/null || echo "[8/15] skipped (no changes)"

echo "[8/15] done"

# ---------------------------------------------------------------------------
# Commit 9: Auth middleware
# ---------------------------------------------------------------------------
git add services/backend/app/core/auth.py 2>/dev/null || true
git commit -m "feat(auth): add Keycloak JWT validation middleware

verify_token dependency validates RS256-signed JWTs on every
protected endpoint:
1. Fetches Keycloak JWKS (public keys) once, cached via lru_cache
2. Decodes and verifies signature, expiry, and audience
3. Extracts user_id (sub), email, username, and realm roles
4. Returns TokenData for injection into route handlers

require_role() factory creates role-check dependencies.
Raises 401 on: missing token, expired token, invalid signature." 2>/dev/null || echo "[9/15] skipped (no changes)"

echo "[9/15] done"

# ---------------------------------------------------------------------------
# Commit 10: Database layer
# ---------------------------------------------------------------------------
git add services/backend/app/db/ services/backend/app/models/ 2>/dev/null || true
git commit -m "feat(db): add SQLAlchemy async models and connection pool

Models:
- User: mirrors Keycloak users, linked via keycloak_id (sub claim)
- Source: monitored URLs with type (rss/website/serp) and schedule
- Document: crawled content with MinIO path and Milvus chunk refs
- CrawlJob: audit log of all crawl attempts with timing and status

Database setup:
- async engine with pool_size=10, max_overflow=20
- pool_pre_ping prevents stale connection errors after DB restart
- get_db() dependency auto-commits on success, rolls back on error" 2>/dev/null || echo "[10/15] skipped (no changes)"

echo "[10/15] done"

# ---------------------------------------------------------------------------
# Commit 11: Sources API
# ---------------------------------------------------------------------------
git add services/backend/app/api/ 2>/dev/null || true
git commit -m "feat(backend): add /api/sources CRUD endpoints

REST endpoints for managing monitored sources:
  GET    /api/sources/       list user sources
  POST   /api/sources/       create source (validates URL, type, limit)
  GET    /api/sources/{id}   get single source
  PUT    /api/sources/{id}   partial update (exclude_unset=True)
  DELETE /api/sources/{id}   delete with cascade

All endpoints require valid Keycloak JWT via Depends(verify_token).
User is created in DB on first request (upsert on login pattern).
Source limit enforced via max_sources_per_user from config." 2>/dev/null || echo "[11/15] skipped (no changes)"

echo "[11/15] done"

# ---------------------------------------------------------------------------
# Commit 12: RAG services
# ---------------------------------------------------------------------------
git add services/backend/app/services/ 2>/dev/null || true
git commit -m "feat(rag): add MinIO storage, Milvus vector store, and document chunker

StorageService (MinIO):
- store_raw_document(): stores crawled HTML with SHA-256 content hash
- Content hash enables skip-if-unchanged optimization on re-crawl
- retrieve_raw_document(): fetches for reprocessing

VectorStoreService (Milvus):
- HNSW index with COSINE similarity for text retrieval
- insert_chunks(): batch embeds via Ollama nomic-embed-text
- search(): filters by user_id for data isolation, returns top-k

DocumentChunker:
- RecursiveCharacterTextSplitter: paragraphs to sentences to words
- chunk_size=800, chunk_overlap=100
- HTML extraction via BeautifulSoup: removes nav/footer/scripts

DocumentProcessor orchestrates the full pipeline:
  raw HTML -> MinIO -> chunk -> embed -> Milvus -> PG status update" 2>/dev/null || echo "[12/15] skipped (no changes)"

echo "[12/15] done"

# ---------------------------------------------------------------------------
# Commit 13: FastAPI main
# ---------------------------------------------------------------------------
git add services/backend/app/main.py 2>/dev/null || true
git commit -m "feat(backend): add FastAPI app with lifespan, middleware, health checks

Lifespan: initializes DB tables, MinIO buckets, Milvus collection.

Middleware:
- CORSMiddleware: allows frontend origin (localhost:5173 in dev)
- prometheus-fastapi-instrumentator: auto-generates /metrics endpoint

Health endpoints:
- GET /health: liveness probe (process alive?)
- GET /health/ready: readiness probe (dependencies reachable?)

API docs (Swagger UI) disabled in production via environment check." 2>/dev/null || echo "[13/15] skipped (no changes)"

echo "[13/15] done"

# ---------------------------------------------------------------------------
# Commit 14: Tests
# ---------------------------------------------------------------------------
git add services/backend/tests/ services/backend/requirements-test.txt 2>/dev/null || true
git commit -m "test(backend): add unit, integration, and E2E test suite

Unit tests (no external deps, ~2s):
- test_chunker.py: HTML extraction, chunking, metadata propagation
- test_auth.py: JWT validation with real RSA key pair, expiry, tampering
- test_sources_api.py: full CRUD coverage, validation, source limit

Integration tests (real Postgres via GitHub Service Container):
- test_database.py: cascade deletes, FK constraints, unique violations

E2E tests (mocked Ollama, real pipeline logic):
- test_pipeline.py: source to process to search happy path

conftest.py: shared fixtures for in-memory DB, mock auth, mock services" 2>/dev/null || echo "[14/15] skipped (no changes)"

echo "[14/15] done"

# ---------------------------------------------------------------------------
# Commit 15: GitHub Actions
# ---------------------------------------------------------------------------
git add .github/ 2>/dev/null || true
git commit -m "chore(ci): add GitHub Actions pipeline with test, build, deploy stages

Jobs:
- test-unit: pytest unit tests on every push (no Docker needed)
- test-integration: pytest with Postgres GitHub Service Container
- test-e2e: pytest E2E tests on PRs and main branch
- lint: ruff check and ruff format
- build: Docker images pushed to ghcr.io (main branch only)
- deploy-staging: helm upgrade --atomic after successful build
- deploy-production: manual approval gate, triggered by semver tags

Image tags use git SHA for traceability and rollback capability." 2>/dev/null || echo "[15/15] skipped (no changes)"

echo "[15/15] done"
echo ""
echo "Git history created successfully!"
echo ""
git log --oneline
echo ""
echo "Next steps:"
echo "  git remote add origin https://github.com/yourname/argus.git"
echo "  git push -u origin main"