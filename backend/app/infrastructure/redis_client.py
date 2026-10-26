from app.core.config import settings


class RedisClient:
    """Redis client with an in-memory fallback for local development."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}
        self._redis = None
        try:
            import redis
            client = redis.from_url(settings.redis_url, socket_connect_timeout=0.2, socket_timeout=0.2)
            client.ping()
            self._redis = client
        except Exception:
            self._redis = None

    def get(self, key: str) -> str | None:
        if self._redis is not None:
            try:
                value = self._redis.get(key)
                return value.decode() if value else None
            except Exception:
                pass
        return self._values.get(key)

    def set(self, key: str, value: str, expire: int | None = None) -> None:
        if self._redis is not None:
            try:
                self._redis.set(key, value, ex=expire)
                return
            except Exception:
                pass
        self._values[key] = value
