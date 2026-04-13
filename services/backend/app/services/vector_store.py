# =============================================================================
# app/services/vector_store.py
# =============================================================================
# Milvus service — stores and searches vector embeddings.
#
# WHAT HAPPENS HERE (step by step):
#
# INDEXING (when a new document arrives):
#   1. Text chunk comes in: "The EU AI Act regulates foundation models..."
#   2. We send it to Ollama's embedding model → get back [0.23, -0.87, ...]
#   3. We store that vector in Milvus alongside metadata (doc_id, source_id, text)
#
# SEARCHING (when a user asks a question):
#   1. User query: "What does the EU say about AI regulation?"
#   2. We embed the query with the same model → [0.21, -0.89, ...]
#   3. Milvus finds the N vectors closest to this query vector
#   4. We return the original text chunks those vectors came from
#   5. The LLM uses those chunks to answer the question (that's RAG!)
#
# SIMILARITY METRICS:
# Milvus supports different ways to measure "closeness":
#   - COSINE: angle between vectors (best for text — we use this)
#   - L2: euclidean distance (good for images)
#   - IP: inner product (good for recommendation systems)
# =============================================================================

from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)
from langchain_ollama import OllamaEmbeddings
import uuid
import structlog
from app.core.config import get_settings

log = structlog.get_logger()


# =============================================================================
# COLLECTION SCHEMA
# In Milvus, a "collection" is like a table in SQL.
# The schema defines what fields each record has.
# =============================================================================

def build_schema(embedding_dim: int) -> CollectionSchema:
    """
    Defines the structure of our Milvus collection.

    Fields:
      id          → unique ID for each chunk (string)
      document_id → links back to our PostgreSQL documents table
      source_id   → which source this came from
      text        → the actual text of the chunk (stored for retrieval)
      embedding   → the vector (this is what Milvus indexes and searches)
    """
    fields = [
        FieldSchema(
            name="id",
            dtype=DataType.VARCHAR,
            max_length=64,
            is_primary=True,    # Primary key — must be unique
            auto_id=False,      # We generate IDs ourselves
        ),
        FieldSchema(
            name="document_id",
            dtype=DataType.VARCHAR,
            max_length=64,
        ),
        FieldSchema(
            name="source_id",
            dtype=DataType.VARCHAR,
            max_length=64,
        ),
        FieldSchema(
            name="user_id",
            dtype=DataType.VARCHAR,
            max_length=64,
        ),
        FieldSchema(
            name="text",
            dtype=DataType.VARCHAR,
            max_length=4096,    # Max chunk size in characters
        ),
        FieldSchema(
            name="title",
            dtype=DataType.VARCHAR,
            max_length=512,
        ),
        FieldSchema(
            name="url",
            dtype=DataType.VARCHAR,
            max_length=2048,
        ),
        FieldSchema(
            name="chunk_index",
            dtype=DataType.INT32,   # Position of this chunk within the document
        ),
        FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=embedding_dim,      # Must match the output dimension of the embedding model
        ),
    ]

    return CollectionSchema(
        fields=fields,
        description="Argus document chunks with embeddings",
        enable_dynamic_field=True,  # Allows storing extra fields not in schema
    )


