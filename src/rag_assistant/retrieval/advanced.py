"""Retrieval: dense candidate pool + BM25 + RRF + cross-encoder rerank (always on)."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi

from rag_assistant import config
from rag_assistant.embeddings.service import Embedder
from rag_assistant.retrieval.chunk_metadata import row_matches_chapter_filters
from rag_assistant.retrieval.fusion import reciprocal_rank_fusion
from rag_assistant.retrieval.tokenization import tokenize
from rag_assistant.vectorstore.faiss_store import FaissVectorStore

logger = logging.getLogger(__name__)

_bm25_cache: dict[tuple[int, int], BM25Okapi] = {}
_cross_encoder: Any = None
_cross_encoder_name: str | None = None


def _bm25_key(store: FaissVectorStore) -> tuple[int, int]:
    return (id(store), len(store.chunks))


def _get_bm25(store: FaissVectorStore) -> BM25Okapi:
    key = _bm25_key(store)
    if key not in _bm25_cache:
        corpus = [tokenize(str(c.get("text", ""))) for c in store.chunks]
        corpus = [t if t else ["_"] for t in corpus]
        logger.info("Building BM25 index over %s chunks", len(corpus))
        _bm25_cache[key] = BM25Okapi(corpus)
    return _bm25_cache[key]


def _get_cross_encoder(model_name: str) -> Any:
    global _cross_encoder, _cross_encoder_name
    if _cross_encoder is None or _cross_encoder_name != model_name:
        from sentence_transformers import CrossEncoder

        logger.info("Loading cross-encoder reranker: %s", model_name)
        _cross_encoder = CrossEncoder(model_name)
        _cross_encoder_name = model_name
    return _cross_encoder


def _hit_from_row(store: FaissVectorStore, row_id: int, score: float) -> dict[str, Any]:
    meta = store.chunks[row_id]
    out: dict[str, Any] = {
        "text": meta["text"],
        "source": meta["source"],
        "chunk_index": meta["chunk_index"],
        "row_id": int(row_id),
        "score": float(score),
    }
    md = meta.get("metadata")
    if md:
        out["metadata"] = md
    return out


def _search_dense_filtered(
    store: FaissVectorStore,
    query_vector: np.ndarray,
    want_k: int,
    chapters: list[str] | None,
) -> list[dict[str, Any]]:
    """FAISS search with optional chapter metadata filter; may widen K until enough hits."""
    ntotal = int(store.index.ntotal)
    if ntotal == 0:
        return []
    want_k = max(1, min(int(want_k), ntotal))
    if not chapters:
        return store.search(query_vector, want_k)
    k = min(ntotal, want_k)
    while True:
        hits = store.search(query_vector, k)
        filtered = [h for h in hits if row_matches_chapter_filters(store, int(h["row_id"]), chapters)]
        if len(filtered) >= want_k or k >= ntotal:
            return filtered[:want_k]
        k = min(ntotal, k * 2)


def retrieve_for_query(
    question: str,
    query_vector: np.ndarray,
    embedder: Embedder,
    store: FaissVectorStore,
    top_k: int | None = None,
    metadata_chapters: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Dense pool + BM25 + RRF + cross-encoder rerank. Same hit shape as ``FaissVectorStore.search``
    (includes ``row_id``).
    """
    del embedder
    tk = config.TOP_K if top_k is None else top_k
    chapters = metadata_chapters if metadata_chapters is not None else config.METADATA_FILTER_CHAPTERS
    ntotal = int(store.index.ntotal)
    if ntotal == 0:
        return []

    top_k_eff = max(1, min(tk, ntotal))
    cand = max(top_k_eff, min(config.RETRIEVAL_CANDIDATE_K, ntotal))

    dense_hits = _search_dense_filtered(store, query_vector, cand, chapters or None)
    dense_ids = [int(h["row_id"]) for h in dense_hits]

    bm25 = _get_bm25(store)
    q_tokens = tokenize(question.strip())
    if not q_tokens:
        q_tokens = ["_"]
    bm25_scores = bm25.get_scores(q_tokens)
    full_order = list(np.argsort(np.asarray(bm25_scores, dtype=np.float64))[::-1])
    if chapters:
        bm25_order = [int(i) for i in full_order if row_matches_chapter_filters(store, int(i), chapters)][
            :cand
        ]
    else:
        bm25_order = [int(i) for i in full_order[:cand]]

    fused = reciprocal_rank_fusion([dense_ids, bm25_order], k=config.RRF_K)
    ordered_unique = sorted(fused.keys(), key=lambda i: fused[i], reverse=True)
    pool_n = min(config.RERANK_POOL, len(ordered_unique))
    pool_ids = ordered_unique[:pool_n]

    if not pool_ids:
        return _search_dense_filtered(store, query_vector, top_k_eff, chapters or None)

    ce = _get_cross_encoder(config.RERANK_MODEL_NAME)
    texts = [store.chunks[i]["text"] for i in pool_ids]
    pairs = list(zip([question.strip()] * len(texts), texts))
    rs = ce.predict(pairs, show_progress_bar=False)
    order = sorted(range(len(pool_ids)), key=lambda j: float(rs[j]), reverse=True)
    best_js = order[:top_k_eff]
    return [_hit_from_row(store, pool_ids[j], float(rs[j])) for j in best_js]
