# Deploy a public demo (Git → URL)

This project is a **Streamlit** app. The simplest path to a **public link** from GitHub is **Streamlit Community Cloud**. Alternatives like **Render** are summarized at the end.

**Secrets:** never commit API keys. Put them only in the host’s **secrets / environment** UI (or local `.env`, gitignored).

---

## Before you deploy

1. **Push the repo to GitHub** (private or public). Confirm **`.env` is not tracked** (`git status` should not list it).
2. In **`src/rag_assistant/config.py`**, set **`LLM_PROVIDER`** to match the key you will add in the cloud (`"gemini"` or `"openai"`). For a **no-key** smoke test only, use `"echo"` (stub answers; HyDE still runs but uses the stub).
3. **Semantic cache:** if `SEMANTIC_CACHE_BACKEND = "redis"` and you have **no** Redis on the host, the app **falls back to JSON** after a failed Redis `ping` (you may see a warning in logs). For the cleanest cloud setup, use **`"json"`** in `config.py` so cache writes under `data/cache/` only.

---

## Option A — Streamlit Community Cloud (recommended)

### 1. Sign in and connect GitHub

1. Open [Streamlit Community Cloud](https://streamlit.io/cloud) and sign in with **GitHub**.
2. Authorize the Streamlit GitHub app for the org/user that owns your repo (you can limit to **only that repository**).

### 2. Create the app

1. **Create app** → pick **repository** and **branch** (e.g. `main`).
2. **Main file path:** `app/streamlit_app.py`  
   (Streamlit runs from the **repo root**; `streamlit_app.py` already adds `src/` to `sys.path`.)
3. **App URL:** Cloud assigns something like `https://<name>.streamlit.app` (you can often customize the subdomain).

### 3. Python version

Community Cloud uses a supported Python version for the runtime. Your project targets **3.11+**; if the UI offers a version picker, choose **3.11** or the closest available.

### 4. Secrets (API keys)

1. After the first deploy (or from **App settings**), open **Secrets** / **Advanced settings**.
2. Paste **TOML** with **root-level** keys only (these become **environment variables**, which this repo reads via `os.environ` the same as `.env` locally):

   **Gemini** (when `LLM_PROVIDER = "gemini"`):

   ```toml
   GEMINI_API_KEY = "your-key-here"
   ```

   Or use `GOOGLE_API_KEY` instead of `GEMINI_API_KEY` if that is what you use in Google AI Studio.

   **OpenAI** (when `LLM_PROVIDER = "openai"`):

   ```toml
   OPENAI_API_KEY = "sk-..."
   ```

3. **Save** and **Reboot** the app if the UI offers it, so the new env vars load.

### 5. First use of the live URL

1. Open the public URL.
2. Sidebar → **Rebuild index** (required on a fresh machine; `data/index/` is empty until you build). With only **`samples/`** checked in, indexing is small and fast.
3. Ask a question; expand **Retrieved chunks** to verify grounding.

### 6. Caveats (all hosts)

- **Ephemeral disk:** anything under `data/` (index, uploads, json cache) may **reset** when the app restarts or the machine is recycled. Treat the public app as a **demo**: re-run **Rebuild index** after long idle periods if needed.
- **Cold start:** first request may be slow while **sentence-transformers** / **cross-encoder** load and Hugging Face models download.
- **Memory:** free tiers have limits; if the app is **killed (OOM)**, reduce `RERANK_POOL` / `RETRIEVAL_CANDIDATE_K` in `config.py` on a branch used for cloud, or upgrade the host plan.

---

## Option B — Render (Web Service)

1. Create a **Web Service** → connect the **GitHub** repo.
2. **Runtime:** Python.
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:** `streamlit run app/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
5. Under **Environment**, add `GEMINI_API_KEY` or `OPENAI_API_KEY` (same names as locally).
6. Deploy; Render gives a **`onrender.com`** URL.

Same caveats as above (disk, cold start, memory).

---

## Checklist

| Step | Done? |
|------|--------|
| Repo on GitHub, `.env` not committed | |
| `LLM_PROVIDER` matches the key you set on the host | |
| `SEMANTIC_CACHE_BACKEND` is `"json"` **or** you accept Redis fallback + warning | |
| **Rebuild index** once on the public URL | |
| Optional: `LLM_PROVIDER = "echo"` for UI/retrieval-only demos without a paid key | |

---

## Related reading

- [security-and-secrets.md](security-and-secrets.md) — keys, public exposure.
- [development-setup.md](development-setup.md) — local `.env` and run.
- [results-and-verification.md](results-and-verification.md) — what “working” looks like in the UI.
