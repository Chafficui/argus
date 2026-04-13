# Argus — Enterprise AI Research Platform

> Self-hosted, agent-based source monitoring and RAG search. Fully on-premise.

## Architecture

```
[React Frontend] ──OIDC──► [Keycloak IAM]
       │
       ▼
[nginx Ingress]
       │
       ▼
[FastAPI Backend] ──► [LangGraph Agent]
       │                    │         │
       ▼                    ▼         ▼
[PostgreSQL]           [Milvus]   [Ollama LLM]
       
[Crawler Service] ──► [MinIO Object Storage]
       │
       ▼
  [Web / SERP]

[Prometheus] ◄── all services
[Loki]       ◄── all logs
[Grafana]    ──► Dashboards
```

## Stack

| Layer | Technology |
|---|---|
| AI Agent | LangChain + LangGraph |
| LLM Inference | Ollama (on-premise, OpenAI-compatible) |
| Vector DB | Milvus |
| Backend | Python / FastAPI |
| Frontend | React + Vite |
| Auth/IAM | Keycloak (OIDC) |
| Orchestration | Kubernetes + Helm |
| Object Storage | MinIO |
| Relational DB | PostgreSQL |
| Observability | Prometheus + Grafana + Loki |
| Crawling | Playwright |

## Quick Start (local dev)

```bash
# 1. Install k3s
curl -sfL https://get.k3s.io | sh -

# 2. Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 3. Add Helm repos
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add milvus https://zilliztech.github.io/milvus-helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# 4. Resolve chart dependencies
helm dependency update ./charts/argus

# 5. Deploy everything
helm install argus ./charts/argus --namespace argus --create-namespace

# 6. Add to /etc/hosts
echo "127.0.0.1 argus.local" | sudo tee -a /etc/hosts

# 7. Open browser
open http://argus.local
```

## Project Structure

```
argus/
├── charts/argus/          # Helm chart (K8s deployment)
│   ├── Chart.yaml         # Chart metadata + dependencies
│   ├── values.yaml        # All configuration
│   └── templates/         # K8s resource templates
├── services/
│   ├── backend/           # FastAPI (Python)
│   ├── crawler/           # Playwright scraper
│   └── frontend/          # React app
└── docs/
```