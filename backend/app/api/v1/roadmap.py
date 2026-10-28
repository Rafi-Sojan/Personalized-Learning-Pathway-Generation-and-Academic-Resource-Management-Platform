import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Concept, ConceptPrerequisite, Course, StudyPlan, StudyPlanItem, StudyPlanRevision, TopicProgress, User
from app.schemas.learning import RoadmapItem, RoadmapRequest, StudyPlanResponse, StudyPlanRevisionResponse
from app.services.audit import record_event

router = APIRouter()


@router.get("", response_model=list[RoadmapItem])
def get_roadmap(days: int = Query(default=14, ge=1, le=90), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[RoadmapItem]:
    course = db.scalar(select(Course).where(Course.owner_id == current_user.id))
    if course is None:
        return []
    return generate_items(db, current_user, course.id, date.today() + timedelta(days=days), 60)


@router.post("/generate", response_model=StudyPlanResponse, status_code=201)
def generate_roadmap(payload: RoadmapRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> StudyPlanResponse:
    course = db.scalar(select(Course).where(Course.id == payload.course_id, Course.owner_id == current_user.id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if payload.target_date < date.today():
        raise HTTPException(status_code=422, detail="Target date must be today or later")
    items = generate_items(db, current_user, course.id, payload.target_date, payload.daily_minutes, payload.revision_minutes)
    db.execute(update(StudyPlan).where(StudyPlan.user_id == current_user.id, StudyPlan.course_id == course.id, StudyPlan.status == "active").values(status="superseded"))
    plan = StudyPlan(user_id=current_user.id, course_id=course.id, target_date=payload.target_date, daily_minutes=payload.daily_minutes)
    db.add(plan)
    db.flush()
    for item in items:
        db.add(StudyPlanItem(plan_id=plan.id, concept_id=item.concept_id, scheduled_date=item.scheduled_date, minutes=item.minutes, sequence=int(item.id.split("-")[-1]) if item.id.split("-")[-1].isdigit() else 0, explanation=item.reason))
    db.flush()
    previous_revisions = db.scalars(select(StudyPlanRevision).join(StudyPlan, StudyPlan.id == StudyPlanRevision.plan_id).where(StudyPlan.user_id == current_user.id, StudyPlan.course_id == course.id)).all()
    revision = StudyPlanRevision(
        plan_id=plan.id,
        revision_number=len(previous_revisions) + 1,
        event="generated",
        snapshot=json.dumps([item.model_dump(mode="json") for item in items], sort_keys=True),
    )
    db.add(revision)
    record_event(db, "roadmap_generated", current_user.id, metadata={"course_id": course.id, "plan_id": plan.id, "revision": revision.revision_number})
    db.commit()
    return StudyPlanResponse(id=plan.id, course_id=plan.course_id, target_date=plan.target_date, daily_minutes=plan.daily_minutes, items=items)


@router.get("/history", response_model=list[StudyPlanRevisionResponse])
def roadmap_history(course_id: str | None = Query(default=None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[StudyPlanRevisionResponse]:
    query = select(StudyPlanRevision).join(StudyPlan, StudyPlan.id == StudyPlanRevision.plan_id).where(StudyPlan.user_id == current_user.id)
    if course_id:
        query = query.where(StudyPlan.course_id == course_id)
    revisions = db.scalars(query.order_by(StudyPlanRevision.created_at.desc())).all()
    return [StudyPlanRevisionResponse(id=item.id, plan_id=item.plan_id, revision_number=item.revision_number, event=item.event, created_at=item.created_at.isoformat()) for item in revisions]


def generate_items(db: Session, user: User, course_id: str, target_date: date, daily_minutes: int, revision_minutes: int = 0) -> list[RoadmapItem]:
    concepts = db.scalars(select(Concept).where(Concept.course_id == course_id, Concept.status != "completed")).all()
    edges = db.scalars(select(ConceptPrerequisite).join(Concept, Concept.id == ConceptPrerequisite.concept_id).where(Concept.course_id == course_id)).all()
    if _has_cycle({concept.id: [edge.prerequisite_id for edge in edges if edge.concept_id == concept.id] for concept in concepts}):
        raise HTTPException(status_code=422, detail="Cannot generate a roadmap from a cyclic prerequisite graph")
    progress = {item.concept_id: item for item in db.scalars(select(TopicProgress).where(TopicProgress.user_id == user.id)).all()}
    by_id = {concept.id: concept for concept in concepts}
    prerequisites = {concept.id: [edge.prerequisite_id for edge in edges if edge.concept_id == concept.id and edge.prerequisite_id in by_id] for concept in concepts}
    ordered = []
    remaining = set(by_id)
    while remaining:
        eligible = [by_id[item_id] for item_id in remaining if not (set(prerequisites[item_id]) & remaining)]
        if not eligible:
            raise HTTPException(status_code=422, detail="Cannot order concepts because prerequisites contain a cycle")
        def mastery_gap(item: Concept) -> float:
            item_progress = progress.get(item.id)
            score = item_progress.score if item_progress and item_progress.score is not None else 0.0
            return 100.0 - score

        eligible.sort(key=lambda item: (-item.difficulty, -mastery_gap(item)))
        ordered.extend(eligible)
        remaining -= {item.id for item in eligible}
    available_days = max((target_date - date.today()).days + 1, 1)
    planned_minutes = sum(25 + concept.difficulty * 10 for concept in ordered) + revision_minutes
    if planned_minutes > available_days * daily_minutes:
        raise HTTPException(status_code=422, detail="The deadline is infeasible for the available daily study time")
    result = []
    for index, concept in enumerate(ordered):
        day = min(index // max(daily_minutes // max(25, concept.difficulty * 10), 1), available_days - 1)
        result.append(RoadmapItem(id=f"plan-{index}", concept_id=concept.id, concept_name=concept.name, scheduled_date=date.today() + timedelta(days=day), minutes=min(daily_minutes, 25 + concept.difficulty * 10), status="planned", reason="Prioritized by incomplete status, difficulty, and current mastery gap."))
    return result


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
