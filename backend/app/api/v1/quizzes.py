from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Concept, Course, QuizAttempt, TopicProgress, User, utc_now
from app.schemas.learning import QuizAttemptRequest, QuizAttemptResponse, QuizQuestion

router = APIRouter()


@router.get("/{concept_id}", response_model=list[QuizQuestion])
def get_quiz(concept_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[QuizQuestion]:
    concept = db.scalar(select(Concept).join(Course, Course.id == Concept.course_id).where(Concept.id == concept_id, Course.owner_id == current_user.id))
    if concept is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    return [QuizQuestion(id=f"q-{concept_id}", prompt=f"Which statement best describes {concept.name}?", options=["A foundational learning concept", "A database table", "A deployment command"], answer_index=0)]


@router.post("/{concept_id}/attempts", response_model=QuizAttemptResponse, status_code=201)
def submit_attempt(concept_id: str, payload: QuizAttemptRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> QuizAttemptResponse:
    concept = db.scalar(select(Concept).join(Course, Course.id == Concept.course_id).where(Concept.id == concept_id, Course.owner_id == current_user.id))
    if concept is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    correct = payload.answer_index == 0
    score = 100.0 if correct else 0.0
    attempt = QuizAttempt(user_id=current_user.id, concept_id=concept_id, answer_index=payload.answer_index, correct=correct, score=score)
    db.add(attempt)
    progress = db.scalar(select(TopicProgress).where(TopicProgress.user_id == current_user.id, TopicProgress.concept_id == concept_id))
    if progress is None:
        progress = TopicProgress(user_id=current_user.id, concept_id=concept_id)
        db.add(progress)
    progress.score = score
    progress.completed = correct
    progress.last_studied_at = utc_now()
    concept.status = "completed" if correct else "in_progress"
    db.commit()
    db.refresh(attempt)
    return QuizAttemptResponse(attempt_id=attempt.id, correct=correct, score=score)
