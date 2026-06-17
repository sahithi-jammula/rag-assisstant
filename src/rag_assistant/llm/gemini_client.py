"""Google Gemini implementation of :class:`~rag_assistant.llm.base.LLMClient`."""

from __future__ import annotations

import logging

from rag_assistant.config import get_gemini_api_key
from rag_assistant.llm.base import LLMClient

logger = logging.getLogger(__name__)


class GeminiLLM(LLMClient):
    """Thin wrapper around ``google-generativeai``."""

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    @property
    def provider_id(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, prompt: str) -> str:
        from rag_assistant.config import GEMINI_TRANSPORT

        import google.generativeai as genai
        from google.api_core import exceptions as google_api_exceptions

        key = get_gemini_api_key()
        if not key:
            raise ValueError(
                "Missing API key. Set GEMINI_API_KEY or GOOGLE_API_KEY in a root `.env` file "
                "(or your process environment)."
            )
        genai.configure(api_key=key, transport=GEMINI_TRANSPORT)
        model = genai.GenerativeModel(self._model_name)
        try:
            response = model.generate_content(prompt)
        except google_api_exceptions.NotFound as exc:
            raise ValueError(
                f"Gemini model {self._model_name!r} is not available for generateContent with this API key "
                f"({exc}). Set ``GEMINI_MODEL`` in ``src/rag_assistant/config.py`` to a current id "
                "(for example gemini-2.5-flash) — see https://ai.google.dev/gemini-api/docs/models"
            ) from exc
        except (google_api_exceptions.TooManyRequests, google_api_exceptions.ResourceExhausted) as exc:
            logger.warning("Gemini quota / rate limit: %s", exc)
            return (
                "**Gemini rate limit or quota (429).** On the free tier, Google limits how many "
                "`generateContent` calls you can make per minute **per model** (your error mentioned "
                "about **5/min** for this model). Wait **30–60 seconds** and send again, avoid double-clicks, "
                "or check usage / billing in [Google AI Studio](https://aistudio.google.com/) and "
                "[rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).\n\n"
                f"_Technical detail: {exc}_"
            )
        try:
            text = response.text
        except Exception as exc:  # noqa: BLE001 — SDK raises for blocked / empty
            logger.exception("Gemini response handling failed: %s", exc)
            return "The model did not return usable text (blocked, empty, or error). Check logs and API quota."
        return text.strip() or "(empty response)"


def generate_answer(prompt: str, model_name: str) -> str:
    """Backward-compatible helper; prefer :class:`GeminiLLM` or :func:`build_llm_client`."""
    return GeminiLLM(model_name=model_name).generate(prompt)
