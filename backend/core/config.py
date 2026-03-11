"""Application configuration via pydantic-settings."""

import re

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://auditai:auditai@localhost:5432/auditai"

    @property
    def async_database_url(self) -> str:
        """Database URL with asyncpg driver for SQLAlchemy."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        # Strip params asyncpg doesn't support
        if "ssl=require" not in url:
            url = url.replace("sslmode=require", "ssl=require")
        url = url.replace("&channel_binding=require", "")
        url = url.replace("channel_binding=require&", "")
        url = url.replace("channel_binding=require", "")
        # Strip connect_timeout (Neon may add it)
        url = re.sub(r"[?&]connect_timeout=\d+", "", url)
        url = url.replace("?&", "?")
        return url

    # LLM: Anthropic (set key) or mock mode (no key, free)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    use_mock_extractor: bool = False

    # App
    debug: bool = False
    deduplication_ttl_seconds: int = 60


settings = Settings()
