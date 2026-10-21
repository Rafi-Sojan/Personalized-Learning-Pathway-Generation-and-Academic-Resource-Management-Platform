from app.repositories.in_memory import repository


def quiz_for_concept(concept_id: str) -> list[dict]:
    concept = next((item for item in repository.concepts if item["id"] == concept_id), None)
    if not concept:
        return []
    return [{
        "id": f"q-{concept_id}",
        "prompt": f"Which statement best describes {concept['name']}?",
        "options": ["A foundational learning concept", "A database table", "A deployment command"],
        "answer_index": 0,
    }]
