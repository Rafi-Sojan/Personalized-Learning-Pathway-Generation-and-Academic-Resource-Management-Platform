from app.services.roadmap_service import build_roadmap


def recommendations() -> list[dict]:
    return build_roadmap(7)[:3]
