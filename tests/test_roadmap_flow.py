from app.services.roadmap_service import build_roadmap


def test_roadmap_contains_only_incomplete_concepts() -> None:
    assert all(item["concept_id"] != "variables" for item in build_roadmap())
