import logging

import redis
from fastapi import Depends, HTTPException, status
from app.config import settings
from app.deps import get_current_user
from app.models import User

logger = logging.getLogger(__name__)

redis_client = redis.Redis.from_url(settings.redis_url, socket_timeout=1, socket_connect_timeout=1)

def rate_limit(name : str, limit: int, window_seconds: int):
    def check(current_user: User = Depends(get_current_user)) -> User:
        if not settings.rate_limit_enabled:
            return current_user

        key = f"ratelimit:{name}:{current_user.id}"
        try:
            redis_client.set(key, 0, ex=window_seconds, nx=True)
            count = redis_client.incr(key)
            seconds_left = max(redis_client.ttl(key), 1)
        except redis.RedisError:
            logger.warning("Rate limiter unabliable; allowing request")
            return current_user

        if count > limit:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, f"Too many requests. Please try again in {seconds_left} seconds.", headers={"Retry-After": str(seconds_left)},)
        return current_user

    return check
 