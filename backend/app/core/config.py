import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Intelligent Learning Roadmap")
    environment: str = os.getenv("ENVIRONMENT", "development")
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    secret_key: str = os.getenv("SECRET_KEY", "development-only-change-me")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./learning.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    upload_dir: str = os.getenv("UPLOAD_DIR", "storage/uploads")
    processed_dir: str = os.getenv("PROCESSED_DIR", "storage/processed")
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

    def __post_init__(self) -> None:
        if self.environment.lower() == "production" and self.secret_key == "development-only-change-me":
            raise ValueError("SECRET_KEY must be explicitly configured in production")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


settings = Settings()
