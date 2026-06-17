# RAG Assistant — container image (AWS App Runner, ECS/Fargate, EC2 + Docker, local smoke test)
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

# git: optional runtime clone of corpus (not required). build-essential sometimes needed for wheels — try without first.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download embedding + rerank models (faster cold start; larger image).
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
    SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); \
    CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

COPY src/ ./src/
COPY app/ ./app/
COPY samples/ ./samples/
COPY .streamlit/ ./.streamlit/
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Keys: inject at runtime (App Runner / ECS / EC2 env). Do not bake .env into the image.
EXPOSE 8501
ENTRYPOINT ["/entrypoint.sh"]
