# Argus

[![CI](https://github.com/Chafficui/argus/actions/workflows/ci.yml/badge.svg)](https://github.com/Chafficui/argus/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)

**Self-hosted AI research platform for monitoring web sources and answering questions with RAG.**

Argus continuously crawls websites, RSS feeds, and search engine results, indexes the content into a vector database, and lets you ask natural-language questions across everything it has collected. Fully on-premise — your data never leaves your infrastructure.

## Architecture

![Architecture](docs/architecture.png)

| Component | Role |
|---|---|
| **FastAPI Backend** | REST API, document processing, RAG pipeline |
| **Crawler Service** | Playwright-based scraping of websites, RSS, and SearXNG SERP results |
| **React Frontend** | Dashboard UI for managing sources and querying documents |
| **PostgreSQL** | Relational storage for users, sources, documents, crawl jobs |
| **Milvus** | Vector database for semantic similarity search |
| **Ollama** | Local LLM inference for embeddings and RAG answers |
| **MinIO** | S3-compatible object storage for raw and processed documents |
| **Keycloak** | OpenID Connect identity provider |
| **Prometheus + Grafana** | Metrics collection and dashboards |
| **Loki + Promtail** | Log aggregation and search |

## Quick Start

Prerequisites: [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/).

```bash
# Clone the repo
git clone https://github.com/Chafficui/argus.git
cd argus

# Start the full stack (backend, databases, observability)
docker compose -f docker-compose.dev.yml up -d

# Pull the required Ollama models
docker exec argus-ollama ollama pull nomic-embed-text
docker exec argus-ollama ollama pull llama3.2

# Verify the backend is running
curl http://localhost:8000/health
```

Once everything is up:

| Service | URL |
|---|---|
| Backend API | http://localhost:8000/docs |
| Grafana | http://localhost:3000 (admin / admin) |
| Prometheus | http://localhost:9090 |
| MinIO Console | http://localhost:9001 (argus-minio / argus-minio-secret) |

### Create a source and run a query

```bash
# Create a website source
curl -X POST http://localhost:8000/api/sources/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Example", "url": "https://example.com", "source_type": "website"}'

# After the crawler has indexed the source, ask a question
curl -X POST http://localhost:8000/api/search/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this website about?"}'
```

## Stack

| Layer | Technology |
|---|---|
| AI Agent | LangChain + LangGraph |
| LLM Inference | Ollama (on-premise, OpenAI-compatible) |
| Vector DB | Milvus |
| Backend | Python / FastAPI |
| Frontend | React + Vite |
| Auth / IAM | Keycloak (OIDC) |
| Orchestration | Kubernetes + Helm |
| Object Storage | MinIO |
| Relational DB | PostgreSQL |
| Observability | Prometheus + Grafana + Loki |
| Crawling | Playwright |

## Development

### Setup

```bash
cd services/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
```

### Running Tests

```bash
# Unit tests (no Docker needed)
pytest -m unit

# Integration tests (needs Docker services running)
pytest -m integration

# All tests
pytest
```

### Environment Variables

All configuration is managed through environment variables via [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/). Defaults are tuned for local development with `docker-compose.dev.yml`. See [config.py](services/backend/app/core/config.py) for the full list.

Key variables:

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | `development` or `production` |
| `DEV_AUTH_BYPASS` | `false` | Skip JWT validation in development |
| `POSTGRES_HOST` | `localhost` | PostgreSQL hostname |
| `MILVUS_HOST` | `localhost` | Milvus hostname |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `LOG_LEVEL` | `info` | Logging level |

## Project Structure

```
argus/
├── charts/argus/             # Helm chart (Kubernetes deployment)
├── docs/                     # Architecture diagrams
├── infra/                    # Prometheus, Grafana, Loki configs
│   ├── prometheus.yml
│   ├── promtail.yml
│   └── grafana/provisioning/ # Auto-provisioned datasources + dashboards
├── services/
│   ├── backend/              # FastAPI backend (Python)
│   └── crawler/              # Playwright crawler (Python)
├── docker-compose.dev.yml    # Local dev stack
├── CONTRIBUTING.md
└── LICENSE
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for commit conventions, branch naming, and code style guidelines.

## License

[MIT](LICENSE)
