"""FAISS inner-product index with JSON metadata persisted alongside."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from rag_assistant.config import (
    FAISS_INDEX_FILENAME,
    INDEX_INFO_FILENAME,
    METADATA_FILENAME,
)

logger = logging.getLogger(__name__)


def _atomic_replace(tmp: Path, final: Path) -> None:
    tmp.replace(final)


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _atomic_replace(tmp, path)


@dataclass
class FaissVectorStore:
    """Row i in FAISS matches self.chunks[i]."""

    index: faiss.Index
    chunks: list[dict[str, Any]]

    @classmethod
    def build(cls, vectors: np.ndarray, chunks: list[dict[str, Any]]) -> "FaissVectorStore":
        if vectors.ndim != 2:
            raise ValueError("vectors must be 2D")
        if vectors.shape[0] != len(chunks):
            raise ValueError("vectors and chunks length mismatch")
        dim = vectors.shape[1]
        idx = faiss.IndexFlatIP(dim)
        mat = np.ascontiguousarray(vectors, dtype="float32")
        faiss.normalize_L2(mat)
        idx.add(mat)
        return cls(index=idx, chunks=chunks)

    def search(self, query_vector: np.ndarray, k: int) -> list[dict[str, Any]]:
        ntotal = int(self.index.ntotal)
        if ntotal == 0:
            return []
        k = max(1, min(int(k), ntotal))
        q = np.ascontiguousarray(query_vector.reshape(1, -1), dtype="float32")
        faiss.normalize_L2(q)
        scores, indices = self.index.search(q, k)
        hits: list[dict[str, Any]] = []
        for score, idx in zip(scores[0].tolist(), indices[0].tolist()):
            if idx < 0 or idx >= len(self.chunks):
                continue
            meta = self.chunks[idx]
            hits.append(
                {
                    "text": meta["text"],
                    "source": meta["source"],
                    "chunk_index": meta["chunk_index"],
                    "row_id": int(idx),
                    "score": float(score),
                    **({"metadata": meta["metadata"]} if meta.get("metadata") else {}),
                }
            )
        return hits

    def save(self, index_dir: Path, index_info: dict[str, Any]) -> None:
        index_dir.mkdir(parents=True, exist_ok=True)
        idx_path = index_dir / FAISS_INDEX_FILENAME
        meta_path = index_dir / METADATA_FILENAME
        info_path = index_dir / INDEX_INFO_FILENAME

        tmp_index = Path(str(idx_path) + ".tmp")
        faiss.write_index(self.index, str(tmp_index))
        _atomic_replace(tmp_index, idx_path)

        _write_json_atomic(meta_path, {"chunks": self.chunks})
        _write_json_atomic(info_path, index_info)
        logger.info("Saved FAISS index to %s", index_dir)

    @classmethod
    def load(cls, index_dir: Path) -> "FaissVectorStore":
        idx_path = index_dir / FAISS_INDEX_FILENAME
        meta_path = index_dir / METADATA_FILENAME
        if not idx_path.is_file() or not meta_path.is_file():
            raise FileNotFoundError("Missing index or metadata file in %s" % index_dir)
        index = faiss.read_index(str(idx_path))
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        chunks = meta["chunks"]
        return cls(index=index, chunks=chunks)


def load_index_info(index_dir: Path) -> dict[str, Any] | None:
    path = index_dir / INDEX_INFO_FILENAME
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def clear_index_dir(index_dir: Path) -> None:
    """Remove known artifacts; ignores missing files."""
    for name in (FAISS_INDEX_FILENAME, METADATA_FILENAME, INDEX_INFO_FILENAME):
        p = index_dir / name
        if p.is_file():
            try:
                p.unlink()
            except OSError as exc:
                logger.warning("Could not delete %s: %s", p, exc)
    for pat in ("*.tmp",):
        for p in index_dir.glob(pat):
            try:
                p.unlink()
            except OSError:
                pass
