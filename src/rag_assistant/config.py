"""Central configuration: edit constants in this file.

Only **API keys** are read from the environment (typically via a root ``.env`` loaded by
``streamlit_app.py``):

- ``GEMINI_API_KEY`` or ``GOOGLE_API_KEY`` when ``LLM_PROVIDER = "gemini"``
- ``OPENAI_API_KEY`` when ``LLM_PROVIDER = "openai"``

Everything else (model **names**, retrieval, cache, HyDE, chapter filters) lives here — no YAML.
"""

from __future__ import annotations

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = _PROJECT_ROOT

DATA_DIR = _PROJECT_ROOT / "data"
CORPUS_DIR = DATA_DIR / "corpus"
UPLOADS_DIR = DATA_DIR / "uploads"
INDEX_DIR = DATA_DIR / "index"
SAMPLES_DIR = _PROJECT_ROOT / "samples"

FAISS_INDEX_FILENAME = "index.faiss"
METADATA_FILENAME = "metadata.json"
INDEX_INFO_FILENAME = "index_info.json"

# --- Models ---
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Google Gemini model id for generateContent when LLM_PROVIDER = "gemini" (see https://ai.google.dev/gemini-api/docs/models)
GEMINI_MODEL = "gemini-2.5-flash"

# Gemini client transport: "rest" (HTTPS, best on Windows) or "grpc" / "grpc_asyncio"
GEMINI_TRANSPORT = "rest"

# "gemini" | "openai" | "echo" — API keys only in .env / environment (see module docstring)
LLM_PROVIDER = "gemini"

# OpenAI Chat Completions model id (edit here; see docs/openai-llm.md)
OPENAI_MODEL = "gpt-4o-mini"

# --- Chunking & retrieval ---
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5

RETRIEVAL_CANDIDATE_K = 48
RERANK_POOL = 32
RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
RRF_K = 60

# --- HyDE (always used for dense vector before retrieval) ---
HYDE_MAX_CHARS = 320

# --- Chapter metadata filter (empty list = all chunks) ---
METADATA_FILTER_CHAPTERS: list[str] = []

# --- Semantic cache (always on; pick backend below) ---
CACHE_DIR = DATA_DIR / "cache"
SEMANTIC_CACHE_PATH = CACHE_DIR / "semantic_cache.json"
SEMANTIC_CACHE_MAX_ENTRIES = 200
SEMANTIC_CACHE_SIMILARITY_THRESHOLD = 0.75
SEMANTIC_CACHE_BACKEND = "redis"  # "json" (file under data/cache/) or "redis" (set REDIS_URL; run Docker)
REDIS_URL = "redis://127.0.0.1:6379/0"
REDIS_SEMANTIC_CACHE_KEY_PREFIX = "rag:sc:v1"


def get_gemini_api_key() -> str | None:
    """Google Gemini / Google AI API key from environment / .env only."""
    key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    return key or None


def get_openai_api_key() -> str | None:
    """OpenAI API key from environment / .env only."""
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    return key or None


def retrieval_profile_fingerprint() -> str:
    """Stable string for cache invalidation when retrieval-related settings change."""
    import hashlib

    mf_key = ",".join(sorted(METADATA_FILTER_CHAPTERS))
    parts = (
        str(RETRIEVAL_CANDIDATE_K),
        str(RERANK_POOL),
        str(TOP_K),
        str(RRF_K),
        RERANK_MODEL_NAME,
        str(HYDE_MAX_CHARS),
        mf_key,
        EMBEDDING_MODEL_NAME,
    )
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


PROMPT_TEMPLATE_VERSION = "1.0"

TEXT_EXTENSIONS = {".md", ".txt", ".markdown"}
PDF_EXTENSIONS = {".pdf"}
