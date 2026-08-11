# Project Memory — LG-management-project

## Network / build constraints (KEY — learned 2026-08-11)
This dev environment (CN network) blocks/throttles many package sources. Docker builds fail unless mirrors are configured.

**Working mirrors (bake into Dockerfiles / compose):**
- PyPI: `https://mirrors.aliyun.com/pypi/simple` — FULL mirror, serves wheels itself. PREFERRED.
  - Do NOT use Tuna PyPI (`pypi.tuna.tsinghua.edu.cn`): it is *lazy* and 302-redirects uncached packages to the blocked `files.pythonhosted.org` → ReadTimeout. (Tuna Debian apt mirror IS fine.)
- Debian apt: `https://mirrors.tuna.tsinghua.edu.cn/debian` works.
- npm: `https://registry.npmmirror.com` works.
- PyTorch CPU wheels: `https://download.pytorch.org/whl/cpu` is reachable directly (4+ MB/s).

**Broken / blocked:**
- `hf-mirror.com` (HuggingFace mirror) — SSL EOF / read timeouts. Do NOT rely on it.
- Docker Hub base image pull needs a registry mirror or the daemon must reach `auth.docker.io` (set Docker Desktop → Settings → Docker Engine → registry-mirrors, e.g. `https://docker.m.daocloud.io`).
- Host has a proxy at `127.0.0.1:7890` but it does NOT forward PyPI/Docker Hub; and containers can't reach the host loopback anyway.

## ai-service embedding model
- **2026-08-11 (decision): torch/sentence-transformers/modelscope REMOVED from requirements by default.** The heavy deps + runtime model download caused endless startup/runtime failures on the CN network. ai-service now starts WITHOUT embeddings: `/v1/chat` and `/v1/qa` work; `/v1/embed` returns 503 ("向量化服务未启用"). To re-enable, uncomment the torch/sentence-transformers/modelscope lines in `ai_service/requirements.txt` and rebuild.
- EmbeddingService is lazy + degrades gracefully (no crash on missing deps). `disabled` property signals availability.
- NOTE: `/v1/qa` does NOT use embeddings — it answers from `context_chunks` passed in. Only `/v1/embed` (vectorizing docs) needs the model.
- If/when re-enabling: transformers>=4.57 requires torch>=2.6 (use `torch==2.6.0+cpu`); ModelScope CDN works (HF mirror `hf-mirror.com` is broken/SSL EOF). ModelScope `snapshot_download()` takes `local_dir=`, NOT `local_dir_use_symlinks`.

## Build notes
- Base image pinned to `python:3.12-slim-bookworm` (the `python:3.12-slim` tag now tracks trixie, whose apt index 404s).
- ai-service image is now LIGHT (no torch) → fast, reliable build. Embeddings are opt-in.

## Start stack
- Only the `lg-management-project` compose project should run. Another project `lg-management-backend` (containers `lgm-*`) existed and was removed.
- Run: `docker compose up -d postgres redis minio backend frontend ai-service` (skip celery unless needed).
- Endpoints: frontend :3000, backend :8000, ai-service :8001.
