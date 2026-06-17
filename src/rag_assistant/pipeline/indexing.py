"""Build or reload the persisted FAISS index from on-disk documents."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from rag_assistant.chunking.splitter import split_raw_documents
from rag_assistant.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    INDEX_DIR,
    PROMPT_TEMPLATE_VERSION,
)
from rag_assistant.embeddings.service import Embedder
from rag_assistant.loaders.corpus_loader import load_all_documents
from rag_assistant.retrieval.chunk_metadata import infer_chunk_metadata
from rag_assistant.vectorstore.faiss_store import FaissVectorStore, clear_index_dir

logger = logging.getLogger(__name__)


@dataclass
class IndexBuildResult:
    ok: bool
    num_documents: int
    num_chunks: int
    index_dir: str
    messages: list[str] = field(default_factory=list)


def build_persisted_index(embedder: Embedder) -> IndexBuildResult:
    """
    Full rebuild: read corpus/uploads/samples, chunk, embed, persist under INDEX_DIR.
    """
    docs, manifest = load_all_documents()
    if not docs:
        return IndexBuildResult(
            ok=False,
            num_documents=0,
            num_chunks=0,
            index_dir=str(INDEX_DIR),
            messages=[
                "No documents found. Add files to data/corpus/ or upload via the sidebar, "
                "and ensure samples/ exists if you rely on bundled examples."
            ],
        )

    text_chunks = split_raw_documents(docs)
    if not text_chunks:
        return IndexBuildResult(
            ok=False,
            num_documents=len(docs),
            num_chunks=0,
            index_dir=str(INDEX_DIR),
            messages=["Documents loaded but produced zero chunks after splitting."],
        )

    chunk_dicts = [
        {
            "text": c.text,
            "source": c.source,
            "chunk_index": c.chunk_index,
            "metadata": infer_chunk_metadata(c.source),
        }
        for c in text_chunks
    ]
    texts = [c["text"] for c in chunk_dicts]

    embedder.load()
    vectors = embedder.encode(texts)
    store = FaissVectorStore.build(vectors, chunk_dicts)

    clear_index_dir(INDEX_DIR)
    index_info = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "embedding_model": embedder.model_name,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "sources": manifest,
        "num_chunks": len(chunk_dicts),
        "prompt_template_version": PROMPT_TEMPLATE_VERSION,
    }
    store.save(INDEX_DIR, index_info)
    logger.info("Index build complete: %s chunks from %s documents", len(chunk_dicts), len(docs))

    return IndexBuildResult(
        ok=True,
        num_documents=len(docs),
        num_chunks=len(chunk_dicts),
        index_dir=str(INDEX_DIR),
        messages=[f"Indexed {len(chunk_dicts)} chunks from {len(docs)} document(s)."],
    )
