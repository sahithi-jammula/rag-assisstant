"""HyDE: hypothetical document embedding for dense retrieval (BM25 stays on raw question)."""

from __future__ import annotations

import logging

import numpy as np

from rag_assistant.embeddings.service import Embedder
from rag_assistant.llm.base import LLMClient

logger = logging.getLogger(__name__)


def _hypothetical_passage(llm: LLMClient, question: str, max_chars: int) -> str:
    prompt = (
        "You are drafting a short hypothetical passage that could appear in a deep learning "
        "textbook (Dive into Deep Learning style). It should directly help answer the user's "
        "question with definitions, intuition, or steps — not meta commentary.\n"
        "Output plain prose only (no bullet list unless essential). "
        f"Hard limit: at most {max_chars} characters.\n\n"
        f"Question:\n{question.strip()}\n"
    )
    text = llm.generate(prompt).strip()
    if len(text) > max_chars:
        text = text[:max_chars]
    return text


def merge_query_and_hyde_vectors(
    question_vec: np.ndarray,
    hyde_vec: np.ndarray | None,
) -> np.ndarray:
    """Average L2-normalized dense query with HyDE vector, then L2-normalize (same space as FAISS IP)."""
    q = np.asarray(question_vec, dtype=np.float32).reshape(-1)
    if hyde_vec is None:
        return q
    h = np.asarray(hyde_vec, dtype=np.float32).reshape(-1)
    if h.shape != q.shape:
        logger.warning("HyDE vector shape mismatch; using question vector only")
        return q
    merged = q + h
    n = float(np.linalg.norm(merged))
    if n < 1e-12:
        return q
    return (merged / n).astype(np.float32)


def maybe_hyde_dense_vector(
    question: str,
    question_vec: np.ndarray,
    embedder: Embedder,
    llm: LLMClient,
) -> np.ndarray:
    """
    Merge HyDE hypothetical-document embedding with the question vector for dense retrieval.

    BM25 in ``retrieve_for_query`` continues to use the raw ``question`` string.
    """
    from rag_assistant import config as _cfg

    try:
        hypo = _hypothetical_passage(llm, question, _cfg.HYDE_MAX_CHARS)
    except Exception as exc:  # noqa: BLE001 — HyDE is best-effort
        logger.warning("HyDE LLM call failed; dense retrieval uses question only: %s", exc)
        return np.asarray(question_vec, dtype=np.float32).reshape(-1)

    if not hypo.strip():
        return np.asarray(question_vec, dtype=np.float32).reshape(-1)

    hv = embedder.encode([hypo])[0]
    return merge_query_and_hyde_vectors(question_vec, hv)