class VectorStoreService:
    """
    Manages the Milvus collection and all vector operations.
    """

    def __init__(self):
        self.settings = get_settings()
        self.collection: Collection | None = None

        # The embedding model — converts text to vectors.
        # We use Ollama so everything stays on-premise.
        # nomic-embed-text is a good open-source embedding model (~274MB).
        self.embeddings = OllamaEmbeddings(
            base_url=self.settings.ollama_base_url,
            model=self.settings.ollama_embedding_model,
        )

    def connect(self):
        """
        Establishes connection to Milvus.
        Called once on startup.
        """
        log.info(
            "Connecting to Milvus",
            host=self.settings.milvus_host,
            port=self.settings.milvus_port,
        )
        connections.connect(
            alias="default",
            host=self.settings.milvus_host,
            port=self.settings.milvus_port,
        )
        self._ensure_collection()

    def _ensure_collection(self):
        """
        Creates the collection if it doesn't exist, loads it if it does.
        Idempotent — safe to call multiple times.
        """
        collection_name = self.settings.milvus_collection
        dim = self.settings.embedding_dimension

        if utility.has_collection(collection_name):
            log.info("Loading existing Milvus collection", name=collection_name)
            self.collection = Collection(collection_name)
            self.collection.load()  # Load into memory for fast search
        else:
            log.info("Creating new Milvus collection", name=collection_name)
            schema = build_schema(dim)
            self.collection = Collection(
                name=collection_name,
                schema=schema,
            )
            self._create_index()
            self.collection.load()

    def _create_index(self):
        """
        Creates a vector index on the embedding field.

        WHY DO WE NEED AN INDEX?
        Without an index, searching 1 million vectors = comparing your query to
        all 1 million vectors one by one. That's O(n) — very slow.

        An index builds a data structure that lets Milvus find approximate
        nearest neighbors much faster (milliseconds instead of seconds).

        Index types:
          HNSW = Hierarchical Navigable Small World — best accuracy/speed tradeoff
          IVF_FLAT = Inverted File Index — good for very large datasets
          FLAT = brute force, no index (only for small datasets / testing)

        We use HNSW. Parameters:
          M = 16: number of connections per node in the graph (higher = more accurate, more memory)
          ef_construction = 200: search width during index build (higher = more accurate, slower build)
        """
        log.info("Creating HNSW index on embedding field")
        self.collection.create_index(
            field_name="embedding",
            index_params={
                "metric_type": "COSINE",    # Cosine similarity for text
                "index_type": "HNSW",
                "params": {
                    "M": 16,
                    "efConstruction": 200,
                },
            },
        )

    # ==========================================================================
    # CORE OPERATIONS
    # ==========================================================================

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Converts a list of text strings to embedding vectors.
        Calls the Ollama embedding model.

        Input:  ["The EU AI Act...", "Foundation models are..."]
        Output: [[0.23, -0.87, ...], [0.11, 0.45, ...]]
        """
        return self.embeddings.embed_documents(texts)

    def embed_query(self, query: str) -> list[float]:
        """
        Embeds a single search query.
        Uses embed_query (slightly different from embed_documents — optimized for queries).
        """
        return self.embeddings.embed_query(query)

    def insert_chunks(self, chunks: list[dict]) -> list[str]:
        """
        Inserts a batch of text chunks into Milvus.

        Each chunk dict:
        {
            "document_id": "...",
            "source_id": "...",
            "user_id": "...",
            "text": "The actual text...",
            "title": "Article title",
            "url": "https://...",
            "chunk_index": 0,
        }

        Returns list of inserted chunk IDs.
        """
        if not chunks:
            return []

        # Generate IDs for each chunk
        chunk_ids = [str(uuid.uuid4()).replace("-", "")[:32] for _ in chunks]

        # Embed all texts in one batch (more efficient than one-by-one)
        texts = [c["text"] for c in chunks]
        log.info("Embedding chunks", count=len(texts))
        embeddings = self.embed_texts(texts)

        # Milvus expects data as parallel lists (one list per field)
        data = [
            chunk_ids,
            [c["document_id"] for c in chunks],
            [c["source_id"] for c in chunks],
            [c["user_id"] for c in chunks],
            [c["text"] for c in chunks],
            [c.get("title", "") for c in chunks],
            [c.get("url", "") for c in chunks],
            [c.get("chunk_index", 0) for c in chunks],
            embeddings,
        ]

        self.collection.insert(data)
        # flush() makes inserts immediately searchable
        # Without this, inserts are buffered and might not appear in search results yet
        self.collection.flush()

        log.info("Inserted chunks into Milvus", count=len(chunks))
        return chunk_ids

    def search(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        source_ids: list[str] | None = None,
    ) -> list[dict]:
        """
        Semantic search: finds the top_k most relevant chunks for a query.

        user_id filter: users can only search their own documents.
        source_ids filter: optionally restrict to specific sources.

        Returns list of result dicts with text, score, and metadata.
        """
        # Embed the query
        query_vector = self.embed_query(query)

        # Build filter expression
        # Milvus filter syntax is similar to Python boolean expressions
        filter_expr = f'user_id == "{user_id}"'
        if source_ids:
            ids_str = ", ".join(f'"{sid}"' for sid in source_ids)
            filter_expr += f" and source_id in [{ids_str}]"

        # Search parameters:
        # ef = search width — higher means more accurate but slower
        # Must be >= top_k
        search_params = {
            "metric_type": "COSINE",
            "params": {"ef": max(top_k * 4, 64)},
        }

        results = self.collection.search(
            data=[query_vector],       # Batch of query vectors (we send 1)
            anns_field="embedding",    # Which field to search
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            # Which fields to return alongside the vector match
            output_fields=["id", "document_id", "source_id", "text", "title", "url", "chunk_index"],
        )

        # results[0] because we searched with one query vector
        hits = results[0]

        formatted = []
        for hit in hits:
            formatted.append({
                "chunk_id": hit.id,
                "document_id": hit.entity.get("document_id"),
                "source_id": hit.entity.get("source_id"),
                "text": hit.entity.get("text"),
                "title": hit.entity.get("title"),
                "url": hit.entity.get("url"),
                "chunk_index": hit.entity.get("chunk_index"),
                # Cosine similarity score: 1.0 = identical, 0.0 = unrelated
                "score": float(hit.score),
            })

        log.info(
            "Vector search completed",
            query_preview=query[:50],
            results=len(formatted),
            top_score=formatted[0]["score"] if formatted else None,
        )
        return formatted

    def delete_by_document(self, document_id: str):
        """Deletes all chunks belonging to a document."""
        self.collection.delete(expr=f'document_id == "{document_id}"')
        log.info("Deleted chunks for document", document_id=document_id)

    def delete_by_source(self, source_id: str):
        """Deletes all chunks belonging to a source."""
        self.collection.delete(expr=f'source_id == "{source_id}"')
        log.info("Deleted chunks for source", source_id=source_id)


# Singleton
vector_store = VectorStoreService()
