from app.services.roadmap_service import build_roadmap


def test_roadmap_contains_only_incomplete_concepts() -> None:
    """Verify completed concepts are omitted from a generated learning schedule."""
    assert all(item["concept_id"] != "variables" for item in build_roadmap())
