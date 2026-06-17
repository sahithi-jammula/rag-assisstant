"""Streamlit UI for the Phase 1 RAG assistant (D2L / study corpus)."""

from __future__ import annotations

import logging
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dotenv import load_dotenv  # noqa: E402

# Load `.env` for API keys only (GEMINI_*, OPENAI_*). All other settings live in config.py.
load_dotenv(ROOT / ".env", override=True)

# TLS before Streamlit / huggingface_hub / Gemini gRPC
from rag_assistant.embeddings.ssl_utils import configure_tls_for_hf_downloads  # noqa: E402

configure_tls_for_hf_downloads()

import streamlit as st  # noqa: E402

logging.basicConfig(level=logging.INFO)

from rag_assistant.config import (  # noqa: E402
    CACHE_DIR,
    CORPUS_DIR,
    EMBEDDING_MODEL_NAME,
    GEMINI_MODEL,
    GEMINI_TRANSPORT,
    HYDE_MAX_CHARS,
    INDEX_DIR,
    LLM_PROVIDER,
    METADATA_FILTER_CHAPTERS,
    OPENAI_MODEL,
    PROMPT_TEMPLATE_VERSION,
    REDIS_URL,
    RERANK_MODEL_NAME,
    RETRIEVAL_CANDIDATE_K,
    RERANK_POOL,
    SEMANTIC_CACHE_BACKEND,
    SEMANTIC_CACHE_SIMILARITY_THRESHOLD,
    TOP_K,
    UPLOADS_DIR,
)
from rag_assistant.embeddings.service import Embedder  # noqa: E402
from rag_assistant.llm import get_api_key, remote_llm_api_key_required  # noqa: E402
from rag_assistant.pipeline.indexing import build_persisted_index  # noqa: E402
from rag_assistant.pipeline.query import answer_question  # noqa: E402
from rag_assistant.vectorstore.faiss_store import FaissVectorStore, load_index_info  # noqa: E402

st.set_page_config(page_title="RAG Assistant — Deep Learning", layout="wide")


def cache_retrieval_caption(msg: dict) -> str:
    """One-line telemetry: L1 exact vs L2 semantic cache vs miss, plus FAISS retrieval time."""
    status = msg.get("cache_status")
    if status is None and msg.get("cache_hit"):
        status = "semantic"
    if status is None:
        status = "miss"
    if status == "exact":
        label = "cache: exact (L1)"
    elif status == "semantic":
        label = "cache: semantic (L2)"
    else:
        label = "cache: miss"
    r = float(msg.get("retrieval_seconds", 0.0))
    return f"{label} · retrieval: {r:.1f}s"


@st.cache_resource(show_spinner="Loading embedding model…")
def get_embedder() -> Embedder:
    embedder = Embedder(EMBEDDING_MODEL_NAME)
    embedder.load()
    return embedder


def ensure_dirs() -> None:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def save_uploads(files: list) -> int:
    count = 0
    for f in files:
        safe = "".join(c for c in f.name if c.isalnum() or c in "._- ")[:120] or "upload.bin"
        name = f"{uuid.uuid4().hex[:8]}_{safe}"
        dest = UPLOADS_DIR / name
        dest.write_bytes(f.getvalue())
        count += 1
    return count


def try_load_store() -> FaissVectorStore | None:
    try:
        return FaissVectorStore.load(INDEX_DIR)
    except FileNotFoundError:
        return None
    except Exception as exc:  # noqa: BLE001 — show in UI without crashing cold start
        logging.exception("Failed to load vector store: %s", exc)
        return None


