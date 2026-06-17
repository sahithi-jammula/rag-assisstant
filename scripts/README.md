# Scripts

## `sync_d2l_en.py`

Sparse-clones **[d2l-ai/d2l-en](https://github.com/d2l-ai/d2l-en)** so only top-level **`chapter_*`** directories (plus `index.md`, `LICENSE`, `LICENSE-SUMMARY`) are checked out—no `ci/`, `contrib/`, full `img/`, etc.

**Requirements:** [Git](https://git-scm.com/downloads) on your `PATH`.

**Default output:** `data/corpus/d2l-en/` (scanned by the app’s corpus loader together with `data/corpus/bundled/` and `samples/`).

From the repository root:

```powershell
python scripts/sync_d2l_en.py
```

Fresh re-download (deletes the clone first):

```powershell
python scripts/sync_d2l_en.py --clean
```

Then in Streamlit: **Rebuild index**.

If sparse checkout looks wrong, run with `--clean` or inspect `git sparse-checkout list` inside `data/corpus/d2l-en/`.

## Optional: Redis (semantic cache)

From the repo root, to run **Redis Stack** in Docker (not required unless `SEMANTIC_CACHE_BACKEND=redis`):

```powershell
docker compose up -d
```

See [../docs/redis-stack.md](../docs/redis-stack.md) and the operator runbook [../docs/scripts-and-commands.md](../docs/scripts-and-commands.md).

## More documentation

- [../docs/document-ingestion.md](../docs/document-ingestion.md) — How this fits with the bundled corpus and uploads.
- [../docs/results-and-verification.md](../docs/results-and-verification.md) — What to expect after index + query.
