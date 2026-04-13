import pytest
from unittest.mock import MagicMock


MOCK_SEARCH_RESULTS = [
    {
        "chunk_id": "chunk-1",
        "document_id": "doc-1",
        "source_id": "source-1",
        "text": "The EU AI Act requires conformity assessments for high-risk AI systems.",
        "title": "EU AI Act Summary",
        "url": "https://example.com/eu-ai-act",
        "chunk_index": 0,
        "score": 0.92,
    },
    {
        "chunk_id": "chunk-2",
        "document_id": "doc-2",
        "source_id": "source-1",
        "text": "Foundation models face transparency obligations under the Act.",
        "title": "Foundation Model Rules",
        "url": "https://example.com/foundation-models",
        "chunk_index": 1,
        "score": 0.78,
    },
]

LOW_SCORE_RESULT = {
    "chunk_id": "chunk-3",
    "document_id": "doc-3",
    "source_id": "source-1",
    "text": "Unrelated content about cooking recipes.",
    "title": "Recipes",
    "url": "https://example.com/recipes",
    "chunk_index": 0,
    "score": 0.25,
}


@pytest.fixture
def mock_vector_search(mocker):
    """Mock the vector_store.search used by the search route."""
    mock = MagicMock()
    mock.search.return_value = MOCK_SEARCH_RESULTS.copy()
    mocker.patch("app.api.routes.search.vector_store", mock)
    return mock


@pytest.fixture
def mock_llm(mocker):
    """Mock the llm_service used by the ask route."""
    mock = MagicMock()
    mock.answer_with_context.return_value = (
        "The EU AI Act requires conformity assessments for high-risk AI systems "
        "and imposes transparency obligations on foundation models."
    )
    mocker.patch("app.api.routes.search.llm_service", mock)
    return mock


class TestSearchEndpoint:

    @pytest.mark.unit
    async def test_search_returns_results(self, client, mock_vector_search):
        response = await client.post("/api/search/", json={
            "query": "EU AI Act requirements",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "EU AI Act requirements"
        assert data["total"] == 2
        assert len(data["results"]) == 2
        assert data["results"][0]["score"] == 0.92
        assert "conformity assessments" in data["results"][0]["text"]

    @pytest.mark.unit
    async def test_search_filters_low_score_results(self, client, mock_vector_search):
        mock_vector_search.search.return_value = MOCK_SEARCH_RESULTS + [LOW_SCORE_RESULT]

        response = await client.post("/api/search/", json={
            "query": "AI regulation",
            "min_score": 0.5,
        })

        assert response.status_code == 200
        data = response.json()
        # Low-score result (0.25) should be filtered out
        assert data["total"] == 2
        scores = [r["score"] for r in data["results"]]
        assert all(s >= 0.5 for s in scores)

    @pytest.mark.unit
    async def test_search_empty_query_returns_422(self, client, mock_vector_search):
        response = await client.post("/api/search/", json={
            "query": "",
        })

        assert response.status_code == 422

    @pytest.mark.unit
    async def test_search_passes_source_ids_filter(self, client, mock_vector_search):
        await client.post("/api/search/", json={
            "query": "test query",
            "source_ids": ["src-1", "src-2"],
        })

        call_kwargs = mock_vector_search.search.call_args[1]
        assert call_kwargs["source_ids"] == ["src-1", "src-2"]

    @pytest.mark.unit
    async def test_search_respects_top_k(self, client, mock_vector_search):
        await client.post("/api/search/", json={
            "query": "test query",
            "top_k": 10,
        })

        call_kwargs = mock_vector_search.search.call_args[1]
        assert call_kwargs["top_k"] == 10

    @pytest.mark.unit
    async def test_search_no_results(self, client, mock_vector_search):
        mock_vector_search.search.return_value = []

        response = await client.post("/api/search/", json={
            "query": "something obscure",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["results"] == []


class TestAskEndpoint:

    @pytest.mark.unit
    async def test_ask_returns_answer_and_sources(
        self, client, mock_vector_search, mock_llm
    ):
        response = await client.post("/api/search/ask", json={
            "query": "What does the EU AI Act require?",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "What does the EU AI Act require?"
        assert "conformity assessments" in data["answer"]
        assert len(data["sources"]) == 2

        mock_llm.answer_with_context.assert_called_once()

    @pytest.mark.unit
    async def test_ask_with_no_results_returns_graceful_message(
        self, client, mock_vector_search, mock_llm
    ):
        mock_vector_search.search.return_value = []
        mock_llm.answer_with_context.return_value = (
            "I couldn't find any relevant information in your sources to answer this question."
        )

        response = await client.post("/api/search/ask", json={
            "query": "What is quantum gravity?",
        })

        assert response.status_code == 200
        data = response.json()
        assert "couldn't find" in data["answer"]
        assert data["sources"] == []

    @pytest.mark.unit
    async def test_ask_passes_system_prompt(
        self, client, mock_vector_search, mock_llm
    ):
        await client.post("/api/search/ask", json={
            "query": "Summarize the AI Act",
            "system_prompt": "Be very brief.",
        })

        call_kwargs = mock_llm.answer_with_context.call_args[1]
        assert call_kwargs["system_prompt"] == "Be very brief."

    @pytest.mark.unit
    async def test_ask_filters_low_score_before_llm(
        self, client, mock_vector_search, mock_llm
    ):
        mock_vector_search.search.return_value = MOCK_SEARCH_RESULTS + [LOW_SCORE_RESULT]

        await client.post("/api/search/ask", json={
            "query": "AI regulation",
            "min_score": 0.5,
        })

        # LLM should only receive 2 chunks (low-score filtered out)
        call_kwargs = mock_llm.answer_with_context.call_args[1]
        assert len(call_kwargs["context_chunks"]) == 2
