"""Legacy in-memory resource accessor retained for compatibility."""

from app.repositories.in_memory import repository


def list_resources(concept_id: str | None = None) -> list[dict]:
    """Return cloned legacy resource fixtures, optionally filtered by concept."""
    values = repository.resources
    if concept_id:
        values = [item for item in values if item["concept_id"] == concept_id]
    return repository.clone(values)
