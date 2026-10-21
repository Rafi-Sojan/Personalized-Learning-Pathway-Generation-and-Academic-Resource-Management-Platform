from fastapi import APIRouter, HTTPException, Query

from app.schemas.learning import Concept
from app.services.concept_service import get_concept, list_concepts

router = APIRouter()


@router.get("", response_model=list[Concept])
def get_concepts(course_id: str | None = Query(default=None)) -> list[Concept]:
    return list_concepts(course_id)


@router.get("/{concept_id}", response_model=Concept)
def get_one_concept(concept_id: str) -> Concept:
    concept = get_concept(concept_id)
    if not concept:
        raise HTTPException(404, "Concept not found")
    return concept
