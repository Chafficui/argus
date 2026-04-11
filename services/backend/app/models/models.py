# =============================================================================
# app/models/models.py
# =============================================================================
# SQLAlchemy ORM models — the Python representation of database tables.
#
# WHAT IS AN ORM?
# ORM = Object-Relational Mapper.
# Instead of writing raw SQL:
#   INSERT INTO sources (url, name, user_id) VALUES ('https://...', 'TechBlog', 'user-123')
# You write Python:
#   db.add(Source(url="https://...", name="TechBlog", user_id="user-123"))
# SQLAlchemy translates that to SQL for you.
#
# TABLE STRUCTURE:
#   users          ← mirrored from Keycloak (we store user prefs here)
#   sources        ← URLs/feeds that Argus monitors
#   documents      ← crawled content from sources
#   crawl_jobs     ← history of crawl runs (success/failure/timing)
# =============================================================================

from sqlalchemy import (
    Column, String, Boolean, Integer, Float,
    DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
import enum
import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Base class for all models — gives us created_at/updated_at for free."""
    pass


# =============================================================================
# ENUMS
# Enums constrain a column to a fixed set of values.
# PostgreSQL stores these efficiently and enforces the constraint at DB level.
# =============================================================================

class SourceType(str, enum.Enum):
    RSS = "rss"           # RSS/Atom feed — structured, easy to parse
    WEBSITE = "website"   # Regular webpage — crawled with Playwright
    SERP = "serp"         # Search Engine Results Page — query + monitor results


class CrawlStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class DocumentStatus(str, enum.Enum):
    RAW = "raw"               # Just crawled, not yet processed
    CHUNKED = "chunked"       # Split into chunks
    EMBEDDED = "embedded"     # Vectors stored in Milvus — ready for search
    FAILED = "failed"


# =============================================================================
# MODELS
# =============================================================================

class User(Base):
    """
    Mirrors Keycloak users in our database.
    We don't store passwords — Keycloak handles auth.
    We just store preferences and track activity.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    # keycloak_id is the "sub" claim from the JWT — the user's Keycloak UUID
    # This is how we link a JWT token to a database user
    keycloak_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships — SQLAlchemy can automatically join related tables
    sources = relationship("Source", back_populates="owner", cascade="all, delete-orphan")


class Source(Base):
    """
    A monitored source — a URL that Argus watches and crawls periodically.
    Could be an RSS feed, a website, or a search query.
    """
    __tablename__ = "sources"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    source_type = Column(Enum(SourceType), nullable=False, default=SourceType.WEBSITE)
    is_active = Column(Boolean, default=True)

    # For SERP sources: the search query to monitor
    search_query = Column(String, nullable=True)

    # Crawl schedule — how often to check this source
    # Stored as hours between crawls (e.g. 6 = every 6 hours)
    crawl_interval_hours = Column(Integer, default=6)
    last_crawled_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="sources")
    documents = relationship("Document", back_populates="source", cascade="all, delete-orphan")
    crawl_jobs = relationship("CrawlJob", back_populates="source", cascade="all, delete-orphan")


class Document(Base):
    """
    A single piece of content crawled from a source.
    One source can have many documents (e.g. one per article).

    The actual text content is stored in MinIO (object storage).
    Here we store metadata + reference to the MinIO object.

    The vector embeddings are stored in Milvus (vector DB).
    Here we store the Milvus document ID so we can cross-reference.
    """
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    source_id = Column(String, ForeignKey("sources.id"), nullable=False, index=True)

    # Content metadata
    title = Column(String, nullable=True)
    url = Column(String, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Content storage
    # Full raw content is in MinIO at this path (e.g. "argus-raw-docs/doc-uuid.html")
    minio_path = Column(String, nullable=True)
    # Summary stored directly in postgres (short enough)
    summary = Column(Text, nullable=True)
    # Word count — useful for UI display
    word_count = Column(Integer, nullable=True)

    # Milvus references — list of chunk IDs stored in Milvus
    # We store as comma-separated string for simplicity
    # (in production you'd use a separate chunk table or JSONB column)
    milvus_chunk_ids = Column(Text, nullable=True)

    status = Column(Enum(DocumentStatus), default=DocumentStatus.RAW)

    # Content hash — to detect if a page has changed since last crawl
    content_hash = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    source = relationship("Source", back_populates="documents")


class CrawlJob(Base):
    """
    A record of a crawl attempt — success or failure.
    This gives us an audit log and helps with debugging.
    Also provides data for the Grafana dashboard (crawl success rate, timing etc.)
    """
    __tablename__ = "crawl_jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    source_id = Column(String, ForeignKey("sources.id"), nullable=False, index=True)

    status = Column(Enum(CrawlStatus), default=CrawlStatus.PENDING)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    # How many new documents were found in this crawl
    documents_found = Column(Integer, default=0)
    documents_indexed = Column(Integer, default=0)

    # Error message if status = FAILED
    error_message = Column(Text, nullable=True)

    # Duration in seconds (computed after crawl finishes)
    duration_seconds = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source = relationship("Source", back_populates="crawl_jobs")
