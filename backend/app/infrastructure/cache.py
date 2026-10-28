import json
from functools import lru_cache
from typing import Callable, TypeVar

from app.infrastructure.redis_client import RedisClient

T = TypeVar("T")
redis_cache = RedisClient()


def get_json(key: str) -> object | None:
    value = redis_cache.get(key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        redis_cache.delete(key)
        return None


def set_json(key: str, value: object, expire: int = 60) -> None:
    redis_cache.set(key, json.dumps(value, default=str, sort_keys=True), expire=expire)


def invalidate_prefix(prefix: str) -> None:
    # Redis key scans are deliberately optional; local fallback values are cleared by exact keys.
    client = getattr(redis_cache, "_redis", None)
    if client is not None:
        for key in client.scan_iter(match=f"{prefix}*"):
            client.delete(key)


def cached(func: Callable[..., T]) -> Callable[..., T]:
    return lru_cache(maxsize=128)(func)
