"""Semantic cache: JSON file and/or Redis backends; reuse answers for similar questions."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import numpy as np

from rag_assistant.config import PROMPT_TEMPLATE_VERSION, retrieval_profile_fingerprint

logger = logging.getLogger(__name__)


def normalize_cache_question(text: str) -> str:
    """Stable string for L1 exact-match (strip, case-fold, collapse whitespace)."""
    return " ".join(text.strip().casefold().split())


def compute_index_fingerprint(index_dir: Path) -> str:
    """
    Short fingerprint of the built index so cache entries invalidate after rebuild
    or when embedding/chunk settings in index_info change.
    """
    from rag_assistant.vectorstore.faiss_store import load_index_info

    info = load_index_info(index_dir)
    if not info:
        return "no_index_info"
    parts = (
        str(info.get("built_at", "")),
        str(info.get("num_chunks", "")),
        str(info.get("embedding_model", "")),
        str(info.get("chunk_size", "")),
        str(info.get("chunk_overlap", "")),
        PROMPT_TEMPLATE_VERSION,
        retrieval_profile_fingerprint(),
    )
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:20]


@dataclass
class CacheEntry:
    question: str
    embedding: list[float]
    answer: str
    hits: list[dict[str, Any]]
    prompt: str
    index_fingerprint: str
    llm_provider: str
    model_label: str
    prompt_template_version: str
    created_at: str


@runtime_checkable
class SemanticCacheBackend(Protocol):
    """Lookup/store contract shared by JSON, Redis, and no-op caches."""

    enabled: bool

    def lookup(
        self,
        query_vector: np.ndarray,
        *,
        index_fingerprint: str,
        llm_provider: str,
        model_label: str,
    ) -> CacheEntry | None: ...

    def lookup_exact(
        self,
        question: str,
        *,
        index_fingerprint: str,
        llm_provider: str,
        model_label: str,
    ) -> CacheEntry | None: ...

    def store(
        self,
        *,
        question: str,
        query_vector: np.ndarray,
        answer: str,
        hits: list[dict[str, Any]],
        prompt: str,
        index_fingerprint: str,
        llm_provider: str,
        model_label: str,
    ) -> None: ...


class NoOpSemanticCache:
    """Disabled cache: always miss, never store."""

    enabled = False

    def lookup(
        self,
        query_vector: np.ndarray,
        *,
        index_fingerprint: str,
        llm_provider: str,
        model_label: str,
    ) -> CacheEntry | None:
        del query_vector, index_fingerprint, llm_provider, model_label
        return None

    def lookup_exact(
        self,
        question: str,
        *,
        index_fingerprint: str,
        llm_provider: str,
        model_label: str,
    ) -> CacheEntry | None:
        del question, index_fingerprint, llm_provider, model_label
        return None

    def store(
        self,
        *,
        question: str,
        query_vector: np.ndarray,
        answer: str,
        hits: list[dict[str, Any]],
        prompt: str,
        index_fingerprint: str,
        llm_provider: str,
        model_label: str,
    ) -> None:
        del (
            question,
            query_vector,
            answer,
            hits,
            prompt,
            index_fingerprint,
            llm_provider,
            model_label,
        )


class JsonSemanticCache:
    """
    In-memory list backed by JSON. Similarity = dot product of L2-normalized
    query vectors (same convention as chunk embeddings).
    """

    def __init__(
        self,
        path: Path,
        *,
        max_entries: int,
        similarity_threshold: float,
        enabled: bool,
    ) -> None:
        self.path = path
        self.max_entries = max(1, int(max_entries))
        self.similarity_threshold = float(similarity_threshold)
        self.enabled = enabled
        self._entries: list[CacheEntry] = []
        if self.enabled:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            items = raw.get("entries", [])
            self._entries = [CacheEntry(**e) for e in items]
        except (json.JSONDecodeError, OSError, TypeError, KeyError) as exc:
            logger.warning("Could not load semantic cache %s: %s", self.path, exc)
            self._entries = []

    def lookup_exact(
        self,
        question: str,
        *,
        index_fingerprint: str,
        llm_provider: str,
        model_label: str,
    ) -> CacheEntry | None:
        if not self.enabled or not self._entries:
            return None
        key = normalize_cache_question(question)
        if not key:
            return None
        for entry in reversed(self._entries):
            if entry.index_fingerprint != index_fingerprint:
                continue
            if entry.llm_provider != llm_provider or entry.model_label != model_label:
                continue
            if entry.prompt_template_version != PROMPT_TEMPLATE_VERSION:
                continue
            if normalize_cache_question(entry.question) == key:
                logger.info("Semantic cache hit (JSON, L1 exact)")
                return entry
        return None

    def _save(self) -> None:
        if not self.enabled:
            return
        payload = {"entries": [asdict(e) for e in self._entries]}
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def lookup(
        self,
        query_vector: np.ndarray,
        *,
        index_fingerprint: str,
        llm_provider: str,
        model_label: str,
    ) -> CacheEntry | None:
        if not self.enabled or not self._entries:
            return None
        q = np.asarray(query_vector, dtype=np.float32).reshape(-1)
        qn = float(np.linalg.norm(q))
        if qn < 1e-12:
            return None
        q = q / qn
        for entry in reversed(self._entries):
            if entry.index_fingerprint != index_fingerprint:
                continue
            if entry.llm_provider != llm_provider or entry.model_label != model_label:
                continue
            if entry.prompt_template_version != PROMPT_TEMPLATE_VERSION:
                continue
            v = np.asarray(entry.embedding, dtype=np.float32).reshape(-1)
            vn = float(np.linalg.norm(v))
            if vn < 1e-12:
                continue
            v = v / vn
            sim = float(np.dot(q, v))
            if sim >= self.similarity_threshold:
                logger.info("Semantic cache hit (JSON, L2 similarity %.4f)", sim)
                return entry
        return None

    def store(
        self,
        *,
        question: str,
        query_vector: np.ndarray,
        answer: str,
        hits: list[dict[str, Any]],
        prompt: str,
        index_fingerprint: str,
        llm_provider: str,
        model_label: str,
    ) -> None:
        if not self.enabled:
            return
        if answer.startswith("**Could not call LLM"):
            return
        emb = np.asarray(query_vector, dtype=np.float32).reshape(-1).tolist()
        entry = CacheEntry(
            question=question.strip(),
            embedding=emb,
            answer=answer,
            hits=hits,
            prompt=prompt,
            index_fingerprint=index_fingerprint,
            llm_provider=llm_provider,
            model_label=model_label,
            prompt_template_version=PROMPT_TEMPLATE_VERSION,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._entries.append(entry)
        while len(self._entries) > self.max_entries:
            self._entries.pop(0)
        self._save()


# Backward-compatible name for the file-backed implementation
SemanticCache = JsonSemanticCache


def build_semantic_cache_from_config() -> SemanticCacheBackend:
    from rag_assistant.config import (
        REDIS_SEMANTIC_CACHE_KEY_PREFIX,
        REDIS_URL,
        SEMANTIC_CACHE_BACKEND,
        SEMANTIC_CACHE_MAX_ENTRIES,
        SEMANTIC_CACHE_PATH,
        SEMANTIC_CACHE_SIMILARITY_THRESHOLD,
    )

    def _json_cache() -> JsonSemanticCache:
        return JsonSemanticCache(
            SEMANTIC_CACHE_PATH,
            max_entries=SEMANTIC_CACHE_MAX_ENTRIES,
            similarity_threshold=SEMANTIC_CACHE_SIMILARITY_THRESHOLD,
            enabled=True,
        )

    if SEMANTIC_CACHE_BACKEND == "redis":
        from rag_assistant.cache.redis_semantic_cache import RedisSemanticCache

        try:
            return RedisSemanticCache(
                url=REDIS_URL,
                key_prefix=REDIS_SEMANTIC_CACHE_KEY_PREFIX,
                max_entries=SEMANTIC_CACHE_MAX_ENTRIES,
                similarity_threshold=SEMANTIC_CACHE_SIMILARITY_THRESHOLD,
                enabled=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Redis semantic cache could not be initialized (%s); falling back to JSON file cache.",
                exc,
            )
            return _json_cache()

    return _json_cache()
