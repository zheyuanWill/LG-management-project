from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://lgadmin:lgdev2026@localhost:5432/lg_erp"
    REDIS_URL: str = "redis://localhost:6379/0"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin2026"
    MINIO_BUCKET: str = "lg-erp"
    AI_SERVICE_URL: str = "http://localhost:8001"
    JWT_SECRET_KEY: str = "lg-jwt-secret-2026-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24

    model_config = {"env_file": ".env", "extra": "allow"}


settings = Settings()