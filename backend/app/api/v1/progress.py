from datetime import timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.infrastructure.cache import redis_cache
from app.models import Concept, Course, QuizAttempt, TopicProgress, User, utc_now
from app.schemas.learning import ProgressUpdate

router = APIRouter()
ACTIVITY_HISTORY_DAYS = 400


@router.get("")
def get_progress(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Return learner progress and recent study timestamps used by the dashboard streak."""
    concepts = db.scalars(select(Concept).join(Course, Course.id == Concept.course_id).where(Course.owner_id == current_user.id)).all()
    updates = db.scalars(select(TopicProgress).where(TopicProgress.user_id == current_user.id)).all()
    cutoff = utc_now() - timedelta(days=ACTIVITY_HISTORY_DAYS)
    progress_activity = db.scalars(
        select(TopicProgress.last_studied_at).where(
            TopicProgress.user_id == current_user.id,
            TopicProgress.last_studied_at >= cutoff,
        )
    ).all()
    quiz_activity = db.scalars(
        select(QuizAttempt.created_at).where(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.created_at >= cutoff,
        )
    ).all()
    completed = sum(1 for item in updates if item.completed)
    activity_timestamps = sorted({
        (timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp.astimezone(timezone.utc)).isoformat()
        for timestamp in [*progress_activity, *quiz_activity]
    })
    return {
        "completed_concepts": completed,
        "total_concepts": len(concepts),
        "updates": {item.concept_id: {"concept_id": item.concept_id, "completed": item.completed, "score": item.score} for item in updates},
        "activity_timestamps": activity_timestamps,
    }


@router.post("")
def update_progress(payload: ProgressUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Upsert owned concept progress, synchronize concept status, and clear stale caches."""
    concept = db.scalar(select(Concept).join(Course, Course.id == Concept.course_id).where(Concept.id == payload.concept_id, Course.owner_id == current_user.id))
    if concept is None:
        raise HTTPException(404, "Concept not found")
    progress = db.scalar(select(TopicProgress).where(TopicProgress.user_id == current_user.id, TopicProgress.concept_id == payload.concept_id))
    if progress is None:
        progress = TopicProgress(user_id=current_user.id, concept_id=payload.concept_id)
        db.add(progress)
    progress.completed = payload.completed
    progress.score = payload.score
    progress.last_studied_at = utc_now()
    concept.status = "completed" if payload.completed else "in_progress"
    db.commit()
    redis_cache.delete(f"courses:{current_user.id}")
    redis_cache.delete(f"concepts:{current_user.id}:all")
    redis_cache.delete(f"concepts:{current_user.id}:{concept.course_id}")
    return {"saved": True, "update": payload.model_dump()}
