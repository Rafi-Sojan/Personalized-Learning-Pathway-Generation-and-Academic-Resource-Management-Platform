from fastapi import APIRouter

from app.repositories.in_memory import repository
from app.schemas.learning import ProgressUpdate

router = APIRouter()


@router.get("")
def get_progress() -> dict:
    completed = sum(1 for item in repository.concepts if item["status"] == "completed")
    return {"completed_concepts": completed, "total_concepts": len(repository.concepts), "updates": repository.clone(repository.progress)}


@router.post("")
def update_progress(payload: ProgressUpdate) -> dict:
    repository.progress[payload.concept_id] = payload.model_dump()
    for concept in repository.concepts:
        if concept["id"] == payload.concept_id:
            concept["status"] = "completed" if payload.completed else "in_progress"
    return {"saved": True, "update": payload.model_dump()}
