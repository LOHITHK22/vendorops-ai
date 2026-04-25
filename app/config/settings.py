from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "VendorOps AI"
    app_env: str = "local"
    app_debug: bool = True
    api_prefix: str = "/v1"

    database_url: str = "sqlite+aiosqlite:///./vendorops.db"
    local_storage_dir: Path = Field(default=Path("./storage"))
    reports_dir: Path = Field(default=Path("./reports_out"))

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    log_level: str = "INFO"
    log_format: str = "json"
    extraction_max_attempts: int = Field(default=3, ge=1, le=5)
    extraction_retry_base_seconds: float = Field(default=0.4, ge=0.0, le=10.0)
    cors_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
