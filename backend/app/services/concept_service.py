from app.repositories.in_memory import repository


def list_concepts(course_id: str | None = None) -> list[dict]:
    """Return development concepts, optionally restricted to a course identifier."""
    values = repository.concepts
    if course_id:
        values = [concept for concept in values if concept["course_id"] == course_id]
    return repository.clone(values)


def get_concept(concept_id: str) -> dict | None:
    """Find a development concept by identifier or return no match."""
    return next((repository.clone(item) for item in repository.concepts if item["id"] == concept_id), None)
