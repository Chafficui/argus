import pytest
from unittest.mock import MagicMock, patch
from pymilvus import DataType


class TestBuildSchema:

    @pytest.mark.unit
    def test_schema_has_expected_fields(self):
        from app.services.vector_store import build_schema

        schema = build_schema(embedding_dim=768)
        field_names = [f.name for f in schema.fields]

        assert "id" in field_names
        assert "document_id" in field_names
        assert "source_id" in field_names
        assert "user_id" in field_names
        assert "text" in field_names
        assert "title" in field_names
        assert "url" in field_names
        assert "chunk_index" in field_names
        assert "embedding" in field_names

    @pytest.mark.unit
    def test_id_is_primary_key(self):
        from app.services.vector_store import build_schema

        schema = build_schema(embedding_dim=768)
        id_field = next(f for f in schema.fields if f.name == "id")

        assert id_field.is_primary is True

    @pytest.mark.unit
    def test_embedding_dimension_matches_parameter(self):
        from app.services.vector_store import build_schema

        schema = build_schema(embedding_dim=384)
        emb_field = next(f for f in schema.fields if f.name == "embedding")

        assert emb_field.dtype == DataType.FLOAT_VECTOR
        assert emb_field.params.get("dim") == 384

    @pytest.mark.unit
    def test_chunk_index_is_int32(self):
        from app.services.vector_store import build_schema

        schema = build_schema(embedding_dim=768)
        chunk_field = next(f for f in schema.fields if f.name == "chunk_index")

        assert chunk_field.dtype == DataType.INT32

    @pytest.mark.unit
    def test_text_max_length(self):
        from app.services.vector_store import build_schema

        schema = build_schema(embedding_dim=768)
        text_field = next(f for f in schema.fields if f.name == "text")

        assert text_field.params.get("max_length") == 4096


