class RedisClient:
    """Small no-op compatible client used until Redis is configured."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._values.get(key)

    def set(self, key: str, value: str, expire: int | None = None) -> None:
        self._values[key] = value
