from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# App settings from .env
class Settings(BaseSettings):
    spotify_client_id: str
    spotify_redirect_uri: str
    database_url: str
    redis_url: str
    allowed_origins: str
    session_secret: str
    frontend_url: str
    environment: str = "development"  # "production" → secure cookies, etc.

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # allow .env vars for frontend (e.g. VITE_API_URL) without error
    )

# Cached settings instance
@lru_cache
def get_settings() -> Settings:
    return Settings()