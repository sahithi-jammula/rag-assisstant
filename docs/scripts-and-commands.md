# Scripts, commands, and operator reference

This page ties together **what to run**, **what each script does**, and **how to debug**. It complements [pipeline-overview.md](pipeline-overview.md) and [development-setup.md](development-setup.md).

---

## Query-time stack (reference)

At query time the app always runs **semantic cache** (possible hit) → **HyDE** on the dense path → **FAISS pool** → **BM25** → **RRF** → **cross-encoder rerank** → prompt → **LLM**. Tune pools, models, and cache in **`src/rag_assistant/config.py`** (not environment toggles for those features). Details: [advanced-rag.md](advanced-rag.md), [semantic-caching.md](semantic-caching.md).

---

## Dependencies (Python)

Declared in **`requirements.txt`** at the repo root (install with `pip install -r requirements.txt` inside your venv).

| Package | Role in this project |
|---------|------------------------|
| `streamlit` | Web UI (`app/streamlit_app.py`) |
| `sentence-transformers` | Embedding model + optional CrossEncoder reranker |
| `faiss-cpu` | Vector index (inner product on L2-normalized vectors) |
| `langchain-text-splitters` | `RecursiveCharacterTextSplitter` for chunking |
| `google-generativeai` | Default Gemini LLM client |
| `pypdf` | PDF text extraction |
| `numpy` | Vector math |
| `python-dotenv` | Load `.env` in the app entrypoint |
| `certifi`, `truststore` | TLS for downloads / API calls (see troubleshooting) |
| `rank-bm25` | BM25 for hybrid retrieval |
| `redis` | **Client only** when `SEMANTIC_CACHE_BACKEND = "redis"` in `config.py`; Redis **server** via Docker ([redis-stack.md](redis-stack.md)) |

**Not in `requirements.txt`:** **Git** (required only for `sync_d2l_en.py`), **Docker** (optional, for Redis Stack).

---

## Scripts (purpose)

| Path | Purpose |
|------|--------|
| **`app/streamlit_app.py`** | Main UI: corpus paths, **live values from `config.py`**, uploads, **Rebuild index**, chat, retrieved chunks, cache-hit captions. Prepends `src/` to `sys.path`. Loads **`.env`** for API keys only. |
| **`scripts/sync_d2l_en.py`** | Sparse-clone [d2l-ai/d2l-en](https://github.com/d2l-ai/d2l-en) into `data/corpus/d2l-en/` (chapter folders + minimal files). Needs **Git** on `PATH`. |
| **`docker-compose.yml`** | **Redis Stack** if you set `SEMANTIC_CACHE_BACKEND = "redis"` in `config.py`. Not required for JSON file cache. |

There is no separate CLI “query” script; questions go through Streamlit or a short Python snippet calling `rag_assistant.pipeline.query.answer_question`.

---

## Commands to run (typical workflow)

From the **repository root**, with venv activated (see [development-setup.md](development-setup.md)):

### 1. Install and env

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

```powershell
# Optional: set in .env for this session, or use a .env line — only keys, not other app settings
$env:GEMINI_API_KEY = "your-key-here"
```

All other settings (models, `LLM_PROVIDER`, cache backend, thresholds, chapter filters) are edited in **`src/rag_assistant/config.py`**.

### 2. (Optional) Full D2L English corpus

```powershell
python scripts/sync_d2l_en.py
```

Fresh clone:

```powershell
python scripts/sync_d2l_en.py --clean
```

```powershell
# Optional: only if config.py has SEMANTIC_CACHE_BACKEND = "redis"
docker compose up -d
```

### 3. Run the app

```powershell
streamlit run app/streamlit_app.py
```

Then: sidebar → **Rebuild index** → ask a question in chat.

---

## Commands kept for reference (copy-paste)

**Echo LLM (no API key)** — set `LLM_PROVIDER = "echo"` in `src/rag_assistant/config.py`, then:

```powershell
streamlit run app/streamlit_app.py
```

**Semantic cache:** edit `SEMANTIC_CACHE_BACKEND`, `SEMANTIC_CACHE_SIMILARITY_THRESHOLD`, `METADATA_FILTER_CHAPTERS`, etc. in **`config.py`**.

**Redis:** set `SEMANTIC_CACHE_BACKEND = "redis"` and `REDIS_URL` in **`config.py`**, run `docker compose up -d`, then start Streamlit.

**More verbose logging (example one-off):**

```powershell
$env:PYTHONWARNINGS = "default"
python -c "import logging; logging.basicConfig(level=logging.DEBUG); ..."
```

For Streamlit, prefer setting `logging.basicConfig` in `streamlit_app.py` temporarily during local debug, or run with `streamlit run ... --logger.level=debug` per Streamlit docs.

---

## Debugging checklist

1. **Import / `ModuleNotFoundError`** — Run `pip install -r requirements.txt` from the **same** venv you use for `streamlit`. See [troubleshooting.md](troubleshooting.md) (Windows long paths, Store Python).
2. **“No index loaded”** — Run **Rebuild index** after documents exist under `data/corpus/`, `data/uploads/`, or `samples/`.
3. **Empty or irrelevant chunks** — Corpus gap vs question; try `TOP_K`, `CHUNK_SIZE`; confirm embedding model in `index_info.json` matches `EMBEDDING_MODEL_NAME`.
4. **Metadata filter returns nothing** — Typo in `METADATA_FILTER_CHAPTERS`; token must match `metadata.chapter` or path segment (`chapter_*`). Rebuild index.
5. **Semantic cache never hits** — Lower `SEMANTIC_CACHE_SIMILARITY_THRESHOLD` in `config.py` for experiments; confirm same Gemini model / `LLM_PROVIDER` as when the entry was stored.
6. **Redis configured but down** — If `SEMANTIC_CACHE_BACKEND = "redis"` and Redis is unreachable, the app **falls back to the JSON file cache** and logs a warning. Fix Redis or set backend to `"json"` in `config.py`.
7. **Gemini / TLS** — Set `GEMINI_TRANSPORT = "rest"` in `config.py` on Windows; see [troubleshooting.md](troubleshooting.md).

**Files worth inspecting:**

| Artifact | What it tells you |
|----------|-------------------|
| `data/index/index_info.json` | Build time, chunk count, embedding model, chunk params |
| `data/index/metadata.json` | Chunk records (text, source, `metadata`, …) |
| `data/cache/semantic_cache.json` | JSON cache entries (if backend is `json`) |
| Sidebar in Streamlit | Live snapshot of `config.py` (cache backend, threshold, HyDE max chars, chapter filter, …) |

**Code entrypoints for breakpoints:**

| Area | File |
|------|------|
| Index build | `rag_assistant.pipeline.indexing.build_persisted_index` |
| Question path | `rag_assistant.pipeline.query.answer_question` |
| HyDE merge | `rag_assistant.retrieval.hyde.maybe_hyde_dense_vector` |
| Retrieval | `rag_assistant.retrieval.advanced.retrieve_for_query` |
| Cache | `rag_assistant.cache.semantic_cache.build_semantic_cache_from_config` |

---

## Related reading

- [results-and-verification.md](results-and-verification.md) — What “good” looks like after setup.
- [scripts/README.md](../scripts/README.md) — D2L sync script details.
- [troubleshooting.md](troubleshooting.md) — Errors and mitigations.
- [config.py](../src/rag_assistant/config.py) — Authoritative env defaults and names.
