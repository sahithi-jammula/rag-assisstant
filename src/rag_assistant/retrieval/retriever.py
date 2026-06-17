"""Embed the question and return ranked chunks from the FAISS store."""

from __future__ import annotations

import numpy as np

from rag_assistant.embeddings.service import Embedder
from rag_assistant.vectorstore.faiss_store import FaissVectorStore


class Retriever:
    def __init__(self, store: FaissVectorStore, embedder: Embedder) -> None:
        self.store = store
        self.embedder = embedder

    def retrieve(self, question: str, top_k: int, query_vector: np.ndarray | None = None) -> list[dict]:
        if query_vector is None:
            qvec = self.embedder.encode([question.strip()])[0]
        else:
            qvec = query_vector
        return self.store.search(qvec, top_k)
