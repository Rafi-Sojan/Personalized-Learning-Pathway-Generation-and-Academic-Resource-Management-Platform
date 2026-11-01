from app.services.roadmap_service import build_roadmap


def recommendations() -> list[dict]:
    """Return curated development recommendations for the sample learning catalog."""
    return build_roadmap(7)[:3]
