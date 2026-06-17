# Results and verification

Use this page to confirm the app behaves as expected after setup and to interpret what you see in the UI.

---

## After a successful setup

| Step | Expected result |
|------|-------------------|
| `pip install -r requirements.txt` | Completes without error (same venv you use for Streamlit). |
| `streamlit run app/streamlit_app.py` | Browser opens (often `http://localhost:8501`); sidebar shows paths and config summary. |
| **Rebuild index** (documents present) | Success message with chunk count; sidebar shows index metadata (`built_at`, `num_chunks`). |
| Chat question | Assistant message with an answer; **Retrieved chunks** expander lists sources, scores, and snippet text. |
| Second very similar question (semantic cache on) | Caption **Semantic cache hit**; answer returns without new retrieval/LLM work (same cached chunks shown). |

---

## Interpreting retrieval scores

- **FAISS / fused scores** are **inner-product** style on **L2-normalized** vectors (cosine-like); higher is more similar for dense components.
- After **cross-encoder rerank**, scores are model-specific relevance scores (higher = better match to the question).

---

## When using optional features

| Feature | What you should see |
|---------|---------------------|
| `LLM_PROVIDER=echo` | Answers are placeholder / echo text; useful to validate **retrieval** and UI without Gemini. |
| `HYDE` | Always used before dense retrieval (after a cache miss); tune `HYDE_MAX_CHARS` in `config.py`. Extra LLM + embed latency on misses. |
| `METADATA_FILTER_CHAPTERS=...` | Fewer or no chunks if tokens do not match any chunk; widen filters or rebuild index. |
| `SEMANTIC_CACHE_BACKEND=redis` | Cache hits/misses behave like JSON backend; keys under Redis prefix `rag:sc:v1` (configurable). |

---

## Smoke test (optional)

With venv active and `src` on the path (Streamlit does this automatically):

```powershell
python -c "import sys; sys.path.insert(0,'src'); from rag_assistant.pipeline.query import answer_question; print('import ok')"
```

If this fails with missing modules, fix the environment first ([troubleshooting.md](troubleshooting.md)).

---

## Related reading

- [pipeline-overview.md](pipeline-overview.md) — Pipeline flowcharts.
- [d2l-sample-questions.md](d2l-sample-questions.md) — Example questions and paraphrase pairs to test cache hits.
- [semantic-caching.md](semantic-caching.md) — `SEMANTIC_CACHE_SIMILARITY_THRESHOLD` and invalidation.
- [scripts-and-commands.md](scripts-and-commands.md) — Commands and debug checklist.
- [development-setup.md](development-setup.md) — Install and first-time flow.
