#!/usr/bin/env python
"""预下载 Embedding 模型到 /cache/models（fastembed 可直接复用）。

为什么需要它：
  fastembed 在首次 /v1/embed 时会自动按 HF_ENDPOINT 下载模型并缓存。
  本脚本只是把"下载"这一步单独拎出来，方便在国内网络环境下提前拉取、
  排查下载问题，或切换镜像源。下载到的目录结构与 fastembed 期望的完全一致。

用法：
  # 在宿主机（镜像已配好）：
  docker compose exec ai-service python provision_model.py
  # 或指定其它镜像源：
  HF_ENDPOINT=https://hf-mirror.com docker compose exec ai-service python provision_model.py

可选：用 ModelScope 下载（国内更稳），再交给 fastembed 加载：
  USE_MODELSCOPE=1 docker compose exec ai-service python provision_model.py
"""
import os

MODEL_ID = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
CACHE_DIR = os.getenv("HF_HUB_CACHE", "/cache/models")
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
USE_MODELSCOPE = os.getenv("USE_MODELSCOPE", "0").lower() in ("1", "true", "yes")


def download_via_huggingface():
    """通过 huggingface_hub 下载，产物即 fastembed 原生布局。"""
    from huggingface_hub import snapshot_download

    # 让 huggingface_hub 走镜像源
    os.environ.setdefault("HF_ENDPOINT", HF_ENDPOINT)
    local_dir = os.path.join(CACHE_DIR, MODEL_ID.replace("/", "--"))
    print(f"[huggingface] 下载 {MODEL_ID} -> {local_dir} (HF_ENDPOINT={HF_ENDPOINT})")
    path = snapshot_download(
        repo_id=MODEL_ID,
        local_dir=local_dir,
        local_dir_use_symlinks=False,
    )
    print(f"[huggingface] 完成: {path}")
    return path


def download_via_modelscope():
    """国内更稳的备选：用 modelscope 拉取后，整理成 fastembed 需要的布局。"""
    from modelscope import snapshot_download as ms_download

    print(f"[modelscope] 下载 {MODEL_ID} 到 {CACHE_DIR}")
    ms_path = ms_download(MODEL_ID, cache_dir=CACHE_DIR)
    print(f"[modelscope] 完成: {ms_path}")
    print("[modelscope] 注意：fastembed 默认读取 HF 布局；")
    print("  若 fastembed 启动时找不到模型，请将 onnx/model.onnx 复制到根目录并保留")
    print("  config.json / tokenizer.json / tokenizer_config.json / special_tokens_map.json。")
    return ms_path


if __name__ == "__main__":
    if USE_MODELSCOPE:
        download_via_modelscope()
    else:
        download_via_huggingface()
    print("模型预下载结束。可直接启动服务或使用 /v1/embed。")
