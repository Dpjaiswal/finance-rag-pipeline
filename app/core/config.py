import logging
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Financial Document Management API"
    environment: str = Field(default="dev", alias="ENVIRONMENT")
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(
        default="sqlite+pysqlite:///./local.db",
        alias="DATABASE_URL",
    )
    test_database_url: str = "sqlite+pysqlite:///:memory:"

    jwt_secret_key: str | None = Field(default=None, alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    storage_dir: Path = Path("storage")
    max_upload_size_mb: int = 25
    allowed_mime_types: set[str] = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    }

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "financial_documents_dev"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    reranker_type: str = "fallback"
    cross_encoder_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    default_admin_email: str | None = None
    default_admin_password: str | None = None
    seed_analyst_email: str | None = None
    seed_analyst_password: str | None = None
    seed_auditor_email: str | None = None
    seed_auditor_password: str | None = None
    seed_client_email: str | None = None
    seed_client_password: str | None = None

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str) and value.lower() in {"release", "prod", "production"}:
            return False
        if isinstance(value, str) and value.lower() in {"dev", "development"}:
            return True
        return value

    @field_validator("jwt_secret_key", mode="after")
    @classmethod
    def require_or_generate_jwt_secret(cls, value, info):
        environment = (info.data.get("environment") or "dev").lower()
        if value:
            return value
        if environment in {"prod", "production", "staging"}:
            raise ValueError("JWT_SECRET_KEY must be set outside local development")
        generated = secrets.token_urlsafe(48)
        logger.warning("JWT_SECRET_KEY is not set; generated an ephemeral local development secret")
        return generated


@lru_cache
def get_settings() -> Settings:
    return Settings()
