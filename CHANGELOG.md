# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-04-25

### Added

- RAG pipeline: semantic search + LLM-powered Q&A with source citations
- Keycloak OIDC authentication with PKCE and role-based access control
- Playwright-based crawler supporting website, RSS, and SERP sources
- Milvus vector database for semantic embeddings (nomic-embed-text)
- Ollama local LLM inference (llama3.2) — fully on-premise, no external API calls
- MinIO object storage for crawled documents
- PostgreSQL for relational data (sources, users, crawl jobs)
- Custom Helm chart for Kubernetes deployment
- CI/CD pipeline with GitHub Actions (test, lint, build, deploy)
- Network policies with default-deny and explicit allow rules
- Staging deployment on k3s VPS with TLS via cert-manager
- Observatory design system (dark theme, Tailwind CSS v4)
- Docker Compose development environment with all services
- Prometheus metrics endpoint on backend

### Changed

- Replaced Bitnami Helm subcharts (PostgreSQL, MinIO, Keycloak) with custom templates using official Docker images

### Fixed

- Keycloak startup probe timing for first-boot Quarkus build on resource-constrained nodes
- Milvus externalS3 configuration for MinIO connectivity
- Ingress network policies for k3s Traefik and ACME HTTP-01 challenges
- Ollama egress policy for model registry access
