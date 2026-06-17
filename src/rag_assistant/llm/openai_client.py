"""OpenAI Chat Completions implementation of :class:`~rag_assistant.llm.base.LLMClient`."""

from __future__ import annotations

import logging

from rag_assistant.config import get_openai_api_key
from rag_assistant.llm.base import LLMClient

logger = logging.getLogger(__name__)


class OpenAILLM(LLMClient):
    """Thin wrapper around the OpenAI Python SDK (chat completions)."""

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    @property
    def provider_id(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, prompt: str) -> str:
        from openai import OpenAI

        key = get_openai_api_key()
        if not key:
            raise ValueError(
                "Missing OpenAI API key. Set OPENAI_API_KEY in a root `.env` file "
                "(or your process environment)."
            )
        client = OpenAI(api_key=key)
        try:
            response = client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
        except Exception as exc:  # noqa: BLE001 — map OpenAI SDK errors to a clear message
            exc_name = type(exc).__name__
            if "RateLimit" in exc_name:
                logger.warning("OpenAI rate limit: %s", exc)
                return (
                    "**OpenAI rate limit.** Wait briefly and retry, or check your plan and "
                    f"[usage limits](https://platform.openai.com/docs/guides/rate-limits).\n\n_{exc}_"
                )
            raise ValueError(
                f"OpenAI API error for model {self._model_name!r}: {exc}. "
                "Confirm the model id in ``src/rag_assistant/config.py`` (``OPENAI_MODEL``) — "
                "see docs/openai-llm.md and https://platform.openai.com/docs/models"
            ) from exc

        choice = response.choices[0].message
        text = (choice.content or "").strip()
        return text or "(empty response)"
