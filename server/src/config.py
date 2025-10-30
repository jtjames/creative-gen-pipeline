"""Configuration management for the Creative Automation API server."""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings sourced from environment variables."""

    dropbox_access_token: Optional[str] = None
    dropbox_root_path: str = "/"
    temporary_link_ttl_seconds: int = 300

    gemini_api_key: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
