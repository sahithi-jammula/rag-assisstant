# Development setup

For a consolidated **command cheat sheet** and **debugging checklist**, see [scripts-and-commands.md](scripts-and-commands.md). For **what “working” looks like** in the UI, see [results-and-verification.md](results-and-verification.md).

## Prerequisites

- **Python 3.11+** (3.12 is fine; align with your environment policy if needed).
- A **Gemini** or **OpenAI** API key in **`.env`**, depending on **`LLM_PROVIDER`** in `config.py` (see [llm-providers.md](llm-providers.md)).
- ~1–2 GB free disk for Python packages + the embedding model download (first run).

## Configuration model

- **`src/rag_assistant/config.py`** — models, chunk sizes, retrieval pool sizes, HyDE, semantic cache backend/threshold, chapter filters, `LLM_PROVIDER`, etc. Edit this file to change behavior.
- **`.env` (repo root)** — **only** API keys: `GEMINI_API_KEY` / `GOOGLE_API_KEY` (Gemini) and/or `OPENAI_API_KEY` (OpenAI). Loaded by `app/streamlit_app.py`. No other app variables need to live here.

## Clone and virtual environment

```powershell
cd c:\rag-assistant
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Use whatever directory you cloned into; the Python package is `rag_assistant` under `src/`, not the folder name on disk.

## API keys

Create **`.env`** in the repo root (see **`.env.example`**). Use the key that matches **`LLM_PROVIDER`** in **`src/rag_assistant/config.py`**:

```env
# For Gemini:
GEMINI_API_KEY=your-key-here

# For OpenAI (when LLM_PROVIDER = "openai"):
OPENAI_API_KEY=your-key-here
```

See [llm-providers.md](llm-providers.md#openai) for **`OPENAI_MODEL`** defaults and how to pick a model id.

To test **without** a remote key, set `LLM_PROVIDER = "echo"` in **`config.py`** (stub LLM; retrieval still runs).

## Prepare documents

1. Optionally run `python scripts/sync_d2l_en.py` for the full D2L English Markdown corpus under `data/corpus/d2l-en/`, or add your own Markdown/PDF/text under `data/corpus/`.
2. Or use the Streamlit uploader which writes to `data/uploads/`.

You can also read the small checked-in example under `samples/`.

## Run the app

From the repo root with the virtual environment active:

```powershell
streamlit run app/streamlit_app.py
```

Streamlit prints a local URL (default `http://localhost:8501`).

## First-time flow

1. Start the app.
2. Open the sidebar: confirm paths and `config.py` values.
3. Click **Rebuild index** once documents exist.
4. Ask a question; expand **Retrieved chunks** to inspect grounding.

## PYTHONPATH / imports

`app/streamlit_app.py` prepends `src/` to `sys.path` so `import rag_assistant` works without editable installs.

## Related reading

- [scripts-and-commands.md](scripts-and-commands.md) — Operator reference and debug steps.
- [results-and-verification.md](results-and-verification.md) — Expected results and smoke tests.
- [troubleshooting.md](troubleshooting.md) — When installs or models fail.
- [security-and-secrets.md](security-and-secrets.md) — Key handling rules.
