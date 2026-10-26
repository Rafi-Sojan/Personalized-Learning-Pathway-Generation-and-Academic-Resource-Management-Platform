from functools import lru_cache
from typing import Callable, TypeVar

from app.infrastructure.redis_client import RedisClient

T = TypeVar("T")
redis_cache = RedisClient()


def cached(func: Callable[..., T]) -> Callable[..., T]:
    return lru_cache(maxsize=128)(func)
