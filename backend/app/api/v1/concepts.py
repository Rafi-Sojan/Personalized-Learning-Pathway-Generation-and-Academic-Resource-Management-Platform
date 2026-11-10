from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.infrastructure.cache import get_json, set_json, redis_cache
from app.models import Concept as ConceptModel, ConceptPrerequisite, Course, SyllabusRecord, User
from app.schemas.learning import Concept

router = APIRouter()


class PrerequisiteRequest(BaseModel):
    prerequisite_id: str


@router.get("", response_model=list[Concept])
def get_concepts(course_id: str | None = Query(default=None), syllabus_only: bool = Query(default=False), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Concept]:
    """List owned concepts and prerequisite edges, using a short-lived user-scoped cache."""
    cache_key = f"concepts:{current_user.id}:{course_id or 'all'}:{'syllabus' if syllabus_only else 'all-sources'}"
    cached = get_json(cache_key)
    if isinstance(cached, list):
        return [Concept(**item) for item in cached]
    query = select(ConceptModel).join(Course, Course.id == ConceptModel.course_id).where(Course.owner_id == current_user.id)
    if course_id:
        query = query.where(ConceptModel.course_id == course_id)
    if syllabus_only:
        query = query.where(ConceptModel.syllabus_version_id.is_not(None))
    concepts = db.scalars(query.order_by(ConceptModel.unit_sequence, ConceptModel.source_page, ConceptModel.name)).all()
    records = db.scalars(select(SyllabusRecord).where(SyllabusRecord.mapped_concept_id.in_([item.id for item in concepts]))).all() if concepts else []
    statuses: dict[str, set[str]] = {}
    versions = {item.id: item.syllabus_version_id for item in concepts}
    for record in records:
        if record.mapped_concept_id and record.syllabus_version_id == versions.get(record.mapped_concept_id):
            statuses.setdefault(record.mapped_concept_id, set()).add(record.review_status)
    review_status = {
        concept_id: "verified" if "verified" in values else "pending_review" if "pending_review" in values else "rejected"
        for concept_id, values in statuses.items()
    }
    if syllabus_only:
        concepts = [item for item in concepts if review_status.get(item.id) != "rejected"]
    prerequisites = db.scalars(select(ConceptPrerequisite).where(ConceptPrerequisite.concept_id.in_([item.id for item in concepts]))).all() if concepts else []
    by_concept: dict[str, list[str]] = {}
    suggested: dict[str, list[str]] = {}
    for edge in prerequisites:
        target = by_concept if edge.status == "accepted" else suggested
        target.setdefault(edge.concept_id, []).append(edge.prerequisite_id)
    result = [Concept(id=item.id, name=item.name, course_id=item.course_id, difficulty=item.difficulty, status=item.status, prerequisites=by_concept.get(item.id, []), suggested_prerequisites=suggested.get(item.id, []), unit_label=item.unit_label, unit_sequence=item.unit_sequence, source_page=item.source_page, syllabus_version_id=item.syllabus_version_id, parent_concept_id=item.parent_concept_id, estimated_minutes=item.estimated_minutes, review_status=review_status.get(item.id)) for item in concepts]
    set_json(cache_key, [item.model_dump() for item in result], expire=30)
    return result


