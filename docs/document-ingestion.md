# Document ingestion

Phase 1 ingests **Markdown, plain text, and PDFs** from disk. It does **not** crawl external websites at runtime; you add material under `data/corpus/` (including optional **git sparse clones** of open textbooks).

The repository ships a **small tracked hint** under `data/corpus/bundled/` (`README.md` only) plus **`samples/`** so a fresh clone can build a minimal index. For the full **Dive into Deep Learning** English sources, run the helper script below (git sparse-checkout of `chapter_*` trees only).

## Where documents live

| Location | Purpose | Git |
|----------|---------|-----|
| `data/corpus/bundled/` | Tracked `README.md` (how to pull D2L sources) | **Tracked** (exception under `data/corpus/`) |
| `data/corpus/` (other paths) | Long-lived documents you add (PDF, `.md`, `.txt`), e.g. optional `d2l-en/` clone | Ignored except `.gitkeep` and `bundled/**` |
| `data/uploads/` | Files saved from the Streamlit uploader | Ignored |
| `samples/` | Tiny optional examples shipped with the repo for first-run demos | Tracked |

The loader **merges** `data/corpus/`, `data/uploads/`, and `samples/` (if present) when building the index. A fresh clone indexes **`bundled/README.md`** + **`samples/*.md`** after **Rebuild index**; after you run `sync_d2l_en.py`, the index also includes **`data/corpus/d2l-en/`** (gitignored).

## D2L English sources (GitHub: d2l-ai/d2l-en)

To pull **only** top-level `chapter_*` directories (plus `index.md` and license files—not `ci/`, `contrib/`, full `img/`, etc.), run from the project root:

```powershell
python scripts/sync_d2l_en.py
```

By default this creates a shallow sparse clone at:

`data/corpus/d2l-en/`

**Licensing:** the book is under upstream **CC BY–SA** terms (see cloned `LICENSE`). Attribute appropriately if you redistribute derived material.

To refresh from `origin` on an existing clone, run the same command again. For a completely fresh clone:

```powershell
python scripts/sync_d2l_en.py --clean
```

**Requirements:** `git` on your PATH. Then run **Rebuild index** in the Streamlit app.

More detail: [../scripts/README.md](../scripts/README.md).

## Supported formats (Phase 1)

| Extension | Handler | Notes |
|-----------|---------|------|
| `.pdf` | `pypdf` | Extracts text per page; layout-heavy PDFs may be imperfect. |
| `.md` | UTF-8 read | Recommended for technical notes; preserves headings in plain text. |
| `.txt` | UTF-8 read | Simplest path for pasted notes. |

Unsupported files are skipped with a warning in the indexing report.

## Upload path (Streamlit)

1. User selects files in `st.file_uploader`.
2. App writes bytes to `data/uploads/` with a sanitized filename (see code for collision handling).
3. **Rebuild index** re-reads uploads alongside `data/corpus/`.

Uploads persist until you delete them from `data/uploads/` or replace them. If you need “ephemeral only” uploads, that would be a small Phase 1 variant (write to `tempfile` instead)—not the default here.

## Encoding

Markdown and text are read as **UTF-8**. If you have legacy files in other encodings, convert them externally or extend the loader with encoding detection later.

## Normalization

Before chunking, the loader trims excessive whitespace. It does not attempt full HTML → text conversion (you could add an HTML loader in a fork if you ingest web exports).

## Chunk identity and traceability

Each chunk carries metadata including:

- **source**: path string shown in the UI
- **chunk_index**: order within that document after splitting
- **metadata** (at index time): e.g. `{"chapter": "chapter_introduction"}` when the path contains a D2L-style `chapter_*` segment — used for `METADATA_FILTER_CHAPTERS` ([advanced-rag.md](advanced-rag.md)).

This makes it obvious **which file** grounded a retrieval hit.

## Operational tips for D2L / study content

- Prefer **Markdown** from the official repo; headings and code fences chunk cleanly.
- Long chapters are split automatically; use **Retrieved chunks** in the UI to see whether boundaries hurt a specific question.
- For math-heavy sections, retrieval still uses **text**; tune `CHUNK_SIZE` / `TOP_K` if hits feel too fragmented.

## Related reading

- [architecture.md](architecture.md) — Loader module boundary.
- [scripts-and-commands.md](scripts-and-commands.md) — `sync_d2l_en.py` and other commands.
- [index-persistence.md](index-persistence.md) — What happens after chunks exist.
- [rag-pipeline-deep-dive.md](rag-pipeline-deep-dive.md) — Chunk size tradeoffs.
