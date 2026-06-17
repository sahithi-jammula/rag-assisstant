# RAG Assistant — Deep Learning

A **Retrieval-Augmented Generation (RAG)** application for **deep learning** Q&A: answers are **grounded in your documents** (e.g. [*Dive into Deep Learning*](https://d2l.ai/)–style Markdown/PDF and uploads) before calling an LLM. The stack is **explicit and modular**—loaders, chunking, embeddings, FAISS, hybrid retrieval (dense + BM25 + RRF + rerank), semantic cache, HyDE, and generation are separate components, not a hidden orchestration framework.

---

## Purpose

Build and operate a **transparent RAG pipeline** you can inspect end-to-end: see which chunks grounded each answer, tune retrieval and models in one place (`config.py`), and swap **Gemini** or **OpenAI** for generation. The project targets **documentation-heavy** corpora (textbooks, notes, PDFs) placed under `data/corpus/` or uploaded in the UI.

**Out of scope:** agent frameworks, tool-calling copilots, live model training, and **automatic web crawling** at query time. For pipeline diagrams and boundaries, see [pipeline overview](docs/pipeline-overview.md).

---

## Features

- **Hybrid retrieval** — FAISS dense search, **BM25**, **RRF** fusion, **cross-encoder reranking**, **HyDE** on the dense query path, optional **chapter metadata** filters ([advanced-rag.md](docs/advanced-rag.md)).
- **Semantic cache** — JSON file or Redis ([semantic-caching.md](docs/semantic-caching.md)).
- **Swappable LLM** — Gemini or OpenAI via `LLM_PROVIDER` in `config.py`; **`echo`** for dry runs without an API. Keys in `.env` only ([llm-providers.md](docs/llm-providers.md)).
- **Streamlit UI** — Rebuild index, chat, **retrieved chunks** with sources and scores.

---

## Repository layout

| Path | Contents |
|------|----------|
| [`src/rag_assistant/`](src/rag_assistant/) | Pipeline code: `loaders/` → `chunking/` → `embeddings/` → `vectorstore/` → `retrieval/` → `cache/` → `llm/` → `pipeline/`. Tunables: [`config.py`](src/rag_assistant/config.py). |
| [`app/streamlit_app.py`](app/streamlit_app.py) | Web UI. |
| [`docs/`](docs/README.md) | Documentation index ([`docs/README.md`](docs/README.md)). |
| [`scripts/`](scripts/README.md) | `sync_d2l_en.py` for optional D2L English corpus. |
| [`samples/`](samples/) | Small Markdown examples for a first index. |
| [`.streamlit/config.toml`](.streamlit/config.toml) | Optional Streamlit server defaults (e.g. bind address). |
| [`docker-compose.yml`](docker-compose.yml) | Optional Redis Stack when using `SEMANTIC_CACHE_BACKEND = "redis"`. |
| [`.env.example`](.env.example) | API key template → copy to `.env` (do not commit `.env`). |

Generated data under `data/` is mostly gitignored; see [document ingestion](docs/document-ingestion.md) and [index persistence](docs/index-persistence.md).

---

## Tech stack

Python **3.11+**, **Streamlit**, **sentence-transformers** (embeddings + cross-encoder), **FAISS**, **rank-bm25**, **langchain-text-splitters**, **pypdf**, **Gemini** / **OpenAI** SDKs, optional **Redis**. Details: [technology-stack.md](docs/technology-stack.md). Dependencies: [`requirements.txt`](requirements.txt).

---

## Quick start

1. Python **3.11+** and a venv ([development-setup.md](docs/development-setup.md)).
2. `pip install -r requirements.txt`
3. Copy `.env.example` → `.env`; set the key matching **`LLM_PROVIDER`** in [`src/rag_assistant/config.py`](src/rag_assistant/config.py).
4. Optional: `python scripts/sync_d2l_en.py` for full D2L English sources, or use `samples/` only.
5. From repo root: `streamlit run app/streamlit_app.py`
6. Sidebar → **Rebuild index** → ask a question → expand **Retrieved chunks**.

Optional Redis: `docker compose up -d` and set cache backend in `config.py` ([redis-stack.md](docs/redis-stack.md)).

---

## Configuration

| Location | Role |
|----------|------|
| **`.env`** | API keys only. |
| **`src/rag_assistant/config.py`** | Models, chunking, retrieval pools, HyDE, cache, `LLM_PROVIDER`, etc. |

---

## Documentation index

| Topic | Doc |
|-------|-----|
| Doc reading order + glossary | [`docs/README.md`](docs/README.md) |
| Architecture | [`docs/architecture.md`](docs/architecture.md) |
| Pipeline flowcharts | [`docs/pipeline-overview.md`](docs/pipeline-overview.md) |
| Retrieval stack + knobs | [`docs/advanced-rag.md`](docs/advanced-rag.md) |
| Commands & debugging | [`docs/scripts-and-commands.md`](docs/scripts-and-commands.md) |
| Secrets & network exposure | [`docs/security-and-secrets.md`](docs/security-and-secrets.md) |

---

## Public deployment

The UI has **no built-in login**. A public URL can incur **LLM cost** and allow **file uploads** to the server. Restrict network access or add auth at the edge; keep keys in the host environment or a secrets manager. See [security-and-secrets.md](docs/security-and-secrets.md).

---

## License

Add a **LICENSE** file to your fork when you publish. Cloned **D2L** content remains under upstream [d2l-en](https://github.com/d2l-ai/d2l-en) terms.

---

## Checkout folder name

The parent folder name (e.g. `rag-assistant`) does not affect imports; the package is `rag_assistant` under `src/`.
