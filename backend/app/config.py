import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# #region agent log
def _debug_log_env():
    keys = ("SPOTIFY_CLIENT_ID", "SPOTIFY_REDIRECT_URI", "DATABASE_URL", "REDIS_URL", "ALLOWED_ORIGINS", "SESSION_SECRET", "FRONTEND_URL", "ENVIRONMENT")
    present = {k: k in os.environ for k in keys}
    session_len = len(os.environ.get("SESSION_SECRET", ""))
    line = '{"sessionId":"64f2a8","hypothesisId":"env_at_settings_load","location":"config.py:get_settings","message":"Required env presence","data":' + str(present).replace("'", '"') + ',"session_secret_len":' + str(session_len) + ',"timestamp":' + str(int(__import__("time").time() * 1000)) + '}\n'
    try:
        with open("/Users/justin/Developer/cur8/.cursor/debug-64f2a8.log", "a") as f:
            f.write(line)
    except Exception:
        pass
    print("[cur8-debug]", line.strip())
# #endregion

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
    _debug_log_env()
    return Settings()