from functools import lru_cache
from pathlib import Path

from pydantic import Field
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

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()

