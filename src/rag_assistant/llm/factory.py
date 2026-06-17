"""Construct the configured :class:`~rag_assistant.llm.base.LLMClient` implementation."""

from __future__ import annotations

from rag_assistant.config import GEMINI_MODEL, LLM_PROVIDER, OPENAI_MODEL
from rag_assistant.llm.base import LLMClient
from rag_assistant.llm.echo import EchoLLM
from rag_assistant.llm.gemini_client import GeminiLLM
from rag_assistant.llm.openai_client import OpenAILLM


def build_llm_client() -> LLMClient:
    """Return the LLM implementation selected by ``LLM_PROVIDER`` in ``config.py``."""
    if LLM_PROVIDER == "echo":
        return EchoLLM()
    if LLM_PROVIDER == "gemini":
        return GeminiLLM(model_name=GEMINI_MODEL)
    if LLM_PROVIDER == "openai":
        return OpenAILLM(model_name=OPENAI_MODEL)
    raise ValueError(
        f"Unknown LLM_PROVIDER={LLM_PROVIDER!r}. "
        "Edit ``LLM_PROVIDER`` in ``src/rag_assistant/config.py`` to ``gemini``, ``openai``, or ``echo``."
    )


def get_api_key() -> str | None:
    """Return the API key for the active remote provider, or ``None`` if missing / not applicable."""
    from rag_assistant.config import get_gemini_api_key, get_openai_api_key

    if LLM_PROVIDER == "gemini":
        return get_gemini_api_key()
    if LLM_PROVIDER == "openai":
        return get_openai_api_key()
    return None


def remote_llm_api_key_required() -> bool:
    """Whether the current provider needs a key in ``.env`` / environment."""
    return LLM_PROVIDER in ("gemini", "openai")
