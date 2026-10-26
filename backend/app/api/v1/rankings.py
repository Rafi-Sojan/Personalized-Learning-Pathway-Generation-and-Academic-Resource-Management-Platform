from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.integrations.scoring_client import rank_concepts
from app.models import Concept, Course, TopicProgress, User

router = APIRouter()


@router.get("")
def get_rankings(_: User = Depends(get_current_user)) -> list[dict]:
    return [
        {"rank": 1, "name": "Aarav", "points": 1240},
        {"rank": 2, "name": "Maya", "points": 1110},
        {"rank": 3, "name": "You", "points": 860},
    ]


@router.get("/concepts")
def get_concept_rankings(course_id: str | None = Query(default=None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    query = select(Concept).join(Course, Course.id == Concept.course_id).where(Course.owner_id == current_user.id)
    if course_id:
        query = query.where(Concept.course_id == course_id)
    concepts = db.scalars(query).all()
    progress = {item.concept_id: item for item in db.scalars(select(TopicProgress).where(TopicProgress.user_id == current_user.id)).all()}
    ranked = rank_concepts([
        {"id": concept.id, "difficulty": concept.difficulty, "progress": progress.get(concept.id).score if progress.get(concept.id) and progress.get(concept.id).score is not None else 0.0, "prerequisite_ready": concept.status != "not_started"}
        for concept in concepts
    ])
    return ranked
