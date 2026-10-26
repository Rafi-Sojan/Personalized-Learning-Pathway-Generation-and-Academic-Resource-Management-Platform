from collections import defaultdict
from time import monotonic

from fastapi import HTTPException, Request, status

from app.core.config import settings


class RateLimiter:
    def __init__(self, limit: int = 60, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._redis = None
        try:
            import redis
            client = redis.from_url(settings.redis_url, socket_connect_timeout=0.2, socket_timeout=0.2)
            client.ping()
            self._redis = client
        except Exception:
            self._redis = None

    def allow(self, key: str) -> bool:
        if self._redis is not None:
            try:
                redis_key = f"roadmap:rate:{id(self)}:{key}"
                count = int(self._redis.incr(redis_key))
                if count == 1:
                    self._redis.expire(redis_key, self.window_seconds)
                return count <= self.limit
            except Exception:
                pass
        now = monotonic()
        recent = [stamp for stamp in self._requests[key] if now - stamp < self.window_seconds]
        self._requests[key] = recent
        if len(recent) >= self.limit:
            return False
        recent.append(now)
        return True


login_limiter = RateLimiter(limit=10, window_seconds=60)
expensive_limiter = RateLimiter(limit=30, window_seconds=60)


def enforce_rate_limit(request: Request, limiter: RateLimiter) -> None:
    client = request.client.host if request.client else "unknown"
    if not limiter.allow(client):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")
