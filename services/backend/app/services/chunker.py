# =============================================================================
# app/services/chunker.py
# =============================================================================
# Splits documents into chunks suitable for embedding and retrieval.
#
# WHY DO WE CHUNK?
# Problem 1 — Context window limits:
#   Embedding models have a max input size (e.g. 512 tokens for nomic-embed-text).
#   A 5000-word article can't be embedded as one unit.
#
# Problem 2 — Retrieval precision:
#   If you embed an entire article as one vector, the vector is a "blur" of all topics.
#   A search for "EU AI Act penalties" might match an article that mentions this
#   in one paragraph but is mostly about something else.
#   With chunks, you surface the exact paragraph — much more precise.
#
# Problem 3 — LLM context window:
#   The LLM gets the retrieved chunks as context. Smaller, focused chunks =
#   more relevant information in fewer tokens.
#
# CHUNKING STRATEGIES:
#   Fixed-size: split every N characters (simple, loses sentence boundaries)
#   Sentence-based: split on sentences (better, but uneven sizes)
#   Recursive: try to split on paragraphs → sentences → words (best — what we use)
#   Semantic: use embeddings to find natural topic boundaries (most advanced)
#
# OVERLAP:
#   Chunks overlap by ~10-20%. Why?
#   "The regulation applies to high-risk AI systems. | These include..."
#   Without overlap, "These" loses its reference.
#   With overlap, both chunks contain the bridging context.
# =============================================================================

from langchain_text_splitters import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
import re
import structlog

log = structlog.get_logger()


class DocumentChunker:
    """
    Handles all document parsing and chunking logic.
    """

    def __init__(
        self,
        chunk_size: int = 800,      # Target size in characters
        chunk_overlap: int = 100,   # Overlap between consecutive chunks
    ):
        # RecursiveCharacterTextSplitter tries to split on these separators IN ORDER:
        # First tries to split on double newlines (paragraphs)
        # If chunk is still too big, tries single newlines
        # Then sentences (". ")
        # Then words (" ")
        # Last resort: characters
        # This preserves natural language boundaries as much as possible.
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
            length_function=len,
        )

    def extract_text_from_html(self, html: bytes | str) -> tuple[str, dict]:
        """
        Extracts clean text and metadata from raw HTML.

        Returns:
            (clean_text, metadata)
            metadata: title, description, canonical URL etc.
        """
        if isinstance(html, bytes):
            html = html.decode("utf-8", errors="replace")

        soup = BeautifulSoup(html, "html.parser")

        # Extract metadata from <head>
        metadata = {}

        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)

        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag:
            metadata["description"] = desc_tag.get("content", "")

        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        if canonical_tag:
            metadata["canonical_url"] = canonical_tag.get("href", "")

        # Remove noise elements — nav, footer, ads, scripts etc.
        # These add tokens without adding searchable content.
        noise_tags = [
            "script", "style", "nav", "footer", "header",
            "aside", "advertisement", "cookie-banner",
            "noscript", "iframe", "form",
        ]
        for tag in soup.find_all(noise_tags):
            tag.decompose()  # Remove from DOM

        # Also remove elements whose class list contains an exact noise class name.
        # We check each CSS class individually to avoid substring false positives
        # (e.g. "ad" matching "download" or "header" matching "in-header-enabled").
        noise_classes = {"nav", "menu", "sidebar", "footer", "header", "ad", "banner", "cookie"}
        for tag in soup.find_all(class_=True):
            tag_classes = {c.lower() for c in tag.get("class", [])}
            if tag_classes & noise_classes:
                tag.decompose()

        # Try to find the main content area first
        main_content = (
            soup.find("main") or
            soup.find("article") or
            soup.find(id=re.compile(r"content|main|article", re.I)) or
            soup.find(class_=re.compile(r"content|main|article|post", re.I)) or
            soup.body
        )

        if main_content is None:
            return "", metadata

        # Extract text block-by-block to preserve paragraph structure
        # while collapsing whitespace within each block element.
        block_tags = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6",
                      "li", "blockquote", "pre", "section", "article"}
        blocks = []
        for element in main_content.find_all(block_tags):
            block_text = element.get_text(separator=" ", strip=True)
            block_text = re.sub(r"\s+", " ", block_text).strip()
            if block_text:
                blocks.append(block_text)
        text = "\n".join(blocks)
        text = re.sub(r"\n{3,}", "\n\n", text)   # Max 2 consecutive newlines

        log.debug("Extracted text from HTML", chars=len(text), title=metadata.get("title"))
        return text, metadata

    def chunk_text(
        self,
        text: str,
        document_id: str,
        source_id: str,
        user_id: str,
        metadata: dict | None = None,
    ) -> list[dict]:
        """
        Splits text into chunks and attaches metadata to each.

        Returns list of chunk dicts ready for insertion into Milvus.
        """
        if not text.strip():
            log.warning("Empty text, skipping chunking", document_id=document_id)
            return []

        raw_chunks = self.splitter.split_text(text)

        # Filter out chunks that are too short to be meaningful
        # (e.g. a chunk that's just "Read more..." or a page number)
        min_chunk_length = 50
        chunks = [c for c in raw_chunks if len(c.strip()) >= min_chunk_length]

        log.info(
            "Chunked document",
            document_id=document_id,
            total_chunks=len(raw_chunks),
            valid_chunks=len(chunks),
        )

        metadata = metadata or {}

        return [
            {
                "document_id": document_id,
                "source_id": source_id,
                "user_id": user_id,
                "text": chunk,
                "title": metadata.get("title", ""),
                "url": metadata.get("url", ""),
                "chunk_index": i,
            }
            for i, chunk in enumerate(chunks)
        ]

    def chunk_html_document(
        self,
        html: bytes | str,
        document_id: str,
        source_id: str,
        user_id: str,
        url: str = "",
    ) -> tuple[list[dict], dict]:
        """
        Full pipeline: HTML → extract text → chunk → return chunks + metadata.
        This is the main entry point for crawled web pages.
        """
        text, metadata = self.extract_text_from_html(html)
        metadata["url"] = url

        chunks = self.chunk_text(
            text=text,
            document_id=document_id,
            source_id=source_id,
            user_id=user_id,
            metadata=metadata,
        )

        return chunks, metadata


# Singleton
chunker = DocumentChunker()
