from collections import defaultdict
from time import monotonic


class RateLimiter:
    def __init__(self, limit: int = 60, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = monotonic()
        recent = [stamp for stamp in self._requests[key] if now - stamp < self.window_seconds]
        self._requests[key] = recent
        if len(recent) >= self.limit:
            return False
        recent.append(now)
        return True
