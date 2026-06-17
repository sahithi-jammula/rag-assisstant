# AWS + RAG — learning map (EC2, S3, Lambda, and friends)

This repo is a **CPU-heavy, long-running Streamlit app** (local embeddings, FAISS, BM25, cross-encoder, HyDE). You can still get **real exposure** to EC2, S3, Lambda, and other AWS pieces by combining them in a **hybrid** layout: one service rarely does “all of RAG” alone.

---

## What fits naturally with *this* codebase

| AWS service | Role with this project | Why |
|-------------|-------------------------|-----|
| **EC2** (or **ECS/Fargate** + **ECR**) | Run the **Docker image** or venv; host Streamlit on a public or restricted port. | Matches long-lived process, large Python deps, model download/cache, disk for `data/index/`. |
| **S3** | **Corpus source of truth** or backups: `aws s3 sync s3://your-bucket/corpus/ /app/data/corpus/` on boot or cron; optional **versioned backups** of `data/index/` (zip/tar) after rebuild. | Cheap object storage; EC2 EBS is for live working files. |
| **IAM** | Instance role for S3 read/write **without** long-lived access keys on disk. | Core cloud skill; least-privilege policies. |
| **Secrets Manager** or **SSM Parameter Store** | Store `GEMINI_API_KEY` / `OPENAI_API_KEY`; inject at startup or read from a small bootstrap script. | Safer than plain text in user-data. |
| **CloudWatch** | Logs and CPU alarms for the instance or container. | Operational awareness. |
| **ALB + ACM** | HTTPS in front of EC2/ECS (Streamlit on 8501 behind target group). | Public “real” URL with TLS. |

See [aws-deployment.md](aws-deployment.md) for concrete deploy steps (Docker, App Runner, EC2).

---

## Lambda — possible, but not as “drop-in” for this Streamlit app

**Lambda is a poor direct host** for this entire app because:

- **Timeout** (minutes max) vs index build + model cold load.
- **Deployment package / container size** limits vs `sentence-transformers` + FAISS + reranker.
- **Ephemeral disk** — fine for tiny demos, awkward for large FAISS indexes unless rebuilt every invoke (slow/expensive).

**Lambda *is* a good learning target** for *narrow* RAG-shaped work:

- **API Gateway + Lambda** that calls **Amazon Bedrock** (`InvokeModel` / Converse) for **generation only**, while retrieval lives elsewhere (Bedrock Knowledge Bases, OpenSearch, a vector DB).
- A **scheduled** Lambda that **kicks off** work (e.g. post a message to **SQS** for an EC2 worker or Step Functions run) — “event-driven” ingestion.
- A tiny **health or webhook** function unrelated to heavy retrieval.

Treat “**Lambda-only full clone of this repo’s retrieval stack**” as an **advanced refactor**, not the first learning milestone.

---

## Other AWS services worth touching for “cloud + RAG” exposure

| Service | Exposure angle |
|---------|----------------|
| **Amazon Bedrock** | Managed foundation models; pair with **Knowledge Bases** for managed ingest + retrieval (different architecture than FAISS-in-process, but same *RAG idea*). |
| **OpenSearch Serverless** (or managed OpenSearch) | Managed **knn** vector search at scale; compare to local FAISS. |
| **Step Functions** | Orchestrate **ingest** steps: copy S3 → normalize → embed → write index (each step can be Lambda, ECS task, or Batch). |
| **SQS** | Decouple “upload notification” from “heavy indexing” on EC2/Batch. |
| **EventBridge** | Schedule nightly re-index or react to S3 `ObjectCreated`. |
| **AWS Batch** | GPU/CPU **batch jobs** for large embedding jobs (optional if you outgrow one EC2). |

---

## Suggested learning path (minimal scope creep)

1. **EC2 + Docker** — Run this app; restrict security group; use **Secrets Manager** for the LLM key.  
2. **S3 + IAM role** — Put Markdown/PDF under a prefix; **sync to** `/app/data/corpus/` before **Rebuild index** in the UI (or automate with a script + cron).  
3. **CloudWatch** — Ship container/instance logs; set a simple CPU alarm.  
4. **Separate tiny project** — **API Gateway + Lambda + Bedrock** “ask one question” JSON API (no Streamlit), to learn **serverless + managed LLM** without fighting Lambda limits for FAISS.

That path gives you **EC2 + S3 + Lambda exposure** plus optional **Bedrock** without rewriting this repository into serverless-first on day one.

---

## Related reading

- [aws-deployment.md](aws-deployment.md) — GitHub, Docker, App Runner / EC2 / Fargate.
- [security-and-secrets.md](security-and-secrets.md) — Keys and public exposure risks.
- [index-persistence.md](index-persistence.md) — What `data/index/` contains (backup implications on S3).
