from app.repositories.in_memory import repository


def list_resources(concept_id: str | None = None) -> list[dict]:
    values = repository.resources
    if concept_id:
        values = [resource for resource in values if resource["concept_id"] == concept_id]
    return repository.clone(values)
