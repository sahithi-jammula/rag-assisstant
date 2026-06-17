# RAG pipeline deep dive

This document explains **what each stage is doing mathematically and practically**, so you can debug behavior and know what to tune first.

## 1. Document loading

**Goal**: produce a list of logical documents, each with:

- `page_content` (or equivalent): raw text
- `metadata["source"]`: a stable string you can show to users (file path or upload name)

**Why it matters**: garbage text (broken PDF extraction, wrong encoding) becomes garbage chunks and garbage embeddings. Always inspect a few loaded files when onboarding a new corpus.

## 2. Chunking

**Goal**: split long documents into segments that:

- Fit comfortably in the embedding model’s context window (for MiniLM this is large, but smaller chunks often retrieve more precisely).
- Preserve local context (e.g. a paragraph about `ImagePullBackOff` stays mostly in one chunk).

### Recursive character splitting

`RecursiveCharacterTextSplitter` tries separators in order (paragraph breaks, newlines, spaces) so splits feel natural.

### Key parameters

| Parameter | Typical effect |
|-----------|----------------|
| `chunk_size` | Larger chunks carry more context per hit; smaller chunks localize relevance. |
| `chunk_overlap` | Reduces the chance that a boundary cuts an important sentence in half across two chunks. |

**Tradeoff**: more overlap → more redundant chunks → larger index and slower builds.

## 3. Embeddings

**Goal**: map each chunk of text to a fixed-length vector such that “semantically similar” texts map to nearby vectors.

For `all-MiniLM-L6-v2`, vectors are often **L2-normalized** before similarity search so that **inner product equals cosine similarity** (up to numerical precision).

### What “relevant” means here

Relevance is **not** human judgment directly; it is **geometric proximity in embedding space** learned from large-scale training data. For textbook-style deep learning prose:

- Strong for paraphrases and definitions (“What is softmax?”).
- Weaker for one-off homework numbers unless similar worked examples exist in your corpus.

## 4. Vector store (FAISS)

**Goal**: given a query vector, return the ids/scores of the closest chunk vectors quickly.

Phase 1 uses a flat inner-product index on normalized vectors (equivalent to cosine similarity ranking for normalized vectors).

### Why top-k is not “truth”

Top-k returns the **k closest** chunks, not necessarily **k correct** chunks. If your corpus lacks the answer, you still get k neighbors—often confidently wrong if the LLM overfits to them.

## 5. Retrieval for prompting

**Goal**: assemble a **context block** from top-k chunks, with clear separators, and feed it to the LLM with the user question.

### Context window and “stuffing”

Gemini models have large context windows, but:

- Very long contexts increase latency and cost.
- Models can “lose focus” in the middle of huge contexts.

Phase 1 keeps a bounded amount of retrieved text (derived from `TOP_K` and chunk size). Tune rather than dumping the entire corpus.

## 6. Prompting

A minimal grounded prompt contains:

1. **Instructions**: answer from context; admit when context is insufficient.
2. **Context**: retrieved chunks with source labels.
3. **Question**: the user’s natural language query.

**Transparency**: the Streamlit UI shows retrieved chunks separately from the final answer so you can see whether grounding helped.

## 7. Generation (Gemini)

The model produces fluent text conditioned on the prompt. Even with good retrieval, models may:

- **Hallucinate** details not in the chunks.
- **Merge** similar concepts incorrectly.

Mitigations: stricter prompts, citation requirements, reranking, evaluation sets—see [advanced-rag.md](advanced-rag.md) and [phase-roadmap.md](phase-roadmap.md).

## Failure modes (teaching checklist)

| Symptom | Likely causes |
|---------|----------------|
| Empty or nonsense retrieval | Wrong index loaded; corpus empty; embedding model mismatch between build and query. |
| “Almost right” answers | Chunk size too large/small; weak embedding model for your domain; need reranking. |
| Stale answers after editing docs | Index not rebuilt; persistence still pointing at old vectors. |
| PDF answers look random | PDF extraction noise; consider Markdown sources or a better PDF pipeline. |

## Related reading

- [architecture.md](architecture.md) — Where each stage lives in code.
- [index-persistence.md](index-persistence.md) — How vectors and metadata stay in sync on disk.
- [document-ingestion.md](document-ingestion.md) — Formats and folder conventions.
