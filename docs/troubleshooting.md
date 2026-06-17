# Troubleshooting

For a consolidated **debug checklist** and **copy-paste env commands**, see [scripts-and-commands.md](scripts-and-commands.md#debugging-checklist).

## Windows path and long paths

- Prefer working under a short path like `c:\rag-assistant`.
- If you hit rare “path too long” errors when pip caching, enable long paths or set `PIP_CACHE_DIR` to a short directory.

## `rank-bm25` / `ModuleNotFoundError: No module named 'rank_bm25'`

Advanced hybrid retrieval requires **`rank-bm25`** (see `requirements.txt`). After pulling new code:

```powershell
pip install -r requirements.txt
```

## Virtual environment activation errors

If PowerShell blocks scripts:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

(Adjust per your org policy.)

## `faiss-cpu` install failures

- Ensure you are on a **64-bit** Python.
- Upgrade pip/setuptools/wheel before retrying.
- If a prebuilt wheel is unavailable for your exact Python version, you may need a slightly different Python patch release—try 3.11.x LTS line.

## `sentence-transformers` / PyTorch download issues

First model download can be slow. If corporate proxy blocks Hugging Face:

- Set `HF_ENDPOINT` or configure proxy env vars per Hugging Face documentation.
- Or download the model on an open network once; cache lives under your user cache (HF home).

### Windows long paths and large wheels (Python 3.13 / Store Python)

Installing `torch` (pulled in by `sentence-transformers`) can fail on Windows with errors like **No such file or directory** under a very deep `site-packages` path. Mitigations:

- Enable **Windows long path support** (see Microsoft / pip documentation linked in pip’s hint).
- Prefer **Python 3.11 or 3.12** from python.org into a short path (for example `C:\Python312\`) and a venv under a short folder.
- Keep the repo under a **short path** (for example `C:\dev\rag-assistant`).

### SSL / certificate errors (Hugging Face **or** Gemini / gRPC)

If logs show **`SSLCertVerificationError`** / **`certificate verify failed: unable to get local issuer certificate`** when loading `sentence-transformers/all-MiniLM-L6-v2`:

1. **Install current deps and restart Streamlit** — the app calls **`truststore.inject_into_ssl()`** so Python uses the **same certificate store as Windows** (Edge often works while Python failed before). It also sets **`SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE`** from **`certifi`** when those env vars are empty. Run:

   ```powershell
   pip install -r requirements.txt
   streamlit run app/streamlit_app.py
   ```

   You should see a log line like: `TLS: truststore.inject_into_ssl() enabled`.

2. **Still failing on Windows Store Python** — install **Python 3.11+ from [python.org](https://www.python.org/downloads/windows/)**, create a **new venv**, `pip install -r requirements.txt` again. Store builds are a frequent source of odd TLS behavior.

3. **Corporate SSL inspection (Zscaler, Blue Coat, etc.)** — Python must trust your organization’s root CA. Ask IT for the root certificate PEM file, then before starting Streamlit:

   ```powershell
   $env:SSL_CERT_FILE = "C:\path\to\corp-root.pem"
   $env:REQUESTS_CA_BUNDLE = $env:SSL_CERT_FILE
   streamlit run app/streamlit_app.py
   ```

4. **Last resort (insecure)** — only on a trusted lab machine, Hugging Face documents `HF_HUB_DISABLE_SSL_VERIFICATION=1`. **Do not** use this for real secrets or production.

### Gemini / `google.generativeai` and gRPC TLS

The legacy SDK defaults to **gRPC**, which uses its own OpenSSL trust path; on some Windows setups you see **`ssl_transport_security.cc`** / **`Handshake failed`** / **`CERTIFICATE_VERIFY_FAILED`** even when Hugging Face works.

**This project defaults `GEMINI_TRANSPORT` to `rest`**, so Gemini calls go over **HTTPS** (same TLS stack as `truststore` / `certifi`). You can override in `.env`:

```env
GEMINI_TRANSPORT=rest
```

Use `grpc` only if you need it and your machine trusts gRPC’s roots (or set `GRPC_DEFAULT_SSL_ROOTS_FILE_PATH` — see `ssl_utils`).

The console message that **support for `google.generativeai` has ended** is a **deprecation notice** from Google: the package still works today, but you should plan to migrate to the newer **`google.genai`** SDK when you refactor; it is not the cause of the SSL line by itself.

## CUDA vs CPU

Phase 1 assumes **CPU** inference for embeddings. If you install GPU PyTorch by mistake, it still works but may warn about CUDA availability. For learning, CPU is simpler.

## Gemini errors

| Error vibe | What to check |
|------------|---------------|
| 401/403 | API key missing/incorrect; billing or API enablement for Gemini in Google AI Studio / Cloud console. |
| Resource exhausted / quota | Free tier limits; wait or switch project/key per Google policy. |
| Model not found (404) | The model id is wrong or retired. Set **`GEMINI_MODEL`** in **`src/rag_assistant/config.py`** to a current id (see [Gemini models](https://ai.google.dev/gemini-api/docs/models)). |
| **429 / Too many requests / quota** | Free tier limits **requests per minute per model** (often low, e.g. 5/min for some models). Wait **30–60 seconds** between questions, avoid resubmitting quickly, or enable billing / use another project key. See [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits). |

## “No index loaded”

You need a successful **Rebuild index** after documents exist. If `data/index/` was copied from another machine with a different `faiss` build, rebuild locally.

## PDF text looks wrong

Not a bug in RAG specifically—**extraction** lost layout. Prefer Markdown sources or a stronger PDF pipeline in Phase 2.

## Empty retrieval / irrelevant chunks

- Corpus may not contain the answer.
- Try smaller `CHUNK_SIZE` or larger `TOP_K` (tradeoffs—see [rag-pipeline-deep-dive.md](rag-pipeline-deep-dive.md)).
- Ensure the same embedding model name was used for build and query (changing model without rebuild causes nonsense similarity).

## Streamlit reruns

Streamlit reruns the script top-to-bottom on interaction. If you store heavy models only in session state after first load, performance is fine; the sample app follows that pattern.

## Semantic cache with Redis disabled or unreachable

If `SEMANTIC_CACHE_BACKEND=redis` and Redis is not running, cache initialization **fails** and the app **disables semantic caching** for that process (queries still work). Start Redis: from the repo root run `docker compose up -d` and ensure `REDIS_URL` matches (see [redis-stack.md](redis-stack.md)).

## `METADATA_FILTER_CHAPTERS` yields no chunks

Filters apply to chunks whose **`metadata.chapter`** or **`source`** path matches a token. **Rebuild the index** after adding `metadata` at index time; an old index may lack `metadata` fields (path-only matching may still work if chapter folder names appear in `source`).

## Related reading

- [scripts-and-commands.md](scripts-and-commands.md) — Commands and debug checklist.
- [development-setup.md](development-setup.md) — Baseline install.
- [index-persistence.md](index-persistence.md) — Index files and rebuild semantics.
