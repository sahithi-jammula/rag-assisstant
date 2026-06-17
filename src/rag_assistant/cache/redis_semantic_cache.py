"""Semantic cache backed by Redis (plain hashes + list; Redis Stack image in Docker is supported)."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np

from rag_assistant.cache.semantic_cache import CacheEntry, normalize_cache_question
from rag_assistant.config import PROMPT_TEMPLATE_VERSION

logger = logging.getLogger(__name__)


class RedisSemanticCache:
    """
    LRU-ish cap via a list of entry ids: LPUSH on store, RPOP+DEL when over max.
    Embeddings stored as JSON arrays for simplicity (decode_responses=True).
    """

    def __init__(
        self,
        *,
        url: str,
        key_prefix: str,
        max_entries: int,
        similarity_threshold: float,
        enabled: bool,
    ) -> None:
        self.url = url
        self.key_prefix = key_prefix.rstrip(":") or "rag:sc:v1"
        self.max_entries = max(1, int(max_entries))
        self.similarity_threshold = float(similarity_threshold)
        self.enabled = enabled
        self._r: Any = None
        if self.enabled:
            import redis

            self._r = redis.from_url(self.url, decode_responses=True)
            self._r.ping()

    def _lru_key(self) -> str:
        return f"{self.key_prefix}:lru"

    def _hash_key(self, entry_id: str) -> str:
        return f"{self.key_prefix}:h:{entry_id}"

    def _client(self) -> Any:
        assert self._r is not None
        return self._r

    def lookup(
        self,
        query_vector: np.ndarray,
        *,
        index_fingerprint: str,
        llm_provider: str,
        model_label: str,
    ) -> CacheEntry | None:
        if not self.enabled:
            return None
        try:
            r = self._client()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis semantic cache connect failed: %s", exc)
            return None

        q = np.asarray(query_vector, dtype=np.float32).reshape(-1)
        qn = float(np.linalg.norm(q))
        if qn < 1e-12:
            return None
        q = q / qn

        try:
            ids = r.lrange(self._lru_key(), 0, -1)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis semantic cache LRANGE failed: %s", exc)
            return None

        # Newest-first (LPUSH head); prefer recent hits
        for eid in ids:
            try:
                raw = r.hgetall(self._hash_key(eid))
            except Exception:
                continue
            if not raw:
                continue
            if raw.get("index_fingerprint") != index_fingerprint:
                continue
            if raw.get("llm_provider") != llm_provider or raw.get("model_label") != model_label:
                continue
            if raw.get("prompt_template_version") != PROMPT_TEMPLATE_VERSION:
                continue
            try:
                emb = json.loads(raw.get("embedding", "[]"))
            except json.JSONDecodeError:
                continue
            v = np.asarray(emb, dtype=np.float32).reshape(-1)
            vn = float(np.linalg.norm(v))
            if vn < 1e-12:
                continue
            v = v / vn
            sim = float(np.dot(q, v))
            if sim >= self.similarity_threshold:
                logger.info("Semantic cache hit (Redis, L2 similarity %.4f)", sim)
                try:
                    hits = json.loads(raw.get("hits", "[]"))
                except json.JSONDecodeError:
                    hits = []
                return CacheEntry(
                    question=raw.get("question", ""),
                    embedding=list(emb),
                    answer=raw.get("answer", ""),
                    hits=hits,
                    prompt=raw.get("prompt", ""),
                    index_fingerprint=index_fingerprint,
                    llm_provider=llm_provider,
                    model_label=model_label,
                    prompt_template_version=raw.get("prompt_template_version", PROMPT_TEMPLATE_VERSION),
                    created_at=raw.get("created_at", ""),
                )
        return None

    def lookup_exact(
        self,
        question: str,
        *,
        index_fingerprint: str,
        llm_provider: str,
        model_label: str,
    ) -> CacheEntry | None:
        if not self.enabled:
            return None
        try:
            r = self._client()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis semantic cache connect failed: %s", exc)
            return None

        key = normalize_cache_question(question)
        if not key:
            return None

        try:
            ids = r.lrange(self._lru_key(), 0, -1)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis semantic cache LRANGE failed: %s", exc)
            return None

        for eid in ids:
            try:
                raw = r.hgetall(self._hash_key(eid))
            except Exception:
                continue
            if not raw:
                continue
            if raw.get("index_fingerprint") != index_fingerprint:
                continue
            if raw.get("llm_provider") != llm_provider or raw.get("model_label") != model_label:
                continue
            if raw.get("prompt_template_version") != PROMPT_TEMPLATE_VERSION:
                continue
            if normalize_cache_question(raw.get("question", "")) != key:
                continue
            logger.info("Semantic cache hit (Redis, L1 exact)")
            try:
                emb = json.loads(raw.get("embedding", "[]"))
            except json.JSONDecodeError:
                continue
            try:
                hits = json.loads(raw.get("hits", "[]"))
            except json.JSONDecodeError:
                hits = []
            return CacheEntry(
                question=raw.get("question", ""),
                embedding=list(emb) if isinstance(emb, list) else [],
                answer=raw.get("answer", ""),
                hits=hits,
                prompt=raw.get("prompt", ""),
                index_fingerprint=index_fingerprint,
                llm_provider=llm_provider,
                model_label=model_label,
                prompt_template_version=raw.get("prompt_template_version", PROMPT_TEMPLATE_VERSION),
                created_at=raw.get("created_at", ""),
            )
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
        try:
            r = self._client()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis semantic cache store skipped (connect): %s", exc)
            return

        emb = np.asarray(query_vector, dtype=np.float32).reshape(-1).tolist()
        eid = uuid.uuid4().hex
        lru = self._lru_key()
        hk = self._hash_key(eid)
        mapping = {
            "question": question.strip(),
            "embedding": json.dumps(emb),
            "answer": answer,
            "hits": json.dumps(hits, ensure_ascii=False),
            "prompt": prompt,
            "index_fingerprint": index_fingerprint,
            "llm_provider": llm_provider,
            "model_label": model_label,
            "prompt_template_version": PROMPT_TEMPLATE_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            pipe = r.pipeline(transaction=True)
            pipe.hset(hk, mapping=mapping)
            pipe.lpush(lru, eid)
            pipe.execute()
            while int(r.llen(lru)) > self.max_entries:
                old = r.rpop(lru)
                if old:
                    r.delete(self._hash_key(old))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis semantic cache store failed: %s", exc)
