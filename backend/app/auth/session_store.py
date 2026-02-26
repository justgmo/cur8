import secrets
from uuid import UUID

from app.redis_client import redis_client

_SESSION_TTL_SECONDS = 7 * 24 * 3600  # 7 days


def create_session(user_id: UUID) -> str:
    """Create session in Redis for user_id."""
    sid = secrets.token_urlsafe(32)
    key = f"session:{sid}"
    redis_client.setex(key, _SESSION_TTL_SECONDS, str(user_id))
    return sid


def get_session(session_id: str) -> str | None:
    """Return stored user_id or None."""
    if not session_id:
        return None
    key = f"session:{session_id}"
    return redis_client.get(key)


def delete_session(session_id: str) -> None:
    """Delete session key (logout)."""
    if session_id:
        redis_client.delete(f"session:{session_id}")