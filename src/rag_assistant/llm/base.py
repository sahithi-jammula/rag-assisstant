"""Abstract base for text-generation backends (swappable LLM layer)."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Minimal contract: turn a full RAG prompt into assistant text."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Short id for logging and UI (e.g. ``gemini``, ``echo``)."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return model text for the given prompt (already includes CONTEXT + QUESTION)."""
