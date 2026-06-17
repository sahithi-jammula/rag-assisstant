"""Sentence-transformers embedding wrapper."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class Embedder:
    """Lazy-loads the model to keep import-time light for tools that only read docs."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model: SentenceTransformer | None = None

    def load(self) -> None:
        if self._model is not None:
            return
        from rag_assistant.embeddings.ssl_utils import configure_tls_for_hf_downloads

        configure_tls_for_hf_downloads()
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", self.model_name)
        self._model = SentenceTransformer(self.model_name)

    @property
    def model(self) -> "SentenceTransformer":
        if self._model is None:
            raise RuntimeError("Call embedder.load() before encoding.")
        return self._model

    @property
    def dimension(self) -> int:
        return int(self.model.get_sentence_embedding_dimension())

    def encode(self, texts: list[str]) -> np.ndarray:
        self.load()
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 32,
        )
        return vectors.astype("float32", copy=False)
