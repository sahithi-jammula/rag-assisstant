# Security and secrets

This project is a **local learning tool**, but it still touches **API keys** and **potentially sensitive documents**. Treat both with normal hygiene.

## Gemini or OpenAI API key

- **Gemini** (`LLM_PROVIDER = "gemini"` in `config.py`): **`GEMINI_API_KEY`** or **`GOOGLE_API_KEY`** in **`.env`**.
- **OpenAI** (`LLM_PROVIDER = "openai"`): **`OPENAI_API_KEY`** in **`.env`**; model id is **`OPENAI_MODEL`** in `config.py` (see [llm-providers.md](llm-providers.md#openai)).
- **Echo** (`LLM_PROVIDER = "echo"`): no remote key.

### Do not

- Commit `.env`, service account JSON, or API keys into git.
- Paste keys into Streamlit `text_input` in shared screen recordings (use env vars instead).
- Log the full prompt if it might contain secrets from your documents **and** you ship logs externally.

## Data residency and networking

- **Gemini**: prompts leave your machine to Google’s servers. Do not upload proprietary cluster dumps if your employer forbids that.
- **OpenAI**: prompts leave your machine to OpenAI’s servers under their terms of use and retention policies.
- **Embeddings**: with `sentence-transformers`, embedding computation is **local** by default.

## File system considerations

- `data/corpus/` and `data/uploads/` may contain internal runbooks. Keep repo permissions sensible on shared machines.
- The persisted index (`data/index/`) contains **chunk text** duplicated on disk. If raw docs are sensitive, protect the whole `data/` directory.
- **Semantic cache** (`SEMANTIC_CACHE_BACKEND=json` → `data/cache/semantic_cache.json`; `redis` → Redis) stores **past questions** and **answers**. Treat it like sensitive local or infra data (see [semantic-caching.md](semantic-caching.md)).

## Model output

LLMs can **leak training biases** or **confidently guess**. For operations work, always verify against your cluster and change management process—Phase 1 documentation grounding reduces but does not eliminate risk.

## Public deployment (AWS, etc.)

If you expose the Streamlit UI on the internet, treat it like **an open website**: there is **no account login** in this repo, so anyone with the URL can trigger **LLM calls** (cost) and **upload files** to the server. Put keys only in the host’s environment / secrets manager, never in git. See [aws-deployment.md](aws-deployment.md).

## Related reading

- [development-setup.md](development-setup.md) — API key in `.env`; other settings in `config.py`.
- [technology-stack.md](technology-stack.md) — Why Gemini is separated from local retrieval.
