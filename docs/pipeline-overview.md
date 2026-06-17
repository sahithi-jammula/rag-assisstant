# RAG pipeline overview

This project runs one **end-to-end RAG pipeline**: index documents with **loaders → chunking (with metadata) → embeddings → FAISS**; answer questions with **semantic cache** (possible short-circuit), **HyDE** on the dense query path, **dense + BM25 + RRF + cross-encoder rerank**, then **RAG prompt → LLM**. Tunables live in **`src/rag_assistant/config.py`**; API keys only in **`.env`**.

## Index build

```mermaid
flowchart LR
  subgraph ingest [Index build]
    D[Documents]
    L[Loaders]
    C[Chunk + metadata]
    E[Embed]
    F[FAISS persist]
    D --> L --> C --> E --> F
  end
```

## Query path

```mermaid
flowchart TB
  subgraph query [Query]
    Q[Question]
    EM[Embed question]
    SC{Semantic cache hit?}
    HY[HyDE merge dense vector]
    DS[Dense FAISS pool]
    BM[BM25]
    RRF[RRF fuse]
    CE[Cross-encoder rerank]
    PR2[RAG prompt]
    LLM2[LLM]
    ST[Cache store]
    OUT[Answer + chunks]
    Q --> EM --> SC
    SC -->|hit| OUT
    SC -->|no| HY --> DS --> BM --> RRF --> CE --> PR2 --> LLM2 --> ST --> OUT
  end
```

## Extensibility

1. **Stable hit shape** — Keep retrieval outputs shaped for the prompt builder and UI (`text`, `source`, `score`, `row_id`, …).
2. **Version the index** — `index_info.json` records embedding model and chunk params; semantic cache uses `retrieval_profile_fingerprint()` so settings stay consistent with stored answers.
3. **Change behavior in `config.py`** — Constants and template version; keys stay in `.env`.

## Out of scope

- In-repo **agent** frameworks and tool-calling orchestration (handle that in a separate codebase if needed).
- **Web crawling** at query time; you supply documents under `data/corpus/` and `data/uploads/`.

**Optional infra:** `scripts/sync_d2l_en.py` (D2L corpus), `docker-compose.yml` (Redis when `SEMANTIC_CACHE_BACKEND = "redis"`).

## Related reading

- [advanced-rag.md](advanced-rag.md) — Stages and `config.py` constants.
- [architecture.md](architecture.md) — Modules and sequence diagrams.
- [technology-stack.md](technology-stack.md) — Libraries.
- [scripts-and-commands.md](scripts-and-commands.md) — Commands and debugging.
