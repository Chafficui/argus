# =============================================================================
# app/services/llm.py
# =============================================================================
# Thin wrapper around Ollama's ChatOllama for RAG responses.
#
# Keeps LangChain imports out of the route handlers and centralizes
# the system prompt and context formatting logic.
# =============================================================================

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
import structlog
from app.core.config import get_settings

log = structlog.get_logger()

DEFAULT_SYSTEM_PROMPT = """You are Argus, an AI research assistant. Answer the user's question \
based ONLY on the provided context. Follow these rules strictly:

1. Only use information from the context below. Do not use prior knowledge.
2. If the context does not contain enough information to answer, say so clearly.
3. Cite your sources by referencing the title and URL when available.
4. Be concise and factual. Prefer bullet points for multi-part answers.
5. If multiple sources agree, synthesize them. If they conflict, note the disagreement."""


class LLMService:
    """Wraps ChatOllama for generating RAG responses."""

    def __init__(self):
        settings = get_settings()
        self.llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0.1,  # Low temperature for factual answers
        )

    def answer_with_context(
        self,
        question: str,
        context_chunks: list[dict],
        system_prompt: str | None = None,
    ) -> str:
        """
        Build a prompt from context chunks + question, call Ollama, return the answer.

        Each chunk dict should have: text, title, url, score
        """
        if not context_chunks:
            return "I couldn't find any relevant information in your sources to answer this question."

        # Build context block with source attribution
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            title = chunk.get("title", "Untitled")
            url = chunk.get("url", "")
            text = chunk.get("text", "")
            source_label = f"[Source {i}: {title}]({url})" if url else f"[Source {i}: {title}]"
            context_parts.append(f"{source_label}\n{text}")

        context_block = "\n\n---\n\n".join(context_parts)

        prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=f"Context:\n\n{context_block}\n\nQuestion: {question}"),
        ]

        log.info(
            "Calling LLM",
            model=self.llm.model,
            context_chunks=len(context_chunks),
            question_preview=question[:80],
        )

        response = self.llm.invoke(messages)
        return response.content


# Singleton
llm_service = LLMService()
