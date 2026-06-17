"""Reciprocal Rank Fusion (RRF) for combining ordered retrieval lists."""

from __future__ import annotations


def reciprocal_rank_fusion(rank_lists: list[list[int]], *, k: int = 60) -> dict[int, float]:
    """
    Each rank list is document ids from best to worst rank.
    Returns a fused score per id (higher is better).
    """
    scores: dict[int, float] = {}
    for ids in rank_lists:
        for rank, doc_id in enumerate(ids):
            if doc_id < 0:
                continue
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return scores
