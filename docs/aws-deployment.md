# AWS deployment and GitHub publishing

This guide is for **learning**: run the Streamlit app on AWS with a **public URL**, and keep the **source on your personal GitHub** without leaking API keys.

**Broader “cloud + RAG” map (EC2, S3, Lambda, Bedrock, …):** [aws-cloud-rag-learning.md](aws-cloud-rag-learning.md).

## Before you start

1. **This app has no built-in login.** A public URL means anyone who finds it can use your UI and **consume your Gemini/OpenAI quota** (and upload files into the server’s `data/uploads/`). For a personal learning deployment, prefer **IP restriction** (security group), **VPN-only** access, or add auth later (reverse proxy + OAuth is the usual pattern).
2. **Never commit `.env` or API keys.** They are in `.gitignore`. On AWS, set **`GEMINI_API_KEY`** / **`GOOGLE_API_KEY`** or **`OPENAI_API_KEY`** as the service’s environment variables (see below).
3. **Corpus and index:** The Docker image ships with **`samples/`** only unless you change the Dockerfile. After deploy, use **Rebuild index** in the sidebar (works on bundled samples), or mount/sync your corpus (see [Corpus on AWS](#corpus-on-aws)).

---

## Step-by-step deployment (pick one path)

Do **Part A (GitHub)** first for both paths. Then choose **Path A** (least ops) or **Path B** (more AWS primitives).

### Part A — Put the code on GitHub (required)

1. On your PC, open a terminal in the repo root (e.g. `c:\rag-assistant`).
2. If there is no `.git` folder yet: `git init`.
3. `git add .` then `git status` — confirm **`.env` is not listed**.
4. `git branch -M main` then `git commit -m "Initial commit: RAG assistant."` (adjust message if you already have commits).
5. On GitHub, create a **new empty** repository (no README if you are pushing an existing tree).
6. `git remote add origin https://github.com/<YOU>/<REPO>.git` then `git push -u origin main`.

You can use `gh repo create <REPO> --private --source=. --remote=origin --push` instead of steps 5–6 if the GitHub CLI is set up.

### Path A — AWS App Runner (HTTPS URL, managed)

**Goal:** AWS builds your `Dockerfile` from GitHub and gives you a **https://…** URL.

1. In [AWS Console](https://console.aws.amazon.com/) choose region (e.g. `us-east-1`).
2. Open **App Runner** → **Create service**.
3. **Source**: Repository type **Source code repository** → **Connect to GitHub** (install/authorize the AWS connector for GitHub if prompted).
4. Select your **repository** and **branch** (usually `main`).
5. **Deployment settings**:
   - **Configuration file**: *Off* (we use the Dockerfile only).
   - **Build type**: **Dockerfile**.
   - **Dockerfile path**: `Dockerfile` (repo root).
6. **Service settings**:
   - **Port**: leave default if the console suggests one; the image uses the **`PORT`** env var App Runner injects (handled by `docker/entrypoint.sh`).
   - **Environment variables** → add **plain text** (not in git):
     - If `LLM_PROVIDER = "gemini"` in `src/rag_assistant/config.py`: **`GEMINI_API_KEY`** or **`GOOGLE_API_KEY`**.
     - If `LLM_PROVIDER = "openai"`: **`OPENAI_API_KEY`**.
7. **Security**: start with a small instance size for learning; review IAM role (App Runner creates a service role — default is fine to begin).
8. **Create & deploy** — wait until status is **Running** (first build can take **10–20+ minutes** because of model downloads in the image build).
9. Open the **default domain** URL App Runner shows (HTTPS).
10. In the Streamlit sidebar, click **Rebuild index**, wait for completion, then ask a test question.
11. **Costs:** delete the service when done experimenting to avoid ongoing charges.

### Path B — EC2 + Docker (SSH, you open port 8501)

**Goal:** A VM you control; you run Docker by hand (classic cloud exposure).

1. **EC2** → **Launch instance**.
2. **Name** the instance; **AMI**: **Amazon Linux 2023** (or Ubuntu 22.04).
3. **Instance type**: `t3.medium` or larger (embedding + rerank are easier with **2+ GiB RAM**; `t3.small` may swap heavily).
4. **Key pair**: create or choose a `.pem` for SSH.
5. **Network**: allow **public IP** for a simple lab (or place behind ALB later).
6. **Security group** inbound rules:
   - **SSH (22)** from **My IP** (recommended).
   - **Custom TCP 8501** from **My IP** first; only use `0.0.0.0/0` if you accept an **open demo** (see warnings above).
7. **Storage**: **20+ GiB** gp3 (Docker images + HF cache + index).
8. **Launch** → wait until **Instance state** = **Running** → note **Public IPv4 address**.

**On the instance (SSH):**

9. Connect: `ssh -i your-key.pem ec2-user@<PUBLIC_IP>` (Amazon Linux user is `ec2-user`; Ubuntu is `ubuntu`).

10. Install and start Docker (Amazon Linux 2023):

    ```bash
    sudo dnf install -y docker
    sudo systemctl enable --now docker
    sudo usermod -aG docker ec2-user
    ```

    Log out and SSH back in so the `docker` group applies.

11. Install Git and clone your repo (HTTPS or SSH clone URL from GitHub):

    ```bash
    sudo dnf install -y git
    git clone https://github.com/<YOU>/<REPO>.git
    cd <REPO>
    ```

12. Build the image:

    ```bash
    docker build -t rag-assistant:latest .
    ```

    First build may take **15–30+ minutes** (PyTorch/sentence-transformers + model pre-cache in the Dockerfile).

13. Run the container (replace the key name with the one matching `LLM_PROVIDER` in `config.py`):

    ```bash
    docker run -d --name rag --restart unless-stopped \
      -p 8501:8501 \
      -e GEMINI_API_KEY="YOUR_KEY_HERE" \
      rag-assistant:latest
    ```

14. On your laptop, open **`http://<PUBLIC_IP>:8501`** (must match security group source).
15. Sidebar → **Rebuild index** → test chat.
16. **Logs:** `docker logs -f rag` — **Stop:** `docker stop rag && docker rm rag`.

**Optional — HTTPS on EC2:** put **Application Load Balancer + ACM** in front, or install **Caddy/nginx** on the instance (separate tutorial).

### After either path works

- **Corpus:** default image uses **`samples/`** only; for more content see [Corpus on AWS](#corpus-on-aws) and [aws-cloud-rag-learning.md](aws-cloud-rag-learning.md) (S3 sync, volumes).
- **Secrets:** for EC2 beyond a lab, prefer **IAM role + S3** or **Secrets Manager** instead of pasting keys in the shell history.

---

## Appendix — Git commands and local Docker

Use the **Part A** numbered steps above as the main GitHub guide. Copy-paste (PowerShell on your PC):

```powershell
git init
git add .
git status   # .env must not appear
git branch -M main
git commit -m "Initial commit: RAG assistant pipeline and docs."
git remote add origin https://github.com/<YOUR_USER>/<YOUR_REPO>.git
git push -u origin main
```

**GitHub CLI** alternative: `gh repo create <YOUR_REPO> --private --source=. --remote=origin --push` (use `--public` if you want).

**Local Docker** (optional sanity check before cloud):

```powershell
docker build -t rag-assistant:local .
docker run --rm -p 8501:8501 -e GEMINI_API_KEY="your-key" rag-assistant:local
```

Open `http://localhost:8501`. Match **`LLM_PROVIDER`** in `src/rag_assistant/config.py` to the key you pass.

| File | Role |
|------|------|
| `Dockerfile` | Python 3.11, deps, pre-download embedding + rerank models |
| `docker/entrypoint.sh` | Creates `data/*`; uses **`PORT`** (App Runner) or **8501** |
| `.streamlit/config.toml` | Headless defaults |

---

## ECS/Fargate (next level)

Build the image, push to **Amazon ECR**, run a **Fargate** service with the same environment variables as App Runner, place an **Application Load Balancer** in front for HTTPS and health checks. Use this after you are comfortable with **Path B** (Docker on a VM).

---

## Corpus on AWS

- **Smallest path:** ship **`samples/`** only (already in the image); use **Rebuild index** after deploy.
- **Full D2L book:** either bake chapters into the image (large, slower builds), or **clone at startup** (custom entrypoint), or **mount S3/EFS** and point `CORPUS_DIR` (would require a small code/config change to use env-based paths). For learning, **EC2 + EBS** with a one-time `git clone` / `sync_d2l_en.py` on the host, then `docker run -v /data/corpus:/app/data/corpus`, is straightforward.

---

## Semantic cache on AWS

Default in `config.py` is **`SEMANTIC_CACHE_BACKEND = "json"`** (file under `data/cache/`). On Fargate/App Runner **without a volume**, the cache resets when the task restarts. For durable cache, use **EFS** mount on `/app/data/cache` or switch to **Redis** (`ElastiCache`) and set `SEMANTIC_CACHE_BACKEND` / `REDIS_URL` in `config.py` plus the matching env on the service.

---

## Related reading

- [security-and-secrets.md](security-and-secrets.md) — keys, logging, data sensitivity.
- [scripts-and-commands.md](scripts-and-commands.md) — local runbook.
- [development-setup.md](development-setup.md) — venv and first-time install.
