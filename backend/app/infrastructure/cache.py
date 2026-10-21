from functools import lru_cache
from typing import Callable, TypeVar

T = TypeVar("T")


def cached(func: Callable[..., T]) -> Callable[..., T]:
    return lru_cache(maxsize=128)(func)
