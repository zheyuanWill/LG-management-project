import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

from config import settings


class EmbeddingService:
    _instance: "EmbeddingService | None" = None
    _model: SentenceTransformer | None = None

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is not None:
            return
        logger.info(f"加载 Embedding 模型: {settings.EMBEDDING_MODEL}")
        self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info(f"Embedding 模型加载完成，维度: {settings.EMBEDDING_DIM}")

    def embed_text(self, text: str) -> list[float]:
        if not text or not text.strip():
            return [0.0] * settings.EMBEDDING_DIM
        embedding = self._model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        valid_texts = [t if t and t.strip() else "" for t in texts]
        embeddings = self._model.encode(valid_texts, normalize_embeddings=True, show_progress_bar=False)
        if isinstance(embeddings, np.ndarray):
            return embeddings.tolist()
        return [emb.tolist() for emb in embeddings]

    @property
    def dim(self) -> int:
        return settings.EMBEDDING_DIM