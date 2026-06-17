# RAG Assistant — documentation

Documentation for the **RAG Assistant** project: what the pipeline does, how to run and configure it. **This folder plus the root [`README.md`](../README.md)** are the canonical description of the repository.

## Reading order

1. [architecture.md](architecture.md) — System shape, data flow, Python modules vs pipeline stages.
2. [scripts-and-commands.md](scripts-and-commands.md) — Scripts, dependencies, commands, debugging.
3. [results-and-verification.md](results-and-verification.md) — Expected UI behavior after setup.
4. [pipeline-overview.md](pipeline-overview.md) — End-to-end pipeline flowcharts (index + query).
5. [technology-stack.md](technology-stack.md) — Libraries and reasonable swap options.
6. [rag-pipeline-deep-dive.md](rag-pipeline-deep-dive.md) — Embeddings, chunking, retrieval, prompting, failure modes.
7. [advanced-rag.md](advanced-rag.md) — Hybrid BM25 + dense, RRF, rerank, HyDE, metadata filters; `config.py` knobs.
8. [document-ingestion.md](document-ingestion.md) — Corpus paths, formats, uploads.
9. [index-persistence.md](index-persistence.md) — FAISS on disk, metadata sidecars, rebuild rules.
10. [security-and-secrets.md](security-and-secrets.md) — API keys, logging, data handling.
11. [llm-providers.md](llm-providers.md) — `LLMClient`, `LLM_PROVIDER`, Gemini / OpenAI, adding backends.
12. [semantic-caching.md](semantic-caching.md) — Semantic cache (JSON or Redis), `config.py`, flowchart.
13. [redis-stack.md](redis-stack.md) — Docker Compose Redis Stack for the `redis` cache backend.
14. [development-setup.md](development-setup.md) — Environment, install, run.
15. [troubleshooting.md](troubleshooting.md) — Common errors (Windows, FAISS, Gemini, OpenAI, embeddings, Redis).
16. [d2l-sample-questions.md](d2l-sample-questions.md) — Example questions and paraphrase pairs for cache testing; **`SEMANTIC_CACHE_SIMILARITY_THRESHOLD`**.
17. [deploy-public-demo.md](deploy-public-demo.md) — **Public URL from Git** (Streamlit Community Cloud, Render); secrets, first-time rebuild.

## How docs map to code

| Topic | Code (from repo root) |
|--------|------------------------|
| Document loading | `src/rag_assistant/loaders/` + optional `scripts/sync_d2l_en.py` |
| Chunking | `src/rag_assistant/chunking/` |
| Embeddings | `src/rag_assistant/embeddings/` |
| Vector store | `src/rag_assistant/vectorstore/` |
| Retrieval, HyDE, metadata filters | `src/rag_assistant/retrieval/` |
| Semantic cache (JSON / Redis) | `src/rag_assistant/cache/` |
| Scripts & Docker | `scripts/`, `docker-compose.yml` |
| LLM | `src/rag_assistant/llm/` |
| Orchestration | `src/rag_assistant/pipeline/` |
| UI | `app/streamlit_app.py` |

## Glossary

| Term | Meaning |
|------|--------|
| **Corpus** | All source documents the assistant uses (configured folders + uploads). |
| **Chunk** | A slice of document text sized for embedding and retrieval. |
| **Embedding** | Dense vector for text; similar texts tend to have similar vectors. |
| **Vector store** | Structure for similarity search over chunk vectors (here: FAISS). |
| **Retrieval** | Selecting top-ranked chunks for a question. |
| **Grounding** | Answering from retrieved text so the model cites your corpus, not only parametric knowledge. |
| **RAG** | Retrieval-Augmented Generation: retrieve → prompt → generate. |
| **Semantic cache** | Store of past (question embedding → answer); on a close match, skip retrieval and main LLM call. Backends: JSON under `data/cache/` or **Redis** ([semantic-caching.md](semantic-caching.md), [redis-stack.md](redis-stack.md)). |

## Conventions

- **Scope:** Documentation-grounded RAG with hybrid retrieval, semantic cache, and HyDE—no automatic crawling beyond what you place under `data/corpus/`. No in-repo agent framework.
- **Transparency:** The UI shows retrieved chunks, sources, and scores.
- **Paths:** `data/corpus/` and `data/uploads/` hold content; `data/index/` holds generated indexes (mostly gitignored).

Quick run: [development-setup.md](development-setup.md) and the root [README.md](../README.md).
