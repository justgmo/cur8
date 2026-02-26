"""Token-bucket rate limit for Spotify API calls (Redis-backed)."""

import time
from uuid import UUID

from app.redis_client import redis_client

BUCKET_KEY_PREFIX = "spotify_tb:"
MAX_TOKENS = 30
REFILL_RATE = 0.5  # tokens per second (1 every 2 sec)
LUA_SCRIPT = """
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local tokens = tonumber(redis.call("HGET", key, "tokens") or max_tokens)
local at = tonumber(redis.call("HGET", key, "at") or now)
local refill = (now - at) * refill_rate
tokens = math.min(max_tokens, tokens + refill)
if tokens < 1 then
  return 0
end
redis.call("HSET", key, "tokens", tokens - 1, "at", now)
redis.call("EXPIRE", key, 120)
return 1
"""


def check_rate_limit(user_id: UUID) -> None:
    """Consume one token from the user's bucket; raise 429 if no token available."""
    from fastapi import HTTPException

    key = f"{BUCKET_KEY_PREFIX}{user_id}"
    now = str(time.time())
    result = redis_client.eval(LUA_SCRIPT, 1, key, str(MAX_TOKENS), str(REFILL_RATE), now)
    if result not in (1, "1"):
        raise HTTPException(status_code=429, detail="Too many Spotify requests; try shortly.")
