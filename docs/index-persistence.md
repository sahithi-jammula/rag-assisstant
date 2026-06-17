# Index persistence (FAISS + metadata)

The vector index is **persisted** so the corpus is not re-embedded on every app restart. You can still **force a full rebuild** when documents or embedding settings change.

## Files under `data/index/`

The application writes a small set of artifacts (exact names are defined in `rag_assistant.config`):

| Artifact | Role |
|----------|------|
| FAISS index file | Binary vectors and graph structures for search. |
| `metadata.json` | Parallel array of chunk records: text, source path, chunk index, optional **`metadata`** (e.g. chapter folder), optional build info. |
| `index_info.json` | Build manifest: timestamp, embedding model id, chunking parameters, list of source paths and content hashes. |

**Invariant**: row `i` in the FAISS index corresponds to `metadata["chunks"][i]` (same ordering).

## Why two JSON files?

- **`metadata.json`**: everything retrieval needs at query time (chunk text for prompting and UI).
- **`index_info.json`**: diagnostics and “should I rebuild?” hints without loading full chunk bodies twice.

Keeping them separate is a readability choice; you could merge them in a fork.

## When to rebuild

Rebuild (full re-ingest, re-chunk, re-embed, overwrite) when:

- Files in `data/corpus/` or `data/uploads/` were added, edited, or removed.
- You changed **embedding model** or **chunking parameters** in config.
- You suspect corruption or you switched machines with incompatible FAISS builds (rare with `IndexFlatIP`, but possible if you change libraries dramatically).

**Rebuild semantics** in the UI:

1. Load all documents from configured roots.
2. Split into chunks.
3. Encode all chunk texts to vectors.
4. Construct a fresh FAISS index.
5. Atomically replace persisted files (write temp then rename where feasible; see implementation).

## Partial / incremental updates (not implemented)

Production systems often incrementally upsert changed documents. This repo intentionally uses **full rebuild** for clarity. Incremental re-embed is an optional enhancement for a fork.

## Loading at startup

On app start, the retriever attempts to `load()` the persisted index. If missing, the UI prompts you to run **Rebuild index** after you place documents in `data/corpus/` or upload files.

## Related reading

- [architecture.md](architecture.md) — Index build sequence diagram.
- [scripts-and-commands.md](scripts-and-commands.md) — Rebuild workflow and debugging.
- [troubleshooting.md](troubleshooting.md) — If load fails after a library upgrade.
