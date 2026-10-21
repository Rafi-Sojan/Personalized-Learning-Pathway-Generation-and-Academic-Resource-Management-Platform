from collections.abc import Generator


def get_db() -> Generator[None, None, None]:
    """Placeholder dependency for a future SQLAlchemy session."""
    yield None
