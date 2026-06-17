# Redis Stack for semantic cache

Semantic caching can persist in **Redis** instead of `data/cache/semantic_cache.json`. The repo includes a **Docker Compose** service using the official **Redis Stack** image (`redis/redis-stack-server`), which bundles Redis with optional modules (RediSearch, etc.). The current implementation uses **plain Redis data types** (hashes + a list); you do not need RediSearch APIs for the cache to work.

## Quick start

1. Start Redis (from the repo root):

   ```bash
   docker compose up -d
   ```

2. Point the app at Redis in **`src/rag_assistant/config.py`**:

   ```python
   SEMANTIC_CACHE_BACKEND = "redis"
   REDIS_URL = "redis://127.0.0.1:6379/0"
   ```

3. For file-based cache only (no Docker), keep:

   ```python
   SEMANTIC_CACHE_BACKEND = "json"
   ```

If `SEMANTIC_CACHE_BACKEND = "redis"` in `config.py` but Redis is unreachable at cache construction time, the app **falls back to the JSON file cache** and logs a warning (queries still work).

## Keys and privacy

- Key prefix defaults to `rag:sc:v1` (override with `REDIS_SEMANTIC_CACHE_KEY_PREFIX`).
- Entries hold **question text**, **answer**, **prompt**, **embedding**, and serialized **hits** — same sensitivity as the JSON cache. See [security-and-secrets.md](security-and-secrets.md).

## Related

- [semantic-caching.md](semantic-caching.md) — Thresholds, invalidation, backends.
- [scripts-and-commands.md](scripts-and-commands.md) — Full command reference and debugging.
- [development-setup.md](development-setup.md) — API key in `.env`; everything else in `config.py`.
