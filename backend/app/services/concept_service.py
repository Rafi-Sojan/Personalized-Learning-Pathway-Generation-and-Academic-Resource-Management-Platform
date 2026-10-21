from app.repositories.in_memory import repository


def list_concepts(course_id: str | None = None) -> list[dict]:
    values = repository.concepts
    if course_id:
        values = [concept for concept in values if concept["course_id"] == course_id]
    return repository.clone(values)


def get_concept(concept_id: str) -> dict | None:
    return next((repository.clone(item) for item in repository.concepts if item["id"] == concept_id), None)