@router.get("/{concept_id}", response_model=Concept)
def get_one_concept(concept_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Concept:
    """Return one owned concept with its prerequisite identifiers."""
    concept = db.scalar(select(ConceptModel).join(Course, Course.id == ConceptModel.course_id).where(ConceptModel.id == concept_id, Course.owner_id == current_user.id))
    if concept is None:
        raise HTTPException(404, "Concept not found")
    edges = db.scalars(select(ConceptPrerequisite).where(ConceptPrerequisite.concept_id == concept.id)).all()
    statuses = set(db.scalars(select(SyllabusRecord.review_status).where(SyllabusRecord.mapped_concept_id == concept.id, SyllabusRecord.syllabus_version_id == concept.syllabus_version_id)).all())
    review_status = "verified" if "verified" in statuses else "pending_review" if "pending_review" in statuses else "rejected" if statuses else None
    return Concept(id=concept.id, name=concept.name, course_id=concept.course_id, difficulty=concept.difficulty, status=concept.status, prerequisites=[edge.prerequisite_id for edge in edges if edge.status == "accepted"], suggested_prerequisites=[edge.prerequisite_id for edge in edges if edge.status == "proposed"], unit_label=concept.unit_label, unit_sequence=concept.unit_sequence, source_page=concept.source_page, syllabus_version_id=concept.syllabus_version_id, parent_concept_id=concept.parent_concept_id, estimated_minutes=concept.estimated_minutes, review_status=review_status)


@router.post("/{concept_id}/prerequisites", status_code=201)
def add_prerequisite(concept_id: str, payload: PrerequisiteRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Create an owned same-course prerequisite edge after rejecting self-links and cycles."""
    concept = db.scalar(select(ConceptModel).join(Course, Course.id == ConceptModel.course_id).where(ConceptModel.id == concept_id, Course.owner_id == current_user.id))
    prerequisite = db.scalar(select(ConceptModel).join(Course, Course.id == ConceptModel.course_id).where(ConceptModel.id == payload.prerequisite_id, Course.owner_id == current_user.id))
    if concept is None or prerequisite is None or concept.course_id != prerequisite.course_id:
        raise HTTPException(status_code=404, detail="Concept or prerequisite not found")
    if concept_id == payload.prerequisite_id:
        raise HTTPException(status_code=422, detail="A concept cannot depend on itself")
    edges = db.scalars(select(ConceptPrerequisite).join(ConceptModel, ConceptModel.id == ConceptPrerequisite.concept_id).where(ConceptModel.course_id == concept.course_id)).all()
    graph: dict[str, list[str]] = {}
    for edge in edges:
        if edge.status == "accepted":
            graph.setdefault(edge.concept_id, []).append(edge.prerequisite_id)
    graph.setdefault(concept_id, []).append(payload.prerequisite_id)
    if _has_cycle(graph):
        raise HTTPException(status_code=422, detail="Prerequisite graph contains a cycle")
    db.merge(ConceptPrerequisite(concept_id=concept_id, prerequisite_id=payload.prerequisite_id, status="accepted", rationale="Added by learner"))
    db.commit()
    redis_cache.delete(f"concepts:{current_user.id}:all")
    redis_cache.delete(f"concepts:{current_user.id}:{concept.course_id}")
    return {"saved": True, "concept_id": concept_id, "prerequisite_id": payload.prerequisite_id}


@router.post("/{concept_id}/prerequisites/{prerequisite_id}/review")
def review_prerequisite(concept_id: str, prerequisite_id: str, status: str = Query(..., pattern="^(accepted|rejected|proposed)$"), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Review a source-derived prerequisite suggestion, rejecting cycles before acceptance."""
    concept = db.scalar(select(ConceptModel).join(Course, Course.id == ConceptModel.course_id).where(ConceptModel.id == concept_id, Course.owner_id == current_user.id))
    edge = db.get(ConceptPrerequisite, (concept_id, prerequisite_id))
    prerequisite = db.scalar(select(ConceptModel).join(Course, Course.id == ConceptModel.course_id).where(ConceptModel.id == prerequisite_id, Course.owner_id == current_user.id))
    if concept is None or prerequisite is None or edge is None or prerequisite.course_id != concept.course_id:
        raise HTTPException(status_code=404, detail="Prerequisite suggestion not found")
    if status == "accepted":
        edges = db.scalars(select(ConceptPrerequisite).join(ConceptModel, ConceptModel.id == ConceptPrerequisite.concept_id).where(ConceptModel.course_id == concept.course_id, ConceptPrerequisite.status == "accepted")).all()
        graph: dict[str, list[str]] = {}
        for existing in edges:
            graph.setdefault(existing.concept_id, []).append(existing.prerequisite_id)
        graph.setdefault(concept_id, []).append(prerequisite_id)
        if _has_cycle(graph):
            raise HTTPException(status_code=422, detail="Accepting this prerequisite would create a cycle")
    edge.status = status
    db.commit()
    redis_cache.delete(f"concepts:{current_user.id}:all")
    redis_cache.delete(f"concepts:{current_user.id}:{concept.course_id}")
    return {"concept_id": concept_id, "prerequisite_id": prerequisite_id, "status": status}


def _has_cycle(graph: dict[str, list[str]]) -> bool:
    """Detect a directed cycle in the concept-to-prerequisite adjacency map."""
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> bool:
        """Track the active DFS path separately from nodes already fully explored."""
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
