# Contributing to Argus

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/).
Every commit message must follow this format:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

### Types

| Type | When to use |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `chore` | Build process, tooling, CI |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |

### Scopes

| Scope | What it covers |
|-------|----------------|
| `backend` | FastAPI app, services, models |
| `frontend` | React app |
| `crawler` | Playwright crawler service |
| `infra` | Helm charts, K8s templates |
| `ci` | GitHub Actions workflows |
| `auth` | Keycloak / JWT / auth middleware |
| `rag` | RAG pipeline, chunker, vector store |
| `db` | Database models, migrations |

### Examples

```
feat(rag): add recursive chunking with configurable overlap

Uses LangChain RecursiveCharacterTextSplitter to split documents
into chunks of 800 chars with 100 char overlap. Filters chunks
shorter than 50 chars to avoid noise in search results.
```

```
feat(infra): add NetworkPolicy default-deny with explicit allow rules

Implements zero-trust networking for the argus namespace.
All inter-pod communication must be explicitly allowed.
Prometheus scraping is permitted from all pods.
```

```
fix(auth): clear JWKS cache on token validation failure

Previously, a rotated Keycloak key would cause all auth to fail
until the process restarted. Now clears the lru_cache on JWTError.

Fixes #12
```

```
test(backend): add integration tests for cascade delete behavior

SQLite doesn't enforce FK constraints — needed real Postgres
to catch the missing cascade on Source → CrawlJob relationship.
```

```
chore(ci): add GitHub Actions workflow for unit + integration tests

Runs unit tests on every push, integration tests on PRs and main.
Uses GitHub Service Containers for Postgres (no testcontainers needed).
Coverage report uploaded to Codecov.
```

---

## Branch Naming

```
feat/rag-search-endpoint
fix/auth-jwks-cache-rotation
chore/update-helm-dependencies
docs/architecture-diagram
```

---

## Pull Request Template

See `.github/pull_request_template.md`

---

## Local Development Setup

```bash
# 1. Clone
git clone https://github.com/yourname/argus.git
cd argus

# 2. Backend
cd services/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt

# 3. Run unit tests (no Docker needed)
pytest tests/unit -m unit

# 4. Run integration tests (needs Docker)
pytest tests/integration -m integration

# 5. Start local dev stack (needs k3s + helm)
helm dependency update ./charts/argus
helm install argus ./charts/argus --namespace argus --create-namespace
```

---

## Code Style

- Python: formatted with `ruff format`, linted with `ruff check`
- All public functions must have docstrings
- No `print()` — use `structlog` logging
- No hardcoded secrets — use environment variables via `config.py`
