import os
from loguru import logger


class Settings:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen2.5:7b")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "512"))
    OCR_MODEL: str = os.getenv("OCR_MODEL", "models")
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8001"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        valid_providers = {"ollama", "cloud", "mock"}
        if cls.LLM_PROVIDER not in valid_providers:
            logger.warning(f"未知的 LLM_PROVIDER: {cls.LLM_PROVIDER}，已回退为 mock")
            cls.LLM_PROVIDER = "mock"
        if cls.LLM_PROVIDER == "ollama" and not cls.LLM_BASE_URL:
            raise ValueError("LLM_PROVIDER=ollama 时必须设置 LLM_BASE_URL")
        logger.info(f"AI 服务配置: provider={cls.LLM_PROVIDER}, model={cls.LLM_MODEL}")


settings = Settings()