import os
from typing import List

from loguru import logger

from config import settings

# fastembed 提供 ONNX 版 Embedding：无需 torch / sentence-transformers，
# 体积小、CPU 推理快。模型在首次 /v1/embed 调用时按需下载并缓存到 /cache/models。
# 启动阶段不触碰模型，因此 AI 服务始终可以快速启动。
_CACHE_DIR = "/cache/models"


class EmbeddingService:
    _instance = None
    _model = None
    _disabled = False
    _dim = 512

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 构造时不做任何模型加载，避免启动崩溃
        self._model = None
        self._disabled = False

    def _ensure_loaded(self):
        """首次调用时再加载模型；失败则标记为禁用并抛出清晰异常。"""
        if self._model is not None:
            return
        if self._disabled:
            raise RuntimeError("embedding 服务未启用（fastembed 未安装或模型不可用）")

        try:
            from fastembed import TextEmbedding
        except ImportError:
            self._disabled = True
            raise RuntimeError(
                "embedding 依赖未安装（fastembed）。"
                "请在 ai_service 的 requirements.txt 中安装 fastembed 后启用。"
            )

        model_name = settings.EMBEDDING_MODEL
        logger.info(f"加载 Embedding 模型 (fastembed): {model_name}")
        try:
            local_path = self._resolve_model_path(model_name)
            self._model = TextEmbedding(
                model_name=local_path,
                cache_dir=_CACHE_DIR,
                threads=0,
            )
            # 探测实际维度（fastembed 默认做 L2 归一化）
            probe = next(self._model.embed(["探测维度"], batch_size=1, parallel=0))
            self._dim = int(probe.shape[0])
            logger.info(f"Embedding 模型加载完成，维度: {self._dim}")
        except Exception as e:
            self._disabled = True
            logger.error(f"Embedding 模型加载失败，/v1/embed 将返回 503: {e}")
            raise RuntimeError(f"embedding 模型加载失败: {e}") from e

    def _resolve_model_path(self, model_name: str) -> str:
        """若传入的是本地目录则直接使用，否则作为 HF repo id 交给 fastembed 下载/缓存。"""
        if os.path.isdir(model_name):
            return model_name
        return model_name

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self._dim
        self._ensure_loaded()
        vec = next(self._model.embed([text], batch_size=1, parallel=0))
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        # fastembed 对空串不友好，统一用空格占位（向量接近零向量，不影响召回）
        valid_texts = [(t if t and t.strip() else " ") for t in texts]
        self._ensure_loaded()
        embeddings = list(self._model.embed(valid_texts, batch_size=32, parallel=0))
        return [emb.tolist() for emb in embeddings]

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def disabled(self) -> bool:
        return self._disabled