class TestVectorStoreService:

    @pytest.fixture
    def mock_deps(self):
        with patch("app.services.vector_store.connections") as mock_conn, \
             patch("app.services.vector_store.utility") as mock_util, \
             patch("app.services.vector_store.Collection") as mock_coll_cls, \
             patch("app.services.vector_store.OllamaEmbeddings") as mock_emb:

            mock_embeddings = MagicMock()
            mock_emb.return_value = mock_embeddings

            mock_collection = MagicMock()
            mock_coll_cls.return_value = mock_collection

            yield {
                "connections": mock_conn,
                "utility": mock_util,
                "Collection": mock_coll_cls,
                "collection": mock_collection,
                "embeddings": mock_embeddings,
            }

    @pytest.fixture
    def vector_store(self, mock_deps):
        from app.services.vector_store import VectorStoreService
        svc = VectorStoreService()
        return svc

    @pytest.mark.unit
    def test_connect_existing_collection(self, vector_store, mock_deps):
        mock_deps["utility"].has_collection.return_value = True

        vector_store.connect()

        mock_deps["connections"].connect.assert_called_once()
        mock_deps["Collection"].assert_called_once()
        mock_deps["collection"].load.assert_called_once()

    @pytest.mark.unit
    def test_connect_creates_new_collection(self, vector_store, mock_deps):
        mock_deps["utility"].has_collection.return_value = False

        vector_store.connect()

        mock_deps["connections"].connect.assert_called_once()
        mock_deps["collection"].create_index.assert_called_once()
        mock_deps["collection"].load.assert_called_once()

    @pytest.mark.unit
    def test_embed_texts(self, vector_store, mock_deps):
        mock_deps["embeddings"].embed_documents.return_value = [[0.1, 0.2], [0.3, 0.4]]

        result = vector_store.embed_texts(["hello", "world"])

        assert result == [[0.1, 0.2], [0.3, 0.4]]
        mock_deps["embeddings"].embed_documents.assert_called_once_with(["hello", "world"])

    @pytest.mark.unit
    def test_embed_query(self, vector_store, mock_deps):
        mock_deps["embeddings"].embed_query.return_value = [0.1, 0.2]

        result = vector_store.embed_query("test query")

        assert result == [0.1, 0.2]

    @pytest.mark.unit
    def test_insert_chunks_empty_returns_empty(self, vector_store):
        result = vector_store.insert_chunks([])
        assert result == []

    @pytest.mark.unit
    def test_insert_chunks(self, vector_store, mock_deps):
        vector_store.collection = mock_deps["collection"]
        mock_deps["embeddings"].embed_documents.return_value = [[0.1] * 768]

        chunks = [{
            "document_id": "doc-1",
            "source_id": "src-1",
            "user_id": "user-1",
            "text": "Test chunk",
            "title": "Test",
            "url": "https://example.com",
            "chunk_index": 0,
        }]

        result = vector_store.insert_chunks(chunks)

        assert len(result) == 1
        mock_deps["collection"].insert.assert_called_once()
        mock_deps["collection"].flush.assert_called_once()

    @pytest.mark.unit
    def test_insert_chunks_sends_list_of_lists(self, vector_store, mock_deps):
        """Regression: pymilvus 2.6 expects list-of-lists, not dict-of-lists."""
        vector_store.collection = mock_deps["collection"]
        mock_deps["embeddings"].embed_documents.return_value = [[0.1] * 768, [0.2] * 768]

        chunks = [
            {
                "document_id": "doc-1", "source_id": "src-1", "user_id": "user-1",
                "text": "First chunk", "title": "T", "url": "https://example.com", "chunk_index": 0,
            },
            {
                "document_id": "doc-1", "source_id": "src-1", "user_id": "user-1",
                "text": "Second chunk", "title": "T", "url": "https://example.com", "chunk_index": 1,
            },
        ]

        vector_store.insert_chunks(chunks)

        data = mock_deps["collection"].insert.call_args[0][0]
        assert isinstance(data, list), "insert() must receive a list, not a dict"
        assert all(isinstance(col, list) for col in data), "each element must be a list (column)"
        assert len(data) == 9  # 9 fields: id, document_id, source_id, user_id, text, title, url, chunk_index, embedding
        assert data[1] == ["doc-1", "doc-1"]  # document_id column
        assert data[4] == ["First chunk", "Second chunk"]  # text column
        assert data[7] == [0, 1]  # chunk_index column

    @pytest.mark.unit
    def test_delete_by_document(self, vector_store, mock_deps):
        vector_store.collection = mock_deps["collection"]

        vector_store.delete_by_document("doc-1")

        mock_deps["collection"].delete.assert_called_once_with(
            expr='document_id == "doc-1"'
        )

    @pytest.mark.unit
    def test_delete_by_source(self, vector_store, mock_deps):
        vector_store.collection = mock_deps["collection"]

        vector_store.delete_by_source("src-1")

        mock_deps["collection"].delete.assert_called_once_with(
            expr='source_id == "src-1"'
        )

    @pytest.mark.unit
    def test_search(self, vector_store, mock_deps):
        vector_store.collection = mock_deps["collection"]
        mock_deps["embeddings"].embed_query.return_value = [0.1] * 768

        mock_hit = MagicMock()
        mock_hit.id = "chunk-1"
        mock_hit.score = 0.95
        mock_hit.entity.get = lambda k: {
            "document_id": "doc-1",
            "source_id": "src-1",
            "text": "Some text",
            "title": "Title",
            "url": "https://example.com",
            "chunk_index": 0,
        }.get(k)

        mock_deps["collection"].search.return_value = [[mock_hit]]

        results = vector_store.search("test query", user_id="user-1", top_k=5)

        assert len(results) == 1
        assert results[0]["chunk_id"] == "chunk-1"
        assert results[0]["score"] == 0.95
        assert results[0]["text"] == "Some text"

    @pytest.mark.unit
    def test_search_with_source_filter(self, vector_store, mock_deps):
        vector_store.collection = mock_deps["collection"]
        mock_deps["embeddings"].embed_query.return_value = [0.1] * 768
        mock_deps["collection"].search.return_value = [[]]

        vector_store.search("query", user_id="user-1", source_ids=["src-1", "src-2"])

        call_kwargs = mock_deps["collection"].search.call_args
        expr = call_kwargs[1]["expr"]
        assert 'user_id == "user-1"' in expr
        assert "source_id in" in expr
        assert '"src-1"' in expr
        assert '"src-2"' in expr
