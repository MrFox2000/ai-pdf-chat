"""Application settings loaded from environment variables or a .env file."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI PDF Chat"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    openai_api_key: str | None = None
    chat_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    chunk_size: int = 900
    chunk_overlap: int = 120
    top_k: int = 5
    max_upload_mb: int = 20

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def offline(self) -> bool:
        """Fall back to deterministic local models when no API key is configured."""
        return not self.openai_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