def main() -> None:
    ensure_dirs()
    key_ok = bool(get_api_key()) if remote_llm_api_key_required() else True

    st.title("RAG Assistant — Deep Learning (Phase 1)")
    st.caption(
        "Retrieval-augmented answers from your corpus (bundled notes + optional **d2l-en** clone) "
        "and a configurable LLM. Expand **Retrieved chunks** to inspect grounding."
    )

    with st.sidebar:
        st.subheader("Paths and models")
        st.code(
            f"corpus:  {CORPUS_DIR}\n"
            f"uploads: {UPLOADS_DIR}\n"
            f"index:   {INDEX_DIR}",
            language="text",
        )
        st.write("**Embedding model:**", EMBEDDING_MODEL_NAME)
        st.write("**LLM provider:**", LLM_PROVIDER)
        if LLM_PROVIDER == "gemini":
            st.write("**Gemini model:**", GEMINI_MODEL)
            st.write("**Gemini transport:**", GEMINI_TRANSPORT)
        elif LLM_PROVIDER == "openai":
            st.write("**OpenAI model:**", OPENAI_MODEL)
        st.write("**Prompt template version:**", PROMPT_TEMPLATE_VERSION)
        st.write("**Top-k (final context):**", TOP_K)
        st.write("**Retrieval:** hybrid BM25 + dense (RRF) → cross-encoder rerank (always on)")
        st.write("**Dense candidate pool:**", RETRIEVAL_CANDIDATE_K, "| **Rerank pool:**", RERANK_POOL)
        st.write("**Rerank model:**", RERANK_MODEL_NAME)
        st.write("**Semantic cache backend:**", SEMANTIC_CACHE_BACKEND)
        st.write("**Semantic cache similarity threshold:**", SEMANTIC_CACHE_SIMILARITY_THRESHOLD)
        if SEMANTIC_CACHE_BACKEND == "redis":
            redis_hint = REDIS_URL.split("@", 1)[-1] if "@" in REDIS_URL else REDIS_URL
            st.caption(f"Redis target: `{redis_hint}` (edit `REDIS_URL` in `config.py`; run `docker compose up -d` if using Redis)")
        st.write("**HyDE max chars:**", HYDE_MAX_CHARS)
        st.write(
            "**Chapter metadata filter:**",
            ", ".join(METADATA_FILTER_CHAPTERS) if METADATA_FILTER_CHAPTERS else "(none — all chunks)",
        )
        st.caption("Edit `src/rag_assistant/config.py` for all settings above. Put only API keys in `.env` (`GEMINI_API_KEY` / `GOOGLE_API_KEY` or `OPENAI_API_KEY`).")
        if remote_llm_api_key_required():
            if LLM_PROVIDER == "gemini":
                st.write("**Gemini API key:**", "set" if key_ok else "missing (`GEMINI_API_KEY` or `GOOGLE_API_KEY`)")
            elif LLM_PROVIDER == "openai":
                st.write("**OpenAI API key:**", "set" if key_ok else "missing (`OPENAI_API_KEY`)")
        else:
            st.write("**API key:**", "not required (`LLM_PROVIDER=echo`)")

        info = load_index_info(INDEX_DIR)
        if info:
            st.success(
                f"Index metadata present: **{info.get('num_chunks', '?')}** chunks, "
                f"built **{info.get('built_at', '?')}** (UTC)."
            )
        else:
            st.warning("No `index_info.json` yet — run **Rebuild index**.")

        uploads = st.file_uploader(
            "Upload PDF / Markdown / text",
            type=["pdf", "md", "txt", "markdown"],
            accept_multiple_files=True,
        )
        if uploads and st.button("Save uploads to data/uploads"):
            n = save_uploads(uploads)
            st.success(f"Saved **{n}** file(s). Rebuild the index to embed them.")

        if st.button("Rebuild index", type="primary"):
            with st.spinner("Indexing corpus (first run may download the embedding model)…"):
                result = build_persisted_index(get_embedder())
            for m in result.messages:
                (st.success if result.ok else st.error)(m)
            if result.ok:
                st.session_state["vector_store"] = try_load_store()
            st.rerun()

    if "vector_store" not in st.session_state:
        st.session_state["vector_store"] = try_load_store()

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    store: FaissVectorStore | None = st.session_state["vector_store"]

    if store is None:
        st.info(
            "No index loaded. Add `data/corpus/d2l-en/` via `python scripts/sync_d2l_en.py`, "
            "or add files under `data/corpus/` / **Save uploads**, then **Rebuild index**."
        )
    else:
        st.success(f"FAISS index ready — **{int(store.index.ntotal)}** vectors.")

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.caption(cache_retrieval_caption(msg))
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("hits") is not None:
                with st.expander("Retrieved chunks (transparent grounding)"):
                    for h in msg["hits"]:
                        st.markdown(
                            f"**{h['source']}** — score `{float(h['score']):.4f}` — "
                            f"chunk index `{h['chunk_index']}`"
                        )
                        body = h["text"]
                        if len(body) > 4000:
                            body = body[:4000] + "…"
                        st.code(body, language="markdown")

    if prompt := st.chat_input("Ask a deep learning / D2L question…"):
        if store is None:
            st.error("Build an index first (sidebar).")
            return
        if remote_llm_api_key_required() and not key_ok:
            st.error(
                "Set the API key for your LLM provider in `.env`: "
                "`GEMINI_API_KEY` or `GOOGLE_API_KEY` for Gemini, or `OPENAI_API_KEY` for OpenAI "
                "(see `src/rag_assistant/config.py` → `LLM_PROVIDER`)."
            )
            return

        st.session_state["messages"].append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Checking semantic cache, then retrieving…"):
                out = answer_question(prompt, get_embedder(), store, TOP_K)
            st.caption(cache_retrieval_caption(out))
            st.markdown(out["answer"])
            with st.expander("Retrieved chunks (transparent grounding)"):
                for h in out["hits"]:
                    st.markdown(
                        f"**{h['source']}** — score `{float(h['score']):.4f}` — "
                        f"chunk index `{h['chunk_index']}`"
                    )
                    body = h["text"]
                    if len(body) > 4000:
                        body = body[:4000] + "…"
                    st.code(body, language="markdown")

        st.session_state["messages"].append(
            {
                "role": "assistant",
                "content": out["answer"],
                "hits": out["hits"],
                "cache_hit": out.get("cache_hit", False),
                "cache_status": out.get("cache_status", "miss"),
                "retrieval_seconds": float(out.get("retrieval_seconds", 0.0)),
            }
        )


if __name__ == "__main__":
    main()
