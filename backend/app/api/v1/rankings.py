from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.integrations.scoring_client import rank_concepts
from app.models import Concept, ConceptPrerequisite, Course, TopicProgress, User

router = APIRouter()


@router.get("")
def get_rankings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    """Return a private mastery summary without exposing fabricated or other learners' data."""
    progress = db.scalars(
        select(TopicProgress)
        .join(Concept, Concept.id == TopicProgress.concept_id)
        .join(Course, Course.id == Concept.course_id)
        .where(TopicProgress.user_id == current_user.id, Course.owner_id == current_user.id)
    ).all()
    points = round(sum(item.score if item.score is not None else (100.0 if item.completed else 0.0) for item in progress))
    return [{"rank": 1, "name": current_user.name, "points": points, "is_current_user": True}]


@router.get("/concepts")
def get_concept_rankings(course_id: str | None = Query(default=None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    """Score owned concepts from difficulty, learner progress, and prerequisite readiness."""
    query = select(Concept).join(Course, Course.id == Concept.course_id).where(Course.owner_id == current_user.id)
    if course_id:
        query = query.where(Concept.course_id == course_id)
    concepts = db.scalars(query).all()
    progress = {item.concept_id: item for item in db.scalars(select(TopicProgress).where(TopicProgress.user_id == current_user.id)).all()}
    concept_ids = [concept.id for concept in concepts]
    edges = db.scalars(select(ConceptPrerequisite).where(ConceptPrerequisite.concept_id.in_(concept_ids), ConceptPrerequisite.status == "accepted")).all() if concept_ids else []
    prerequisites = {concept.id: {edge.prerequisite_id for edge in edges if edge.concept_id == concept.id} for concept in concepts}
    completed = {item.concept_id for item in progress.values() if item.completed} | {concept.id for concept in concepts if concept.status == "completed"}
    ranked_inputs = []
    for concept in concepts:
        topic_progress = progress.get(concept.id)
        ranked_inputs.append({
            "id": concept.id,
            "difficulty": concept.difficulty,
            "progress": topic_progress.score if topic_progress and topic_progress.score is not None else 0.0,
            "prerequisite_ready": prerequisites[concept.id].issubset(completed),
        })
    ranked = rank_concepts(ranked_inputs)
    return ranked
