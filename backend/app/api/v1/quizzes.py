from fastapi import APIRouter

from app.schemas.learning import QuizQuestion
from app.services.quiz_service import quiz_for_concept

router = APIRouter()


@router.get("/{concept_id}", response_model=list[QuizQuestion])
def get_quiz(concept_id: str) -> list[QuizQuestion]:
    return quiz_for_concept(concept_id)
