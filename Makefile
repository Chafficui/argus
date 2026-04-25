.PHONY: help dev dev-down dev-clean pull-models test test-backend test-crawler test-frontend lint build

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

dev: ## Start all services (Docker Compose)
	docker compose -f docker-compose.dev.yml up -d

dev-down: ## Stop all services
	docker compose -f docker-compose.dev.yml down

dev-clean: ## Stop all services and remove volumes
	docker compose -f docker-compose.dev.yml down -v

pull-models: ## Pull Ollama models (llama3.2 + nomic-embed-text)
	docker exec argus-ollama ollama pull llama3.2
	docker exec argus-ollama ollama pull nomic-embed-text

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: test-backend test-crawler test-frontend ## Run all tests

test-backend: ## Run backend unit tests
	cd services/backend && python -m pytest tests/unit -m unit -v

test-crawler: ## Run crawler unit tests
	cd services/crawler && python -m pytest tests/unit -m unit -v

test-frontend: ## Run frontend type check and lint
	cd services/frontend && npx tsc --noEmit && npx eslint src/

# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------

lint: ## Lint and format-check backend code
	cd services/backend && ruff check app/ && ruff format app/ --check

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

build: ## Build all Docker images locally
	docker build -t argus-backend services/backend
	docker build -t argus-frontend services/frontend
	docker build -t argus-crawler services/crawler
