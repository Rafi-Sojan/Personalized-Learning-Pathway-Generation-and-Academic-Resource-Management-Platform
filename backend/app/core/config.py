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
    max_pdf_pages: int = int(os.getenv("MAX_PDF_PAGES", "100"))
    max_extracted_text_chars: int = int(os.getenv("MAX_EXTRACTED_TEXT_CHARS", "500000"))
    worker_timeout_seconds: int = int(os.getenv("DOCUMENT_WORKER_TIMEOUT_SECONDS", "120"))
    max_processing_attempts: int = int(os.getenv("DOCUMENT_MAX_PROCESSING_ATTEMPTS", "3"))
    document_retry_delay_seconds: int = int(os.getenv("DOCUMENT_RETRY_DELAY_SECONDS", "60"))
    ocr_enabled: bool = os.getenv("OCR_ENABLED", "false").lower() in {"1", "true", "yes"}
    scoring_engine_path: str = os.getenv("SCORING_ENGINE_PATH", "")
    storage_backend: str = os.getenv("STORAGE_BACKEND", "local").lower()
    storage_bucket: str = os.getenv("STORAGE_BUCKET", "")
    storage_prefix: str = os.getenv("STORAGE_PREFIX", "learning-roadmap")
    storage_endpoint_url: str = os.getenv("STORAGE_ENDPOINT_URL", "")
    audit_retention_days: int = int(os.getenv("AUDIT_RETENTION_DAYS", "3650"))
    initial_admin_email: str = os.getenv("INITIAL_ADMIN_EMAIL", "")
    initial_admin_password: str = os.getenv("INITIAL_ADMIN_PASSWORD", "")
    metrics_auth_token: str = os.getenv("METRICS_AUTH_TOKEN", "")

    def __post_init__(self) -> None:
        if self.environment.lower() == "production" and self.secret_key == "development-only-change-me":
            raise ValueError("SECRET_KEY must be explicitly configured in production")
        if self.max_pdf_pages < 1 or self.max_extracted_text_chars < 1:
            raise ValueError("PDF processing limits must be positive")
        if self.worker_timeout_seconds < 1 or self.max_processing_attempts < 1 or self.document_retry_delay_seconds < 0:
            raise ValueError("Document retry settings are invalid")
        if self.storage_backend not in {"local", "s3"}:
            raise ValueError("STORAGE_BACKEND must be local or s3")
        if self.storage_backend == "s3" and not self.storage_bucket:
            raise ValueError("STORAGE_BUCKET is required when STORAGE_BACKEND=s3")
        if self.audit_retention_days < 1:
            raise ValueError("AUDIT_RETENTION_DAYS must be positive")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


settings = Settings()
