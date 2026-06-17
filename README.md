# RAG Assistant — Deep Learning (Basic + Advanced RAG)

A small **Retrieval-Augmented Generation** app: ask questions about **deep learning** (grounded in *Dive into Deep Learning* sources and your uploads) before calling an LLM. **Roadmap:** [Phase 1 = Basic RAG, Phase 2 = Advanced RAG](docs/phase-roadmap.md) in this repo only; **agents** belong in a **separate project** if you need them.

> **Checkout folder:** a generic name like `rag-assistant` is recommended; the code does not depend on the folder name (only `src/rag_assistant/` is import path).

## Principles

- **Documentation-grounded RAG** (Basic + Advanced): explicit loaders → chunking → embeddings → FAISS → hybrid retrieval → semantic cache → swappable LLM—not a hidden orchestration framework.
- **Transparency**: the UI shows retrieved chunks, sources, and scores so you can audit grounding.
- **Configuration split**: **`.env`** for API keys only; **`src/rag_assistant/config.py`** for models, retrieval, cache, and HyDE (see [`docs/README.md`](docs/README.md) for the full map).
- **Scope**: learning assistant for *Dive into Deep Learning*–style corpora and your uploads; **agents**, live training, and automatic crawling are intentionally **out of scope** here ([`docs/phase-roadmap.md`](docs/phase-roadmap.md)).

## Renaming the checkout and Cursor

Renaming the directory on disk **does not break** the app (paths are derived from `config.py`). **This README plus `docs/` are the canonical description**—commit them before you push. If you open the repo from a new path, your editor may treat it as a new workspace (**chat history often does not follow** the folder rename); rely on the tracked docs for continuity.

## Documentation (start here)

The project is **documentation-first**. Read [`docs/README.md`](docs/README.md) for the full reading list, glossary, and how each pipeline stage maps to Python modules. For **example D2L questions** and **paraphrases to test semantic caching**, see [`docs/d2l-sample-questions.md`](docs/d2l-sample-questions.md). **Configuration:** edit [`src/rag_assistant/config.py`](src/rag_assistant/config.py). For **API keys only**, copy [`.env.example`](.env.example) to `.env` and set `GEMINI_API_KEY` / `GOOGLE_API_KEY` (Gemini) or `OPENAI_API_KEY` (OpenAI), matching `LLM_PROVIDER` in `config.py`.

**Operators:** [`docs/scripts-and-commands.md`](docs/scripts-and-commands.md) (scripts, dependencies, run/debug commands) · [`docs/results-and-verification.md`](docs/results-and-verification.md) (expected outcomes).

**Deploy / GitHub:** [`docs/aws-deployment.md`](docs/aws-deployment.md) — Docker image, push to personal GitHub without secrets, run on **AWS App Runner**, **EC2 + Docker**, or **ECS/Fargate** (public URL caveats included). **Which AWS services pair with RAG:** [`docs/aws-cloud-rag-learning.md`](docs/aws-cloud-rag-learning.md) (EC2, S3, Lambda, Bedrock, OpenSearch, etc.).

## Quick start

1. Create a virtual environment and install dependencies (see [`docs/development-setup.md`](docs/development-setup.md)).
2. Set the API key that matches **`LLM_PROVIDER`** in `config.py`: **`GEMINI_API_KEY`** or **`GOOGLE_API_KEY`** for Gemini, or **`OPENAI_API_KEY`** for OpenAI (see [`docs/llm-providers.md`](docs/llm-providers.md#openai) for **`OPENAI_MODEL`** and switching).
3. **Optional full book:** from the repo root run `python scripts/sync_d2l_en.py` to sparse-clone [d2l-ai/d2l-en](https://github.com/d2l-ai/d2l-en) into `data/corpus/d2l-en/` (see [`scripts/README.md`](scripts/README.md)). A tiny **bundled** README + `samples/` still allow a first index without the clone.
4. **Optional Redis semantic cache:** `docker compose up -d` then set `SEMANTIC_CACHE_BACKEND=redis` (see [`docs/redis-stack.md`](docs/redis-stack.md)).
5. Run:

```powershell
streamlit run app/streamlit_app.py
```

6. In the sidebar, click **Rebuild index**, then ask a question. Expand **Retrieved chunks** to see what grounded the answer.

## Commands (reference)

| Goal | Command |
|------|--------|
| Install deps | `pip install -r requirements.txt` |
| Sync D2L corpus | `python scripts/sync_d2l_en.py` |
| Start Redis (optional) | `docker compose up -d` |
| Run UI | `streamlit run app/streamlit_app.py` |

See [`docs/scripts-and-commands.md`](docs/scripts-and-commands.md) for `LLM_PROVIDER=echo`, HyDE, metadata filters, cache knobs in `config.py`, and a **debugging checklist**.

## Repository layout

- `docs/` — architecture, stack, security, persistence, roadmap, **scripts-and-commands**, **results-and-verification**.
- `src/rag_assistant/` — modular RAG pipeline (loaders → chunking → embeddings → FAISS → **advanced retrieval** → optional HyDE / metadata filters → **semantic cache** → swappable LLM). See [`docs/advanced-rag.md`](docs/advanced-rag.md).
- `app/streamlit_app.py` — UI.
- `scripts/` — `sync_d2l_en.py` (sparse clone of D2L English sources).
- `docker-compose.yml` — optional **Redis Stack** for `SEMANTIC_CACHE_BACKEND=redis`.
- `samples/` — tiny example Markdown for first-run demos.

## License

Learning project; the **D2L book** has its own license in the upstream repo (CC BY–SA style for prose—see cloned `LICENSE`). Add a license file for *this* repo if you open-source it.
