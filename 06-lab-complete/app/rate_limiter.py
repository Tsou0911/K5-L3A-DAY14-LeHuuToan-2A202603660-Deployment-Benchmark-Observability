from hashlib import sha256
from uuid import uuid4

from fastapi import HTTPException

from .config import settings
from .redis_client import r


update_window = r.register_script("""
local clock = redis.call('TIME')
local now = tonumber(clock[1]) * 1000 + math.floor(tonumber(clock[2]) / 1000)
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now - 60000)
if redis.call('ZCARD', KEYS[1]) >= tonumber(ARGV[1]) then
    local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
    return math.max(1, math.ceil((tonumber(oldest[2]) + 60000 - now) / 1000))
end
redis.call('ZADD', KEYS[1], now, ARGV[2])
redis.call('PEXPIRE', KEYS[1], 60000)
return 0
""")


def check_rate_limit(key: str) -> None:
    if settings.rate_limit_per_minute <= 0:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    digest = sha256(key.encode()).hexdigest()
    retry_after = update_window(
        keys=[f"lab14:rate:{digest}"], args=[settings.rate_limit_per_minute, uuid4().hex]
    )
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )
