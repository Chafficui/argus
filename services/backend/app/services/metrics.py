"""
Argus-specific Prometheus metrics.

These go beyond HTTP metrics (handled by prometheus-fastapi-instrumentator)
to track business-level events: RAG queries, crawl operations, document indexing.
"""

from prometheus_client import Counter, Histogram, Gauge

# =============================================================================
# RAG search metrics
# =============================================================================

rag_queries_total = Counter(
    "argus_rag_queries_total",
    "Total number of RAG /ask queries",
    ["status"],
)

rag_query_duration_seconds = Histogram(
    "argus_rag_query_duration_seconds",
    "Time from query received to LLM response returned",
    buckets=[1, 5, 10, 30, 60, 120],
)

rag_chunks_retrieved = Histogram(
    "argus_rag_chunks_retrieved",
    "Number of chunks passed to LLM per query",
    buckets=[0, 1, 2, 3, 5, 10],
)

# =============================================================================
# Crawl operation metrics
# =============================================================================

crawl_jobs_total = Counter(
    "argus_crawl_jobs_total",
    "Total crawl jobs completed",
    ["status", "source_type"],
)

crawl_duration_seconds = Histogram(
    "argus_crawl_duration_seconds",
    "Duration of a single source crawl cycle",
    ["source_type"],
    buckets=[10, 30, 60, 120, 300, 600],
)

documents_indexed_total = Counter(
    "argus_documents_indexed_total",
    "Total documents successfully embedded into Milvus",
)

# =============================================================================
# System state
# =============================================================================

active_sources_gauge = Gauge(
    "argus_active_sources_total",
    "Current number of active monitored sources",
)
