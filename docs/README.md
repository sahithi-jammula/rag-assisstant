# RAG Assistant — Deep Learning — Documentation

This folder explains **what** the assistant does, **how** each stage of the RAG pipeline works, and **why** it is split into **Basic RAG (Phase 1)** and **Advanced RAG (Phase 2)** in the roadmap. The goal is transparency for learning, not hiding behavior behind opaque frameworks. **Treat these files (and the root `README.md`) as the canonical description of the project** when you publish or rename the checkout directory—IDE chat history is not a substitute.

## Reading order

1. [architecture.md](architecture.md) — System shape, data flow, and how Python modules map to pipeline stages.
2. [scripts-and-commands.md](scripts-and-commands.md) — **Scripts, dependencies, commands, debugging** (operator runbook).
3. [results-and-verification.md](results-and-verification.md) — Expected outcomes after setup; how to read the UI.
4. [phase-roadmap.md](phase-roadmap.md) — **Phase 1 (Basic RAG)** vs **Phase 2 (Advanced RAG)**; flowcharts only.
5. [technology-stack.md](technology-stack.md) — Libraries and services for Basic + Advanced RAG, plus when you might swap them.
6. [rag-pipeline-deep-dive.md](rag-pipeline-deep-dive.md) — Embeddings, chunking, retrieval, prompting, and common failure modes.
7. [advanced-rag.md](advanced-rag.md) — Hybrid BM25 + dense, RRF, rerank, HyDE, metadata filters; `config.py` knobs.
8. [document-ingestion.md](document-ingestion.md) — Where files live, supported formats, and how uploads join the corpus.
9. [index-persistence.md](index-persistence.md) — FAISS on disk, metadata sidecars, and when to rebuild.
10. [security-and-secrets.md](security-and-secrets.md) — API keys, logging, and data handling.
11. [llm-providers.md](llm-providers.md) — Swappable `LLMClient`, `LLM_PROVIDER`, OpenAI/Gemini keys and **`OPENAI_MODEL`**, adding backends.
12. [semantic-caching.md](semantic-caching.md) — Semantic cache (JSON or Redis), `config.py` knobs, flowchart.
13. [redis-stack.md](redis-stack.md) — Docker Compose Redis Stack for the optional `redis` cache backend.
14. [development-setup.md](development-setup.md) — Environment, install, and how to run the app.
15. [troubleshooting.md](troubleshooting.md) — Typical errors (Windows, FAISS, Gemini, OpenAI, embeddings, Redis cache).
16. [d2l-sample-questions.md](d2l-sample-questions.md) — Example D2L-style questions + paraphrase pairs for semantic-cache testing; where to set **`SEMANTIC_CACHE_SIMILARITY_THRESHOLD`**.
17. [aws-deployment.md](aws-deployment.md) — **GitHub + AWS**: Docker image, App Runner / EC2 / Fargate notes, secrets, corpus/index on cloud.
18. [aws-cloud-rag-learning.md](aws-cloud-rag-learning.md) — **EC2 / S3 / Lambda / Bedrock** and related services: what fits this repo vs a second learning project.

## How docs map to code

| Concept in docs | Code location (after clone) |
|-----------------|----------------------------|
| Document loading | `src/rag_assistant/loaders/` + optional `scripts/sync_d2l_en.py` |
| Chunking | `src/rag_assistant/chunking/` |
| Embeddings | `src/rag_assistant/embeddings/` |
| Vector store | `src/rag_assistant/vectorstore/` |
| Advanced retrieval + HyDE + metadata filters | `src/rag_assistant/retrieval/` |
| Semantic cache (JSON / Redis) | `src/rag_assistant/cache/` |
| Scripts & Docker (optional) | `scripts/`, `docker-compose.yml` |
| LLM (swappable) | `src/rag_assistant/llm/` |
| Orchestration | `src/rag_assistant/pipeline/` |
| UI | `app/streamlit_app.py` |

## Glossary

| Term | Meaning |
|------|--------|
| **Corpus** | All source documents you want the assistant to use (folder + uploads). |
| **Chunk** | A contiguous slice of text from a document, sized for embedding and retrieval. |
| **Embedding** | A dense vector representing text; “similar” texts tend to have nearby vectors. |
| **Vector store** | Data structure holding chunk embeddings for similarity search (here: FAISS). |
| **Retrieval** | Finding the top-k chunks most similar to the user question. |
| **Grounding** | Conditioning the model answer on retrieved text so it cites your docs, not only parametric knowledge. |
| **RAG** | Retrieval-Augmented Generation: retrieve → build prompt → generate. |
| **Semantic cache** | Optional store of past (question embedding → answer); skips retrieval + LLM when similar enough. Backends: JSON (`data/cache/`) or **Redis** (see [semantic-caching.md](semantic-caching.md), [redis-stack.md](redis-stack.md)). |

## Conventions in this repo

- **Scope**: documentation-grounded RAG only (**Basic** + **Advanced**); no live training jobs, no automatic crawling at runtime beyond what you clone into `data/corpus/`. **No in-repo agent framework**—use another codebase for agents.
- **Transparency**: the UI shows retrieved chunks, sources, and scores by default.
- **Paths**: `data/corpus/` and `data/uploads/` hold user content; `data/index/` holds generated indexes (gitignored except where noted).
- **Operators**: use [scripts-and-commands.md](scripts-and-commands.md) and [results-and-verification.md](results-and-verification.md) for runbooks, dependency tables, and “what good looks like.”

For the shortest path to run the app, see [development-setup.md](development-setup.md) and the root [README.md](../README.md).
