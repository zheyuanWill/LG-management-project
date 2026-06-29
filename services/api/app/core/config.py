"""
Application Configuration

Uses pydantic-settings for typed, validated configuration from environment variables.
"""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres123@localhost:5432/lg_management"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET: str = "lg-management"
    MINIO_USE_SSL: bool = False
    
    # CORS — comma-separated string: CORS_ORIGINS="https://a.com,https://b.com"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080,https://admin.fasdasdaasdasdadqwqaczxczzxczxc.xyz"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
    
    # Kingdee Jingdouyun (精斗云)
    KINGDEE_ENABLED: bool = False
    KINGDEE_CLIENT_ID: str = ""
    KINGDEE_CLIENT_SECRET: str = ""
    KINGDEE_APP_KEY: str = ""
    KINGDEE_APP_SECRET: str = ""
    KINGDEE_INSTANCE_ID: str = ""
    KINGDEE_BASE_URL: str = "https://api.kingdee.com"
    KINGDEE_DOMAIN: str = ""
    KINGDEE_SID: str = ""
    KINGDEE_DB_ID: str = ""
    
    # Email / SMTP
    SMTP_ENABLED: bool = False
    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_TLS: bool = True

    # AI Agent
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_EMBEDDING_MODEL: str = "text-embedding-v3"
    # Universal AI Config
    AI_PROVIDER: str = ""  # OPENAI, AZURE_OPENAI, ANTHROPIC, DEEPSEEK, QWEN
    AI_API_KEY: str = ""
    AI_BASE_URL: str = ""
    AI_MODEL: str = ""

    # App
    DEBUG: bool = True
    APP_NAME: str = "LG Management API"
    API_PREFIX: str = "/api"
    
    model_config = {
        "env_file": (".env", ".env.kingdee.sandbox"),
        "case_sensitive": True,
    }
    
    def validate_jwt_secret(self) -> None:
        """Raise if using default JWT secret in production."""
        if not self.DEBUG and self.JWT_SECRET_KEY == "your-super-secret-key-change-in-production":
            raise RuntimeError(
                "SECURITY: Using default JWT secret key in production! "
                "Set JWT_SECRET_KEY environment variable."
            )


settings = Settings()
settings.validate_jwt_secret()
