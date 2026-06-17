"""Chunk-level metadata (e.g. D2L chapter folder) and optional chapter filters."""

from __future__ import annotations

from rag_assistant.vectorstore.faiss_store import FaissVectorStore


def infer_chunk_metadata(source: str) -> dict[str, str]:
    """
    Derive lightweight metadata from ``source`` path (forward slashes normalized).

    D2L English clone paths typically contain ``.../chapter_introduction/...``.
    """
    norm = source.replace("\\", "/")
    for part in norm.split("/"):
        if part.startswith("chapter_"):
            return {"chapter": part}
    return {}


def row_matches_chapter_filters(
    store: FaissVectorStore,
    row_id: int,
    chapter_filters: list[str] | None,
) -> bool:
    """
    If ``chapter_filters`` is empty/None, all rows match.

    Otherwise a row matches if **any** filter token matches: exact ``metadata.chapter``,
    or the token appears as a path segment in ``source``.
    """
    if not chapter_filters:
        return True
    if row_id < 0 or row_id >= len(store.chunks):
        return False
    meta = store.chunks[row_id]
    md = meta.get("metadata") or {}
    chapter = str(md.get("chapter", ""))
    src = str(meta.get("source", "")).replace("\\", "/")
    for raw in chapter_filters:
        tok = raw.strip()
        if not tok:
            continue
        if chapter == tok:
            return True
        seg = f"/{tok}/"
        if seg in src or src.endswith(f"/{tok}") or src.startswith(f"{tok}/"):
            return True
    return False
