import redis

from .config import get_settings

settings = get_settings()

# Redis client
redis_client = redis.Redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True
)