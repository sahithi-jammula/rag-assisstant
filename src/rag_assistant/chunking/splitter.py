"""Text splitting using langchain-text-splitters (no full LangChain chain)."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag_assistant.config import CHUNK_OVERLAP, CHUNK_SIZE
from rag_assistant.loaders.corpus_loader import RawDocument


@dataclass(frozen=True)
class TextChunk:
    """One chunk ready for embedding."""

    text: str
    source: str
    chunk_index: int


def split_raw_documents(
    documents: list[RawDocument],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[TextChunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    chunks: list[TextChunk] = []
    for doc in documents:
        parts = splitter.split_text(doc.text)
        idx = 0
        for part in parts:
            text = part.strip()
            if not text:
                continue
            chunks.append(TextChunk(text=text, source=doc.source, chunk_index=idx))
            idx += 1
    return chunks
