from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.infrastructure.cache import get_json, set_json, redis_cache
from app.models import Concept as ConceptModel, ConceptPrerequisite, Course, User
from app.schemas.learning import Concept

router = APIRouter()


class PrerequisiteRequest(BaseModel):
    prerequisite_id: str


@router.get("", response_model=list[Concept])
def get_concepts(course_id: str | None = Query(default=None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Concept]:
    cache_key = f"concepts:{current_user.id}:{course_id or 'all'}"
    cached = get_json(cache_key)
    if isinstance(cached, list):
        return [Concept(**item) for item in cached]
    query = select(ConceptModel).join(Course, Course.id == ConceptModel.course_id).where(Course.owner_id == current_user.id)
    if course_id:
        query = query.where(ConceptModel.course_id == course_id)
    concepts = db.scalars(query).all()
    prerequisites = db.scalars(select(ConceptPrerequisite).where(ConceptPrerequisite.concept_id.in_([item.id for item in concepts]))).all() if concepts else []
    by_concept: dict[str, list[str]] = {}
    for edge in prerequisites:
        by_concept.setdefault(edge.concept_id, []).append(edge.prerequisite_id)
    result = [Concept(id=item.id, name=item.name, course_id=item.course_id, difficulty=item.difficulty, status=item.status, prerequisites=by_concept.get(item.id, [])) for item in concepts]
    set_json(cache_key, [item.model_dump() for item in result], expire=30)
    return result


@router.get("/{concept_id}", response_model=Concept)
def get_one_concept(concept_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Concept:
    concept = db.scalar(select(ConceptModel).join(Course, Course.id == ConceptModel.course_id).where(ConceptModel.id == concept_id, Course.owner_id == current_user.id))
    if concept is None:
        raise HTTPException(404, "Concept not found")
    prerequisites = db.scalars(select(ConceptPrerequisite.prerequisite_id).where(ConceptPrerequisite.concept_id == concept.id)).all()
    return Concept(id=concept.id, name=concept.name, course_id=concept.course_id, difficulty=concept.difficulty, status=concept.status, prerequisites=list(prerequisites))


@router.post("/{concept_id}/prerequisites", status_code=201)
def add_prerequisite(concept_id: str, payload: PrerequisiteRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    concept = db.scalar(select(ConceptModel).join(Course, Course.id == ConceptModel.course_id).where(ConceptModel.id == concept_id, Course.owner_id == current_user.id))
    prerequisite = db.scalar(select(ConceptModel).join(Course, Course.id == ConceptModel.course_id).where(ConceptModel.id == payload.prerequisite_id, Course.owner_id == current_user.id))
    if concept is None or prerequisite is None or concept.course_id != prerequisite.course_id:
        raise HTTPException(status_code=404, detail="Concept or prerequisite not found")
    if concept_id == payload.prerequisite_id:
        raise HTTPException(status_code=422, detail="A concept cannot depend on itself")
    edges = db.scalars(select(ConceptPrerequisite).join(ConceptModel, ConceptModel.id == ConceptPrerequisite.concept_id).where(ConceptModel.course_id == concept.course_id)).all()
    graph: dict[str, list[str]] = {}
    for edge in edges:
        graph.setdefault(edge.concept_id, []).append(edge.prerequisite_id)
    graph.setdefault(concept_id, []).append(payload.prerequisite_id)
    if _has_cycle(graph):
        raise HTTPException(status_code=422, detail="Prerequisite graph contains a cycle")
    db.merge(ConceptPrerequisite(concept_id=concept_id, prerequisite_id=payload.prerequisite_id))
    db.commit()
    redis_cache.delete(f"concepts:{current_user.id}:all")
    redis_cache.delete(f"concepts:{current_user.id}:{concept.course_id}")
    return {"saved": True, "concept_id": concept_id, "prerequisite_id": payload.prerequisite_id}


def _has_cycle(graph: dict[str, list[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(parent) for parent in graph.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False
    return any(visit(node) for node in graph)
