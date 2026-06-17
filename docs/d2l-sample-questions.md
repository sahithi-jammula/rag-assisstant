# Sample questions (Dive into Deep Learning) + semantic-cache pairs

Use these after you have **D2L-style Markdown** in the corpus (e.g. `python scripts/sync_d2l_en.py` → `data/corpus/d2l-en/`, plus **Rebuild index** in Streamlit). Wording follows common *Dive into Deep Learning* topics; answers should ground in whatever chapters you actually indexed.

---

## Where is the semantic-cache similarity threshold?

Edit `**SEMANTIC_CACHE_SIMILARITY_THRESHOLD`** in `**src/rag_assistant/config.py**`. Only **API keys** belong in `**.env`**.

- **Higher** (e.g. `0.95`) → fewer cache hits; only very close paraphrases match.
- **Lower** (e.g. `0.85`) → more hits; risk of reusing an answer when intent drifted slightly.

Cache compares **only the user question embedding** (not the HyDE-augmented vector). See [semantic-caching.md](semantic-caching.md).

---

## Questions to probe retrieval (ask once, read chunks)

Ask in **plain language**; expand **Retrieved chunks** to see if the right `chapter_`* / section grounded the answer.

### Preliminaries / notation

1. What is the difference between **machine learning** and **statistics** for prediction?
2. Explain **supervised learning** vs **unsupervised learning** with one example each.
3. What role does a **loss function** play in training a model?

### Linear regression & optimization

1. How does **linear regression** relate to minimizing mean squared error?
2. What is **gradient descent**, and why do we use a **learning rate**?
3. Explain **stochastic gradient descent (SGD)** vs full-batch gradient descent in one paragraph.

### Softmax & classification

1. What is the **softmax** function, and why is it used for multi-class classification?
2. How does **cross-entropy loss** relate to maximum likelihood for classification?

### Multilayer perceptrons

1. What is a **multilayer perceptron (MLP)**, and why do we need **nonlinear activation** functions between layers?
2. What is the **universal approximation theorem** (informal intuition is enough)?

### Convolutional networks

1. What is a **convolutional layer** trying to exploit in image data?
2. How does **padding** and **stride** change the spatial size of a feature map?

### Sequence models & attention (if indexed)

1. What problem do **RNNs** address that feedforward networks handle poorly?
2. In one or two sentences, what is **attention** trying to compute in a sequence model?

### Practical / “study guide” style

1. Give a **minimal checklist** for debugging when training loss does not decrease.
2. What is **overfitting**, and what are two common ways to reduce it?

---

## Similar question pairs (test semantic caching)

**How to test**

1. Semantic cache is **always on** (tune threshold in `config.py`).
2. Ask **Question A**; wait for a full answer (cache **miss** then **store**).
3. Ask **Question B** (paraphrase of A). If embeddings are close enough vs `SEMANTIC_CACHE_SIMILARITY_THRESHOLD`, you should see a **Semantic cache hit** caption and the same cached chunks.

If B never hits, try a **lower** threshold (e.g. `0.88`) or a tighter paraphrase. If unrelated questions hit, **raise** the threshold.


| #   | Question A (first ask)                          | Question B (paraphrase — ask second)                                      |
| --- | ----------------------------------------------- | ------------------------------------------------------------------------- |
| 1   | What is stochastic gradient descent?            | Can you explain **SGD** and how it differs from batch gradient descent?   |
| 2   | Why do we use softmax for classification?       | Why is **softmax** used at the output of a multi-class classifier?        |
| 3   | What is overfitting in machine learning?        | Explain **overfitting** and how it shows up on train vs validation error. |
| 4   | What is a convolutional neural network good at? | What inductive bias does a **CNN** exploit for images?                    |
| 5   | What is the purpose of a learning rate?         | Why do we need a **step size** when updating weights with gradients?      |
| 6   | What is cross-entropy loss?                     | How does **cross-entropy** penalize wrong class probabilities?            |
| 7   | What are activation functions in deep networks? | Why can’t a deep **MLP** be only linear layers?                           |
| 8   | What is attention in Transformers?              | Give a short intuition for **self-attention** in sequence models.         |


**Negative control (should *not* hit the same cache entry):** after asking about SGD, ask something unrelated like “How do I pickle a pandas DataFrame?” — you should get a **miss** and a new retrieval path.

---

## Optional: restrict to one chapter (metadata filter)

If you set e.g. `METADATA_FILTER_CHAPTERS=chapter_linear-regression`, pair questions should still be **about content in that chapter** or retrieval may return nothing useful. See [advanced-rag.md](advanced-rag.md).

## Related reading

- [semantic-caching.md](semantic-caching.md) — Full cache behavior and invalidation.
- [results-and-verification.md](results-and-verification.md) — What a cache hit looks like in the UI.
- [scripts/README.md](../scripts/README.md) — Syncing the D2L English corpus.

