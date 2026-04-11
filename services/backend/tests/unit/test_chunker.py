# =============================================================================
# tests/unit/test_chunker.py
# =============================================================================
# Unit tests for the DocumentChunker.
#
# UNIT TEST PHILOSOPHY:
# - Test one thing at a time
# - No external dependencies (no DB, no network)
# - Fast (should run in milliseconds)
# - Descriptive names: test_WHAT_WHEN_EXPECTED
# =============================================================================

import pytest
from app.services.chunker import DocumentChunker


# We create a fresh chunker for each test
# (no shared state — tests are independent)
@pytest.fixture
def chunker():
    return DocumentChunker(chunk_size=500, chunk_overlap=50)


class TestExtractTextFromHtml:
    """Tests for HTML → clean text extraction."""

    @pytest.mark.unit
    def test_extracts_title_from_head(self, chunker, sample_html):
        _, metadata = chunker.extract_text_from_html(sample_html)
        assert metadata["title"] == "EU AI Act: What You Need to Know"

    @pytest.mark.unit
    def test_extracts_main_content(self, chunker, sample_html):
        text, _ = chunker.extract_text_from_html(sample_html)
        assert "EU AI Act" in text
        assert "conformity assessments" in text

    @pytest.mark.unit
    def test_removes_nav_elements(self, chunker, sample_html):
        text, _ = chunker.extract_text_from_html(sample_html)
        # Navigation text should be stripped
        assert "Home | About | Contact" not in text

    @pytest.mark.unit
    def test_removes_footer(self, chunker, sample_html):
        text, _ = chunker.extract_text_from_html(sample_html)
        assert "Copyright 2026" not in text

    @pytest.mark.unit
    def test_handles_empty_html(self, chunker):
        text, metadata = chunker.extract_text_from_html(b"<html></html>")
        assert text == ""
        assert metadata == {}

    @pytest.mark.unit
    def test_handles_bytes_input(self, chunker, sample_html):
        """Should accept both bytes and str."""
        text_from_bytes, _ = chunker.extract_text_from_html(sample_html)
        text_from_str, _ = chunker.extract_text_from_html(sample_html.decode("utf-8"))
        assert text_from_bytes == text_from_str

    @pytest.mark.unit
    def test_handles_malformed_html(self, chunker):
        """BeautifulSoup is forgiving — should not crash on bad HTML."""
        bad_html = b"<html><body><p>Unclosed paragraph<div>Mixed tags</body>"
        text, _ = chunker.extract_text_from_html(bad_html)
        assert "Unclosed paragraph" in text


class TestChunkText:
    """Tests for text → chunks splitting."""

    @pytest.mark.unit
    def test_returns_list_of_dicts(self, chunker):
        chunks = chunker.chunk_text(
            text="A " * 300,  # 600 chars — should produce multiple chunks
            document_id="doc-1",
            source_id="src-1",
            user_id="user-1",
        )
        assert isinstance(chunks, list)
        assert all(isinstance(c, dict) for c in chunks)

    @pytest.mark.unit
    def test_chunk_has_required_fields(self, chunker):
        chunks = chunker.chunk_text(
            text="Some meaningful content that is long enough. " * 20,
            document_id="doc-1",
            source_id="src-1",
            user_id="user-1",
        )
        assert len(chunks) > 0
        required = {"document_id", "source_id", "user_id", "text", "chunk_index"}
        for chunk in chunks:
            assert required.issubset(chunk.keys()), f"Missing fields: {required - chunk.keys()}"

    @pytest.mark.unit
    def test_chunk_indices_are_sequential(self, chunker):
        long_text = "This is a sentence with real content. " * 50
        chunks = chunker.chunk_text(long_text, "doc-1", "src-1", "user-1")
        indices = [c["chunk_index"] for c in chunks]
        assert indices == list(range(len(indices)))

    @pytest.mark.unit
    def test_filters_short_chunks(self, chunker):
        """Chunks shorter than 50 chars should be dropped."""
        chunks = chunker.chunk_text(
            text="Short.\n\n" + "Long enough content here. " * 30,
            document_id="doc-1",
            source_id="src-1",
            user_id="user-1",
        )
        for chunk in chunks:
            assert len(chunk["text"].strip()) >= 50

    @pytest.mark.unit
    def test_empty_text_returns_empty_list(self, chunker):
        chunks = chunker.chunk_text("", "doc-1", "src-1", "user-1")
        assert chunks == []

    @pytest.mark.unit
    def test_whitespace_only_returns_empty_list(self, chunker):
        chunks = chunker.chunk_text("   \n\n\t  ", "doc-1", "src-1", "user-1")
        assert chunks == []

    @pytest.mark.unit
    def test_metadata_attached_to_chunks(self, chunker):
        metadata = {"title": "Test Article", "url": "https://example.com"}
        chunks = chunker.chunk_text(
            text="Real content here. " * 20,
            document_id="doc-1",
            source_id="src-1",
            user_id="user-1",
            metadata=metadata,
        )
        for chunk in chunks:
            assert chunk["title"] == "Test Article"
            assert chunk["url"] == "https://example.com"

    @pytest.mark.unit
    def test_user_id_propagated_to_all_chunks(self, chunker):
        """Critical: user isolation requires user_id on every chunk."""
        chunks = chunker.chunk_text(
            text="Content. " * 50,
            document_id="doc-1",
            source_id="src-1",
            user_id="specific-user-xyz",
        )
        for chunk in chunks:
            assert chunk["user_id"] == "specific-user-xyz"


class TestChunkHtmlDocument:
    """Integration of extract + chunk pipeline."""

    @pytest.mark.unit
    def test_full_pipeline_returns_chunks_and_metadata(self, chunker, sample_html):
        chunks, metadata = chunker.chunk_html_document(
            html=sample_html,
            document_id="doc-1",
            source_id="src-1",
            user_id="user-1",
            url="https://example.com/eu-ai-act",
        )
        assert len(chunks) > 0
        assert metadata["title"] == "EU AI Act: What You Need to Know"
        assert metadata["url"] == "https://example.com/eu-ai-act"

    @pytest.mark.unit
    def test_chunk_text_contains_article_content(self, chunker, sample_html):
        chunks, _ = chunker.chunk_html_document(
            sample_html, "doc-1", "src-1", "user-1"
        )
        all_text = " ".join(c["text"] for c in chunks)
        assert "EU AI Act" in all_text
        assert "Foundation Models" in all_text
