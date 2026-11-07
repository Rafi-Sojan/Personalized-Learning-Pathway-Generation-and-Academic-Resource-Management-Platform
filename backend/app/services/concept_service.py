"""Legacy in-memory concept accessors retained for compatibility."""

from app.repositories.in_memory import repository


def list_concepts(course_id: str | None = None) -> list[dict]:
    """Return cloned concept fixtures, optionally scoped to a course identifier."""
    values = repository.concepts
    if course_id:
        values = [item for item in values if item["course_id"] == course_id]
    return repository.clone(values)


def get_concept(concept_id: str) -> dict | None:
    """Return one cloned concept fixture or ``None`` when the identifier is absent."""
    return next((repository.clone(item) for item in repository.concepts if item["id"] == concept_id), None)
