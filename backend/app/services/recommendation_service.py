"""Legacy recommendation helper retained for compatibility."""

from app.services.roadmap_service import build_roadmap


def recommendations() -> list[dict]:
    """Return the first three items from the legacy sample roadmap utility."""
    return build_roadmap(7)[:3]
