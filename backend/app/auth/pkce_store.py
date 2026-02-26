from app.redis_client import redis_client

_PKCE_TTL_SECONDS = 600

def save_pkce_state(state: str, verifier: str) -> None:
    """Store verifier in Redis keyed by state."""
    key = f"pkce:{state}"
    redis_client.setex(key, _PKCE_TTL_SECONDS, verifier)


def pop_pkce_verifier(state: str) -> None:
    """Get verifier for state and delete key (one-time use)."""
    key = f"pkce:{state}"
    with redis_client.pipeline() as pipe:
        pipe.get(key)
        pipe.delete(key)
        verifier, _ = pipe.execute()
    return verifier

