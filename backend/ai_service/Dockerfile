# ── AI 推理服务 ──────────────────────────────
FROM python:3.12-slim-bookworm AS ai-service

ARG PIP_INDEX_URL=https://pypi.org/simple
ARG DEBIAN_MIRROR=http://deb.debian.org
ENV PIP_INDEX_URL=$PIP_INDEX_URL PIP_TRUSTED_HOST=mirrors.aliyun.com PIP_DEFAULT_TIMEOUT=120 PIP_RETRIES=10
# Embedding 模型（fastembed / huggingface_hub）与 pip 缓存统一落到持久化卷
ENV HF_HUB_CACHE=/cache/models PIP_CACHE_DIR=/cache/pip

WORKDIR /app

# 系统依赖（Debian 源可切换为国内镜像，避免 deb.debian.org 不稳定）
RUN sed -i "s|http://deb.debian.org/debian|${DEBIAN_MIRROR}/debian|g" /etc/apt/sources.list 2>/dev/null; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i "s|http://deb.debian.org/debian|${DEBIAN_MIRROR}/debian|g" /etc/apt/sources.list.d/debian.sources; \
    fi
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
