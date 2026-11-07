import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import exists, or_, select, update
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Concept, ConceptPrerequisite, Course, HistoricalExamQuestion, Resource, StudyPlan, StudyPlanItem, StudyPlanRevision, SyllabusRecord, SyllabusVersion, TopicProgress, User
from app.schemas.learning import RoadmapItem, RoadmapRequest, StudyPlanResponse, StudyPlanRevisionResponse
from app.services.audit import record_event

router = APIRouter()


@router.get("", response_model=list[RoadmapItem])
def get_roadmap(course_id: str = Query(...), days: int = Query(default=14, ge=1, le=90), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[RoadmapItem]:
    """Preview a schedule for the explicitly selected learner-owned course."""
    course = db.scalar(select(Course).where(Course.id == course_id, Course.owner_id == current_user.id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return generate_items(db, current_user, course.id, date.today() + timedelta(days=days), 60, allow_partial=True)


@router.post("/generate", response_model=StudyPlanResponse, status_code=201)
def generate_roadmap(payload: RoadmapRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> StudyPlanResponse:
    """Persist a feasible course plan, supersede the previous plan, and snapshot the revision."""
    course = db.scalar(select(Course).where(Course.id == payload.course_id, Course.owner_id == current_user.id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    has_processed_syllabus = db.scalar(
        select(SyllabusVersion.id)
        .join(Resource, Resource.id == SyllabusVersion.source_resource_id)
        .where(
            SyllabusVersion.course_id == course.id,
            Resource.kind == "syllabus_pdf",
            Resource.processing_status == "processed",
        )
        .limit(1)
    )
    if has_processed_syllabus is None:
        raise HTTPException(status_code=409, detail="Upload and process a syllabus copy, then generate its concept map before creating a roadmap")
    if payload.target_date < date.today():
        raise HTTPException(status_code=422, detail="Target date must be today or later")
    items = generate_items(db, current_user, course.id, payload.target_date, payload.daily_minutes, payload.revision_minutes)
    if not items:
        raise HTTPException(status_code=409, detail="Generate syllabus-derived concepts before creating a roadmap")
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
    """List the authenticated learner's roadmap revision history, optionally by course."""
    query = select(StudyPlanRevision).join(StudyPlan, StudyPlan.id == StudyPlanRevision.plan_id).where(StudyPlan.user_id == current_user.id)
    if course_id:
        query = query.where(StudyPlan.course_id == course_id)
    revisions = db.scalars(query.order_by(StudyPlanRevision.created_at.desc())).all()
    return [StudyPlanRevisionResponse(id=item.id, plan_id=item.plan_id, revision_number=item.revision_number, event=item.event, created_at=item.created_at.isoformat()) for item in revisions]


def generate_items(db: Session, user: User, course_id: str, target_date: date, daily_minutes: int, revision_minutes: int = 0, allow_partial: bool = False) -> list[RoadmapItem]:
    """Order incomplete concepts by evidence and prerequisites, optionally limiting previews to available capacity."""
    records_exist = exists(select(SyllabusRecord.id).where(SyllabusRecord.mapped_concept_id == Concept.id, SyllabusRecord.syllabus_version_id == Concept.syllabus_version_id))
    records_verified = exists(select(SyllabusRecord.id).where(SyllabusRecord.mapped_concept_id == Concept.id, SyllabusRecord.syllabus_version_id == Concept.syllabus_version_id, SyllabusRecord.review_status == "verified"))
    concepts = db.scalars(select(Concept).where(
        Concept.course_id == course_id,
        Concept.status != "completed",
        Concept.syllabus_version_id.is_not(None),
        or_(~records_exist, records_verified),
    )).all()
    edges = db.scalars(select(ConceptPrerequisite).join(Concept, Concept.id == ConceptPrerequisite.concept_id).where(Concept.course_id == course_id, ConceptPrerequisite.status == "accepted")).all()
    if _has_cycle({concept.id: [edge.prerequisite_id for edge in edges if edge.concept_id == concept.id] for concept in concepts}):
        raise HTTPException(status_code=422, detail="Cannot generate a roadmap from a cyclic prerequisite graph")
    progress = {item.concept_id: item for item in db.scalars(select(TopicProgress).where(TopicProgress.user_id == user.id)).all()}
    evidence: dict[str, list[HistoricalExamQuestion]] = {}
    for question in db.scalars(select(HistoricalExamQuestion).where(
        HistoricalExamQuestion.course_id == course_id,
        HistoricalExamQuestion.review_status == "verified",
        HistoricalExamQuestion.question_kind == "main",
        HistoricalExamQuestion.concept_id.is_not(None),
    )).all():
        evidence.setdefault(question.concept_id or "", []).append(question)
    by_id = {concept.id: concept for concept in concepts}
    prerequisites = {concept.id: [edge.prerequisite_id for edge in edges if edge.concept_id == concept.id and edge.prerequisite_id in by_id] for concept in concepts}
    ordered = []
    remaining = set(by_id)
    while remaining:
        eligible = [by_id[item_id] for item_id in remaining if not (set(prerequisites[item_id]) & remaining)]
        if not eligible:
            raise HTTPException(status_code=422, detail="Cannot order concepts because prerequisites contain a cycle")
        def mastery_gap(item: Concept) -> float:
            """Translate the learner's latest concept score into a remaining mastery gap."""
            item_progress = progress.get(item.id)
            score = item_progress.score if item_progress and item_progress.score is not None else 0.0
            return 100.0 - score

        current_year = date.today().year
        def evidence_priority(item: Concept) -> float:
            """Weight reviewed question recurrence by recency and documented marks."""
            questions = evidence.get(item.id, [])
            if not questions:
                return 0.0
            weighted = sum((1 / (1 + max(current_year - question.exam_year, 0) * 0.15)) * (1 + min(question.marks or 0, 100) / 100) for question in questions)
            return weighted

        eligible.sort(key=lambda item: (-evidence_priority(item), -mastery_gap(item), -item.difficulty, item.source_page or 0, (item.unit_label or "").casefold(), item.name.casefold(), item.id))
        ordered.extend(eligible)
        remaining -= {item.id for item in eligible}
    available_days = max((target_date - date.today()).days + 1, 1)
    def estimated_minutes(concept: Concept) -> int:
        """Use allocated syllabus unit time, falling back to concept difficulty."""
        return concept.estimated_minutes or (25 + concept.difficulty * 10)

    available_minutes = max(available_days * daily_minutes - revision_minutes, 0)
    required_minutes = sum(max(1, estimated_minutes(concept)) for concept in ordered)
    if not allow_partial and required_minutes > available_minutes:
        raise HTTPException(status_code=422, detail="The deadline is infeasible for the available daily study time")
    result: list[RoadmapItem] = []
    remaining_budget = available_minutes
    day = 0
    minutes_left = daily_minutes
    sequence = 0
    for concept in ordered:
        estimate = max(1, estimated_minutes(concept))
        scheduled_minutes = min(estimate, remaining_budget)
        if scheduled_minutes <= 0:
            break
        remaining_for_concept = scheduled_minutes
        chunks: list[tuple[int, int]] = []
        while remaining_for_concept > 0 and day < available_days:
            if minutes_left == 0:
                day += 1
                minutes_left = daily_minutes
                continue
            chunk = min(remaining_for_concept, minutes_left)
            chunks.append((day, chunk))
            remaining_for_concept -= chunk
            remaining_budget -= chunk
            minutes_left -= chunk
        linked = evidence.get(concept.id, [])
        reasons = ["Prerequisites are satisfied", f"mastery gap {mastery_gap(concept):.0f}%", f"concept difficulty {concept.difficulty}/5"]
        if linked:
            recent_year = max(question.exam_year for question in linked)
            reasons.append(f"{len(linked)} verified historical questions; latest in {recent_year}")
        else:
            reasons.append("no verified historical evidence")
        time_basis = "syllabus unit hours" if concept.estimated_minutes else "difficulty estimate"
        reasons.append(f"estimated {estimate} minutes from {time_basis}")
        if scheduled_minutes < estimate:
            reasons.append(f"preview schedules {scheduled_minutes} of {estimate} minutes within current capacity")
        for chunk_index, (scheduled_day, chunk_minutes) in enumerate(chunks, start=1):
            segment_reasons = [*reasons, f"study segment {chunk_index} of {len(chunks)}"] if len(chunks) > 1 else reasons
            result.append(RoadmapItem(id=f"plan-{sequence}", concept_id=concept.id, concept_name=concept.name, scheduled_date=date.today() + timedelta(days=scheduled_day), minutes=chunk_minutes, status="planned", reason=" · ".join(segment_reasons), evidence_question_ids=[question.id for question in linked]))
            sequence += 1
        if scheduled_minutes < estimate:
            break
    return result


def _has_cycle(graph: dict[str, list[str]]) -> bool:
    """Return whether prerequisite edges contain a directed cycle."""
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        """Detect a back edge while tracking the active and fully explored nodes."""
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
