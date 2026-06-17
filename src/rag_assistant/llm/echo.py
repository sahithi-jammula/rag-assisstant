"""Local stub LLM for testing the RAG path without calling a remote API."""

from __future__ import annotations

from rag_assistant.llm.base import LLMClient


class EchoLLM(LLMClient):
    """Returns a fixed message; useful for verifying retrieval and prompts."""

    @property
    def provider_id(self) -> str:
        return "echo"

    def generate(self, prompt: str) -> str:
        n = len(prompt)
        return (
            "**Echo mode** — no remote LLM was called. "
            "Set ``LLM_PROVIDER = \"gemini\"`` or ``\"openai\"`` in ``src/rag_assistant/config.py`` "
            "and add ``GEMINI_API_KEY`` or ``OPENAI_API_KEY`` to ``.env`` for real answers.\n\n"
            f"The assembled RAG prompt is **{n}** characters (inspect **Retrieved chunks** for context)."
        )
