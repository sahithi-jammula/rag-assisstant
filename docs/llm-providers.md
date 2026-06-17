# Swappable LLM layer

Retrieval and prompting stay explicit; **generation** goes through a small interface so you can swap backends without rewriting the RAG pipeline.

## Interface

- **Abstract type:** `rag_assistant.llm.base.LLMClient` — `provider_id` and `generate(prompt: str) -> str`.
- **Factory:** `rag_assistant.llm.factory.build_llm_client()` — uses **`LLM_PROVIDER`** from **`src/rag_assistant/config.py`**.
- **Query path:** `rag_assistant.pipeline.query.answer_question(..., llm=None)` — when `llm` is omitted, the factory builds the default client.

## Built-in providers

Set **`LLM_PROVIDER`** in **`config.py`** to one of:

| `LLM_PROVIDER` | Class | API key in `.env` | Model / options in `config.py` |
|----------------|-------|-------------------|--------------------------------|
| `"gemini"` | `GeminiLLM` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | `GEMINI_MODEL`, `GEMINI_TRANSPORT` |
| `"openai"` | `OpenAILLM` | `OPENAI_API_KEY` | `OPENAI_MODEL` — see [OpenAI](#openai) |
| `"echo"` | `EchoLLM` | *(none)* | Stub text only |

Any other `LLM_PROVIDER` value raises **`ValueError`** from the factory.

**Streamlit note:** after you change `config.py`, **restart the Streamlit process** so Python reloads `rag_assistant.config`.

## OpenAI

Use when **`LLM_PROVIDER = "openai"`** in **`src/rag_assistant/config.py`**.

### Keys and model name

| What | Where |
|------|-------|
| **API key** | **`OPENAI_API_KEY`** in a root **`.env`** file (or your process environment). Never commit the key. |
| **Model id** | **`OPENAI_MODEL`** in **`config.py`** (e.g. `gpt-4o-mini`). |

The app calls the **Chat Completions** API with a single **user** message containing the full RAG prompt (same shape as for Gemini).

### Choosing a model version

OpenAI’s catalog changes over time; always check the official list: **[Models](https://platform.openai.com/docs/models)**.

Practical defaults for **RAG / tutoring** (good quality, reasonable cost):

| Model id (examples) | Notes |
|---------------------|--------|
| **`gpt-4o-mini`** | **Default in this repo.** Strong default for Q&A over retrieved text; usually cheaper than full `gpt-4o`. |
| **`gpt-4o`** | Higher capability / cost when answers need more nuance. |
| **`gpt-4-turbo`** | Older “4” family; still valid if your account supports it. |

Reasoning-focused ids (e.g. **`o3-mini`**, **`o1`**) may behave differently or need different parameters; start with **`gpt-4o-mini`** unless you know you need a reasoning model.

If the API returns **“model not found”** or **400** for the model string, the id is wrong for your **organization / project** or not enabled in the dashboard—pick an id from the docs link above.

### Switch from Gemini to OpenAI

1. In **`config.py`**: `LLM_PROVIDER = "openai"` and set **`OPENAI_MODEL`** as desired.
2. In **`.env`**: set **`OPENAI_API_KEY=...`** (you can leave `GEMINI_API_KEY` unset).
3. Restart Streamlit so `config` reloads.

## Adding a provider

1. Add a new module under `src/rag_assistant/llm/` implementing `LLMClient`.
2. Register it in `build_llm_client()` and allow the id in `LLM_PROVIDER` in `config.py`.
3. Add the HTTP/SDK dependency to `requirements.txt`.
4. Document any new **API key** env name next to the existing keys in [development-setup.md](development-setup.md) and [security-and-secrets.md](security-and-secrets.md).

## Related reading

- [technology-stack.md](technology-stack.md) — current default stack.
- [architecture.md](architecture.md) — where the LLM sits in the query sequence.
- [development-setup.md](development-setup.md) — `.env` for keys only.
