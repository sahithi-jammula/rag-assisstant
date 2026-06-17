"""End-to-end question answering using retrieval + a configurable LLM."""

from __future__ import annotations

import time

from rag_assistant.cache.semantic_cache import build_semantic_cache_from_config, compute_index_fingerprint
from rag_assistant.config import INDEX_DIR, PROMPT_TEMPLATE_VERSION, TOP_K
from rag_assistant.embeddings.service import Embedder
from rag_assistant.llm.base import LLMClient
from rag_assistant.llm.factory import build_llm_client
from rag_assistant.retrieval.advanced import retrieve_for_query
from rag_assistant.retrieval.hyde import maybe_hyde_dense_vector
from rag_assistant.vectorstore.faiss_store import FaissVectorStore


def build_rag_prompt(question: str, hits: list[dict], prompt_version: str = PROMPT_TEMPLATE_VERSION) -> str:
    blocks: list[str] = []
    for i, h in enumerate(hits, start=1):
        blocks.append(f"### Source {i}: {h['source']}\n{h['text']}")
    context = "\n\n".join(blocks) if blocks else "(no retrieved context)"
    return (
        "You are a careful deep learning tutor helping a learner (Dive into Deep Learning / similar notes).\n"
        "Answer using ONLY the CONTEXT below when it contains enough information.\n"
        "If CONTEXT is missing or insufficient, say so clearly and suggest what material "
        "the user should add to the corpus.\n"
        "Use clear structure (short paragraphs or bullet lists) when helpful.\n\n"
        f"Prompt template version: {prompt_version}\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION:\n{question.strip()}\n"
    )


def answer_question(
    question: str,
    embedder: Embedder,
    store: FaissVectorStore,
    top_k: int = TOP_K,
    llm: LLMClient | None = None,
) -> dict:
    client = llm or build_llm_client()
    model_label = getattr(client, "model_name", client.provider_id)
    index_fp = compute_index_fingerprint(INDEX_DIR)

    cache = build_semantic_cache_from_config()
    retrieval_seconds = 0.0

    if cache.enabled:
        exact = cache.lookup_exact(
            question,
            index_fingerprint=index_fp,
            llm_provider=client.provider_id,
            model_label=model_label,
        )
        if exact is not None:
            return {
                "answer": exact.answer,
                "hits": exact.hits,
                "prompt": exact.prompt,
                "model": model_label,
                "llm_provider": client.provider_id,
                "prompt_template_version": exact.prompt_template_version,
                "cache_hit": True,
                "cache_status": "exact",
                "retrieval_seconds": retrieval_seconds,
            }

    embedder.load()
    q_vectors = embedder.encode([question.strip()])
    qvec = q_vectors[0]

    hit = cache.lookup(
        qvec,
        index_fingerprint=index_fp,
        llm_provider=client.provider_id,
        model_label=model_label,
    )
    if hit is not None:
        return {
            "answer": hit.answer,
            "hits": hit.hits,
            "prompt": hit.prompt,
            "model": model_label,
            "llm_provider": client.provider_id,
            "prompt_template_version": hit.prompt_template_version,
            "cache_hit": True,
            "cache_status": "semantic",
            "retrieval_seconds": retrieval_seconds,
        }

    dense_vec = maybe_hyde_dense_vector(question, qvec, embedder, client)
    t0 = time.perf_counter()
    hits = retrieve_for_query(question, dense_vec, embedder, store, top_k)
    retrieval_seconds = time.perf_counter() - t0
    prompt = build_rag_prompt(question, hits)
    try:
        answer = client.generate(prompt)
    except ValueError as exc:
        answer = f"**Could not call LLM ({client.provider_id}).** {exc}"
    out = {
        "answer": answer,
        "hits": hits,
        "prompt": prompt,
        "model": model_label,
        "llm_provider": client.provider_id,
        "prompt_template_version": PROMPT_TEMPLATE_VERSION,
        "cache_hit": False,
        "cache_status": "miss",
        "retrieval_seconds": retrieval_seconds,
    }
    cache.store(
        question=question,
        query_vector=qvec,
        answer=answer,
        hits=hits,
        prompt=prompt,
        index_fingerprint=index_fp,
        llm_provider=client.provider_id,
        model_label=model_label,
    )
    return out
