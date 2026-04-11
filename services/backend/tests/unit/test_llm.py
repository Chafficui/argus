import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def llm_service():
    with patch("app.services.llm.ChatOllama") as mock_ollama:
        mock_llm = MagicMock()
        mock_ollama.return_value = mock_llm

        from app.services.llm import LLMService
        svc = LLMService()

    return svc


class TestLLMService:

    @pytest.mark.unit
    def test_answer_with_context_calls_llm(self, llm_service):
        llm_service.llm.invoke.return_value = MagicMock(content="The answer is 42.")

        chunks = [
            {"text": "Some context", "title": "Doc", "url": "https://example.com", "score": 0.9},
        ]

        result = llm_service.answer_with_context("What is the answer?", chunks)

        assert result == "The answer is 42."
        llm_service.llm.invoke.assert_called_once()

    @pytest.mark.unit
    def test_answer_with_empty_context_returns_fallback(self, llm_service):
        result = llm_service.answer_with_context("What is X?", [])

        assert "couldn't find" in result.lower()
        llm_service.llm.invoke.assert_not_called()

    @pytest.mark.unit
    def test_answer_includes_context_in_prompt(self, llm_service):
        llm_service.llm.invoke.return_value = MagicMock(content="Answer.")

        chunks = [
            {"text": "EU AI Act text", "title": "AI Act", "url": "https://eu.example.com", "score": 0.9},
            {"text": "Second chunk", "title": "More Info", "url": "", "score": 0.8},
        ]

        llm_service.answer_with_context("Tell me about AI Act", chunks)

        call_args = llm_service.llm.invoke.call_args[0][0]
        # Messages should be [SystemMessage, HumanMessage]
        human_msg = call_args[1].content
        assert "EU AI Act text" in human_msg
        assert "Second chunk" in human_msg
        assert "Tell me about AI Act" in human_msg

    @pytest.mark.unit
    def test_answer_uses_custom_system_prompt(self, llm_service):
        llm_service.llm.invoke.return_value = MagicMock(content="Brief.")

        chunks = [{"text": "ctx", "title": "T", "url": "", "score": 0.9}]

        llm_service.answer_with_context("Q?", chunks, system_prompt="Be brief.")

        call_args = llm_service.llm.invoke.call_args[0][0]
        system_msg = call_args[0].content
        assert system_msg == "Be brief."

    @pytest.mark.unit
    def test_answer_uses_default_system_prompt(self, llm_service):
        llm_service.llm.invoke.return_value = MagicMock(content="Answer.")

        chunks = [{"text": "ctx", "title": "T", "url": "", "score": 0.9}]

        llm_service.answer_with_context("Q?", chunks)

        call_args = llm_service.llm.invoke.call_args[0][0]
        system_msg = call_args[0].content
        assert "Argus" in system_msg
        assert "context" in system_msg.lower()
