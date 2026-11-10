"""Owned, source-aware course and semester roadmap endpoints."""

import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import exists, or_, select, update
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.infrastructure.cache import redis_cache
from app.models import Concept, ConceptPrerequisite, Course, HistoricalExamQuestion, Resource, StudyPlan, StudyPlanItem, StudyPlanRevision, SyllabusRecord, SyllabusVersion, TopicProgress, User, utc_now
from app.schemas.learning import RoadmapItem, RoadmapItemUpdate, RoadmapRequest, SemesterRoadmapRequest, StudyPlanResponse, StudyPlanRevisionResponse
from app.services.audit import record_event
from ml.graph.concept_prioritizer import ConceptPriorityInput, QuestionEvidence, prioritize_with_dependencies
from ml.scheduling.course_roadmap import ActivityDemand, ROADMAP_SESSION_ALGORITHM_VERSION, ScheduledActivity, build_concept_demands, schedule_activity_demands

router = APIRouter()


def _owned_course(db: Session, user: User, course_id: str) -> Course:
    """Resolve one course without revealing another learner's identifiers."""
    course = db.scalar(select(Course).where(Course.id == course_id, Course.owner_id == user.id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def _require_processed_syllabus(db: Session, course_id: str) -> None:
    """Reject persisted plans that do not have a processed private syllabus source."""
    version_id = db.scalar(
        select(SyllabusVersion.id)
        .join(Resource, Resource.id == SyllabusVersion.source_resource_id)
        .where(
            SyllabusVersion.course_id == course_id,
            Resource.kind == "syllabus_pdf",
            Resource.processing_status == "processed",
        )
        .limit(1)
    )
    if version_id is None:
        raise HTTPException(status_code=409, detail="Upload and process a syllabus copy, then generate its concept map before creating a roadmap")


def _current_concepts(db: Session, course_id: str) -> list[Concept]:
    """Return incomplete current-version concepts backed by verified records when records exist."""
    records_exist = exists(select(SyllabusRecord.id).where(SyllabusRecord.mapped_concept_id == Concept.id, SyllabusRecord.syllabus_version_id == Concept.syllabus_version_id))
    records_verified = exists(select(SyllabusRecord.id).where(SyllabusRecord.mapped_concept_id == Concept.id, SyllabusRecord.syllabus_version_id == Concept.syllabus_version_id, SyllabusRecord.review_status == "verified"))
    return list(db.scalars(select(Concept).where(
        Concept.course_id == course_id,
        Concept.status != "completed",
        Concept.syllabus_version_id.is_not(None),
        or_(~records_exist, records_verified),
    )).all())


def _reviewed_profile(db: Session, concepts: list[Concept], require_review: bool) -> tuple[dict[str, object], SyllabusVersion | None]:
    """Use profile metadata only after review, optionally blocking persisted generation until then."""
    version_ids = {concept.syllabus_version_id for concept in concepts if concept.syllabus_version_id}
    if not version_ids:
        return {}, None
    version = db.scalar(select(SyllabusVersion).where(SyllabusVersion.id.in_(version_ids)).order_by(SyllabusVersion.created_at.desc()).limit(1))
    if version is None or not version.roadmap_profile:
        return {}, version
    if version.roadmap_profile_status != "verified":
        if require_review:
            raise HTTPException(status_code=409, detail="Review and verify the extracted course roadmap profile before generating a persisted plan")
        return {}, version
    return version.roadmap_profile, version


def _assessment_scope(profile: dict[str, object], concept: Concept) -> str:
    """Resolve a concept's source-declared CIE/SEE scope without inferring missing exclusions."""
    raw_units = profile.get("units", [])
    if not isinstance(raw_units, list):
        return "both"
    for raw_unit in raw_units:
        if not isinstance(raw_unit, dict):
            continue
        same_sequence = concept.unit_sequence is not None and raw_unit.get("sequence") == concept.unit_sequence
        same_label = concept.unit_label is not None and str(raw_unit.get("label", "")).casefold() == concept.unit_label.split()[0].casefold()
        if same_sequence or same_label:
            scope = str(raw_unit.get("assessment_scope", "both"))
            return scope if scope in {"both", "cie_only", "see_only"} else "both"
    return "both"


def _profile_has_workload(profile: dict[str, object]) -> bool:
    """Return whether a reviewed profile contains positive modality or unit-hour evidence."""
    raw_modalities = profile.get("modality_hours", {})
    if isinstance(raw_modalities, dict) and any(
        isinstance(value, (int, float)) and value > 0 for value in raw_modalities.values()
    ):
        return True
    raw_units = profile.get("units", [])
    return isinstance(raw_units, list) and any(
        isinstance(unit, dict)
        and isinstance(unit.get("hours"), (int, float))
        and float(unit["hours"]) > 0
        for unit in raw_units
    )


def _question_evidence(db: Session, course_id: str) -> tuple[dict[str, list[HistoricalExamQuestion]], dict[str, list[HistoricalExamQuestion]]]:
    """Separate reviewed main-question priority evidence from Part-A retrieval evidence."""
    main: dict[str, list[HistoricalExamQuestion]] = {}
    quiz: dict[str, list[HistoricalExamQuestion]] = {}
    questions = db.scalars(select(HistoricalExamQuestion).where(
        HistoricalExamQuestion.course_id == course_id,
        HistoricalExamQuestion.review_status == "verified",
        HistoricalExamQuestion.concept_id.is_not(None),
    )).all()
    for question in questions:
        target = quiz if question.question_kind == "quiz" else main
        target.setdefault(question.concept_id or "", []).append(question)
    return main, quiz


def _revision_demands(
    course: Course,
    ordered: list[Concept],
    main_evidence: dict[str, list[HistoricalExamQuestion]],
    profile: dict[str, object],
    version: SyllabusVersion | None,
    revision_minutes: int,
) -> list[ActivityDemand]:
    """Append explicit end-of-plan revision blocks across the highest-priority concepts."""
    if revision_minutes <= 0 or not ordered:
        return []
    demands: list[ActivityDemand] = []
    remaining = revision_minutes
    index = 0
    candidates = ordered[: min(4, len(ordered))]
    while remaining > 0:
        concept = candidates[index % len(candidates)]
        minutes = min(45, remaining)
        questions = main_evidence.get(concept.id, [])
        demands.append(ActivityDemand(
            demand_id=f"{course.id}-revision-{index}",
            course_id=course.id,
            course_code=course.code,
            course_title=course.title,
            concept_id=concept.id,
            concept_name=concept.name,
            syllabus_version_id=version.id if version else concept.syllabus_version_id,
            unit_label=concept.unit_label,
            source_page=concept.source_page,
            assessment_scope=_assessment_scope(profile, concept),
            activity_type="final_revision",
            modality="self_study",
            minutes=minutes,
            reason="Reserved end-of-plan revision after source-ordered coverage",
            evidence_question_ids=tuple(question.id for question in questions),
        ))
        remaining -= minutes
        index += 1
    return demands


def _course_demands(
    db: Session,
    user: User,
    course: Course,
    *,
    mode: str,
    revision_minutes: int,
    require_profile_review: bool,
) -> list[ActivityDemand]:
    """Build dependency-safe, assessment-aware activity demands for one owned course."""
    concepts = _current_concepts(db, course.id)
    if not concepts:
        return []
    profile, version = _reviewed_profile(db, concepts, require_profile_review)
    course_type = str(profile.get("course_type", "generic")) if profile else "generic"
    profile_has_workload = _profile_has_workload(profile)
    edges = db.scalars(select(ConceptPrerequisite).join(Concept, Concept.id == ConceptPrerequisite.concept_id).where(Concept.course_id == course.id, ConceptPrerequisite.status == "accepted")).all()
    progress = {item.concept_id: item for item in db.scalars(select(TopicProgress).where(TopicProgress.user_id == user.id, TopicProgress.concept_id.in_([item.id for item in concepts]))).all()}
    main_evidence, quiz_evidence = _question_evidence(db, course.id)
    by_id = {concept.id: concept for concept in concepts}
    prerequisites: dict[str, list[str]] = {}
    for concept in concepts:
        accepted = [edge.prerequisite_id for edge in edges if edge.concept_id == concept.id and edge.prerequisite_id in by_id]
        if concept.parent_concept_id in by_id and concept.parent_concept_id not in accepted:
            accepted.append(concept.parent_concept_id)
        prerequisites[concept.id] = accepted
    priority_inputs = [
        ConceptPriorityInput(
            concept_id=concept.id,
            name=concept.name,
            difficulty=concept.difficulty,
            mastery_score=progress[concept.id].score if concept.id in progress else None,
            source_page=concept.source_page,
            unit_label=concept.unit_label,
            unit_sequence=concept.unit_sequence,
            evidence=tuple(QuestionEvidence(question.exam_year, question.marks) for question in main_evidence.get(concept.id, [])),
        )
        for concept in concepts
    ]
    try:
        decisions = prioritize_with_dependencies(priority_inputs, prerequisites, current_year=date.today().year)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Cannot generate a roadmap: {exc}") from exc
    decision_by_id = {decision.concept_id: decision for decision in decisions}
    ordered = [by_id[decision.concept_id] for decision in decisions]
    demands: list[ActivityDemand] = []
    included_concepts: list[Concept] = []
    for position, concept in enumerate(ordered):
        decision = decision_by_id[concept.id]
        main_questions = main_evidence.get(concept.id, [])
        quiz_questions = quiz_evidence.get(concept.id, [])
        reasons = ["Prerequisites and syllabus unit order are satisfied", *decision.reasons]
        if main_questions:
            reasons.append(f"latest reviewed main question in {max(question.exam_year for question in main_questions)}")
        if quiz_questions:
            reasons.append(f"{len(quiz_questions)} reviewed Part-A retrieval questions")
        estimate = concept.estimated_minutes or (25 + concept.difficulty * 10)
        estimate_source = (
            "reviewed syllabus workload"
            if profile_has_workload
            else "stored concept estimate"
            if concept.estimated_minutes is not None
            else "difficulty fallback"
        )
        reasons.append(f"estimated {estimate} minutes from {estimate_source}")
        concept_demands = build_concept_demands(
            demand_prefix=f"{course.id}-{position}",
            course_id=course.id,
            course_code=course.code,
            course_title=course.title,
            course_type=course_type,
            concept_id=concept.id,
            concept_name=concept.name,
            syllabus_version_id=concept.syllabus_version_id,
            unit_label=concept.unit_label,
            source_page=concept.source_page,
            assessment_scope=_assessment_scope(profile, concept),
            base_minutes=estimate,
            mastery_score=progress[concept.id].score if concept.id in progress else None,
            mode=mode,
            reason=" · ".join(reasons),
            main_question_ids=[question.id for question in main_questions],
            quiz_question_ids=[question.id for question in quiz_questions],
        )
        if concept_demands:
            included_concepts.append(concept)
            demands.extend(concept_demands)
    demands.extend(_revision_demands(course, included_concepts, main_evidence, profile, version, revision_minutes))
    return demands


def _schedule(
    demands_by_course: dict[str, list[ActivityDemand]],
    *,
    start_date: date,
    target_date: date,
    daily_minutes: int,
    unavailable_weekdays: list[int],
    allow_partial: bool,
) -> list[ScheduledActivity]:
    """Translate scheduler validation failures into stable API validation responses."""
    try:
        return schedule_activity_demands(
            demands_by_course,
            start_date=start_date,
            target_date=target_date,
            daily_minutes=daily_minutes,
            unavailable_weekdays=unavailable_weekdays,
            allow_partial=allow_partial,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc).capitalize()) from exc


def _preview_items(scheduled: list[ScheduledActivity], demands: list[ActivityDemand]) -> list[RoadmapItem]:
    """Convert scheduled segments to non-persisted response items and explain partial previews."""
    required = {item.demand_id: item.minutes for item in demands}
    allocated: dict[str, int] = {}
    for item in scheduled:
        allocated[item.demand_id] = allocated.get(item.demand_id, 0) + item.minutes
    result: list[RoadmapItem] = []
    for index, item in enumerate(scheduled):
        reason = item.reason
        if allocated[item.demand_id] < required[item.demand_id]:
            reason = f"{reason} · preview schedules {allocated[item.demand_id]} of {required[item.demand_id]} minutes within current capacity"
        result.append(RoadmapItem(
            id=f"preview-{index}",
            course_id=item.course_id,
            course_code=item.course_code,
            course_title=item.course_title,
            concept_id=item.concept_id,
            concept_name=item.concept_name,
            scheduled_date=item.scheduled_date,
            minutes=item.minutes,
            status="planned",
            reason=reason,
            activity_type=item.activity_type,
            modality=item.modality,
            unit_label=item.unit_label,
            source_page=item.source_page,
            assessment_scope=item.assessment_scope,
            syllabus_version_id=item.syllabus_version_id,
            evidence_question_ids=list(item.evidence_question_ids),
        ))
    scheduled_total = sum(allocated.values())
    required_total = sum(required.values())
    if result and scheduled_total < required_total:
        result[-1].reason = (
            f"{result[-1].reason} · preview covers {scheduled_total} of {required_total} total minutes; "
            "later activities remain unscheduled"
        )
    return result


def _persist_plan(
    db: Session,
    user: User,
    scheduled: list[ScheduledActivity],
    *,
    scope_type: str,
    mode: str,
    course: Course | None,
    program_code: str | None,
    scheme_year: int | None,
    semester: int | None,
    start_date: date,
    target_date: date,
    daily_minutes: int,
    revision_minutes: int,
    unavailable_weekdays: list[int],
) -> StudyPlanResponse:
    """Supersede the matching active plan, persist typed items, and snapshot the revision."""
    active = update(StudyPlan).where(StudyPlan.user_id == user.id, StudyPlan.scope_type == scope_type, StudyPlan.status == "active")
    if scope_type == "course" and course is not None:
        active = active.where(StudyPlan.course_id == course.id)
    else:
        active = active.where(StudyPlan.program_code == program_code, StudyPlan.scheme_year == scheme_year, StudyPlan.semester == semester)
    db.execute(active.values(status="superseded"))
    plan = StudyPlan(
        user_id=user.id,
        course_id=course.id if course else None,
        scope_type=scope_type,
        mode=mode,
        start_date=start_date,
        target_date=target_date,
        daily_minutes=daily_minutes,
        revision_minutes=revision_minutes,
        program_code=program_code,
        scheme_year=scheme_year,
        semester=semester,
        algorithm_version=ROADMAP_SESSION_ALGORITHM_VERSION,
    )
    plan.unavailable_weekdays = unavailable_weekdays
    db.add(plan)
    db.flush()
    items: list[RoadmapItem] = []
    for sequence, item in enumerate(scheduled):
        stored = StudyPlanItem(
            plan_id=plan.id,
            concept_id=item.concept_id,
            course_id=item.course_id,
            syllabus_version_id=item.syllabus_version_id,
            scheduled_date=item.scheduled_date,
            minutes=item.minutes,
            sequence=sequence,
            activity_type=item.activity_type,
            modality=item.modality,
            unit_label=item.unit_label,
            source_page=item.source_page,
            assessment_scope=item.assessment_scope,
            explanation=item.reason,
        )
        stored.evidence_question_ids = list(item.evidence_question_ids)
        db.add(stored)
        db.flush()
        items.append(RoadmapItem(
            id=stored.id,
            course_id=item.course_id,
            course_code=item.course_code,
            course_title=item.course_title,
            concept_id=item.concept_id,
            concept_name=item.concept_name,
            scheduled_date=item.scheduled_date,
            minutes=item.minutes,
            status=stored.status,
            reason=item.reason,
            activity_type=item.activity_type,
            modality=item.modality,
            unit_label=item.unit_label,
            source_page=item.source_page,
            assessment_scope=item.assessment_scope,
            syllabus_version_id=item.syllabus_version_id,
            evidence_question_ids=list(item.evidence_question_ids),
        ))
    previous_revisions = db.scalars(select(StudyPlanRevision).join(StudyPlan, StudyPlan.id == StudyPlanRevision.plan_id).where(StudyPlan.user_id == user.id)).all()
    revision = StudyPlanRevision(
        plan_id=plan.id,
        revision_number=len(previous_revisions) + 1,
        event="generated",
        snapshot=json.dumps([item.model_dump(mode="json") for item in items], sort_keys=True),
    )
    db.add(revision)
    record_event(db, "roadmap_generated", user.id, metadata={"scope_type": scope_type, "course_id": plan.course_id, "plan_id": plan.id, "revision": revision.revision_number, "mode": mode})
    db.commit()
    return StudyPlanResponse(
        id=plan.id,
        scope_type=scope_type,
        mode=mode,
        course_id=plan.course_id,
        program_code=program_code,
        scheme_year=scheme_year,
        semester=semester,
        start_date=start_date,
        target_date=target_date,
        daily_minutes=daily_minutes,
        revision_minutes=revision_minutes,
        unavailable_weekdays=plan.unavailable_weekdays,
        items=items,
    )


def _stored_plan_response(db: Session, plan: StudyPlan) -> StudyPlanResponse:
    """Rehydrate one owned persisted plan with current session status and display metadata."""
    stored_items = list(db.scalars(
        select(StudyPlanItem)
        .where(StudyPlanItem.plan_id == plan.id)
        .order_by(StudyPlanItem.sequence)
    ).all())
    course_ids = {item.course_id for item in stored_items}
    concept_ids = {item.concept_id for item in stored_items}
    courses = {
        item.id: item
        for item in db.scalars(select(Course).where(Course.id.in_(course_ids))).all()
    } if course_ids else {}
    concepts = {
        item.id: item
        for item in db.scalars(select(Concept).where(Concept.id.in_(concept_ids))).all()
    } if concept_ids else {}
    items = [
        RoadmapItem(
            id=item.id,
            course_id=item.course_id,
            course_code=courses[item.course_id].code,
            course_title=courses[item.course_id].title,
            concept_id=item.concept_id,
            concept_name=concepts[item.concept_id].name,
            scheduled_date=item.scheduled_date,
            minutes=item.minutes,
            status=item.status,
            reason=item.explanation,
            activity_type=item.activity_type,
            modality=item.modality,
            unit_label=item.unit_label,
            source_page=item.source_page,
            assessment_scope=item.assessment_scope,
            syllabus_version_id=item.syllabus_version_id,
            evidence_question_ids=item.evidence_question_ids,
        )
        for item in stored_items
        if item.course_id in courses and item.concept_id in concepts
    ]
    return StudyPlanResponse(
        id=plan.id,
        scope_type=plan.scope_type,
        mode=plan.mode,
        course_id=plan.course_id,
        program_code=plan.program_code,
        scheme_year=plan.scheme_year,
        semester=plan.semester,
        start_date=plan.start_date,
        target_date=plan.target_date,
        daily_minutes=plan.daily_minutes,
        revision_minutes=plan.revision_minutes,
        unavailable_weekdays=plan.unavailable_weekdays,
        items=items,
    )


@router.get("", response_model=list[RoadmapItem])
def get_roadmap(course_id: str = Query(...), days: int = Query(default=14, ge=1, le=90), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[RoadmapItem]:
    """Preview a generic-safe schedule without allowing unreviewed profile metadata to control it."""
    course = _owned_course(db, current_user, course_id)
    return generate_items(db, current_user, course.id, date.today() + timedelta(days=days), 60, allow_partial=True)


@router.get("/active", response_model=StudyPlanResponse | None)
def get_active_roadmap(
    course_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudyPlanResponse | None:
    """Return the newest active owned plan, optionally including a selected course."""
    query = select(StudyPlan).where(StudyPlan.user_id == current_user.id, StudyPlan.status == "active")
    if course_id:
        course = _owned_course(db, current_user, course_id)
        semester_contains_course = exists(select(StudyPlanItem.id).where(
            StudyPlanItem.plan_id == StudyPlan.id,
            StudyPlanItem.course_id == course.id,
        ))
        query = query.where(or_(StudyPlan.course_id == course.id, semester_contains_course))
    plan = db.scalar(query.order_by(StudyPlan.created_at.desc()).limit(1))
    return _stored_plan_response(db, plan) if plan is not None else None


@router.post("/generate", response_model=StudyPlanResponse, status_code=201)
def generate_roadmap(payload: RoadmapRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> StudyPlanResponse:
    """Persist a reviewed, activity-aware course plan under the supplied capacity."""
    course = _owned_course(db, current_user, payload.course_id)
    _require_processed_syllabus(db, course.id)
    start_date = payload.start_date or date.today()
    if start_date < date.today() or payload.target_date < date.today():
        raise HTTPException(status_code=422, detail="Start and target dates must be today or later")
    demands = _course_demands(db, current_user, course, mode=payload.mode, revision_minutes=payload.revision_minutes, require_profile_review=True)
    if not demands:
        raise HTTPException(status_code=409, detail="Generate and verify syllabus-derived concepts before creating a roadmap")
    scheduled = _schedule({course.id: demands}, start_date=start_date, target_date=payload.target_date, daily_minutes=payload.daily_minutes, unavailable_weekdays=payload.unavailable_weekdays, allow_partial=False)
    return _persist_plan(
        db,
        current_user,
        scheduled,
        scope_type="course",
        mode=payload.mode,
        course=course,
        program_code=course.program_code,
        scheme_year=course.scheme_year,
        semester=course.semester,
        start_date=start_date,
        target_date=payload.target_date,
        daily_minutes=payload.daily_minutes,
        revision_minutes=payload.revision_minutes,
        unavailable_weekdays=payload.unavailable_weekdays,
    )


@router.post("/semester/generate", response_model=StudyPlanResponse, status_code=201)
def generate_semester_roadmap(payload: SemesterRoadmapRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> StudyPlanResponse:
    """Interleave explicitly selected same-scope courses without inferring institutional option choices."""
    courses = list(db.scalars(select(Course).where(Course.owner_id == current_user.id, Course.id.in_(payload.course_ids))).all())
    if len(courses) != len(payload.course_ids):
        raise HTTPException(status_code=404, detail="One or more selected courses were not found")
    scopes = {(course.program_code, course.scheme_year, course.semester) for course in courses}
    if len(scopes) != 1 or any(value is None for value in next(iter(scopes))):
        raise HTTPException(status_code=422, detail="Semester plans require explicitly selected courses from one branch, scheme, and semester")
    program_code, scheme_year, semester = next(iter(scopes))
    start_date = payload.start_date or date.today()
    if start_date < date.today() or payload.target_date < date.today():
        raise HTTPException(status_code=422, detail="Start and target dates must be today or later")
    base_revision, remainder = divmod(payload.revision_minutes, len(courses))
    demands_by_course: dict[str, list[ActivityDemand]] = {}
    for index, course in enumerate(sorted(courses, key=lambda item: (item.code, item.id))):
        _require_processed_syllabus(db, course.id)
        share = base_revision + (1 if index < remainder else 0)
        demands = _course_demands(db, current_user, course, mode=payload.mode, revision_minutes=share, require_profile_review=True)
        if not demands:
            raise HTTPException(status_code=409, detail=f"{course.code} has no verified current syllabus concepts")
        demands_by_course[course.id] = demands
    scheduled = _schedule(demands_by_course, start_date=start_date, target_date=payload.target_date, daily_minutes=payload.daily_minutes, unavailable_weekdays=payload.unavailable_weekdays, allow_partial=False)
    return _persist_plan(
        db,
        current_user,
        scheduled,
        scope_type="semester",
        mode=payload.mode,
        course=None,
        program_code=program_code,
        scheme_year=scheme_year,
        semester=semester,
        start_date=start_date,
        target_date=payload.target_date,
        daily_minutes=payload.daily_minutes,
        revision_minutes=payload.revision_minutes,
        unavailable_weekdays=payload.unavailable_weekdays,
    )


@router.get("/history", response_model=list[StudyPlanRevisionResponse])
def roadmap_history(course_id: str | None = Query(default=None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[StudyPlanRevisionResponse]:
    """List the authenticated learner's roadmap revision history, optionally by course."""
    query = select(StudyPlanRevision).join(StudyPlan, StudyPlan.id == StudyPlanRevision.plan_id).where(StudyPlan.user_id == current_user.id)
    if course_id:
        semester_contains_course = exists(select(StudyPlanItem.id).where(
            StudyPlanItem.plan_id == StudyPlan.id,
            StudyPlanItem.course_id == course_id,
        ))
        query = query.where(or_(StudyPlan.course_id == course_id, semester_contains_course))
    revisions = db.scalars(query.order_by(StudyPlanRevision.created_at.desc())).all()
    return [StudyPlanRevisionResponse(id=item.id, plan_id=item.plan_id, revision_number=item.revision_number, event=item.event, created_at=item.created_at.isoformat()) for item in revisions]


@router.patch("/items/{item_id}")
def update_roadmap_item(item_id: str, payload: RoadmapItemUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Update one owned session and feed optional completion mastery back into future plans."""
    item = db.scalar(select(StudyPlanItem).join(StudyPlan, StudyPlan.id == StudyPlanItem.plan_id).where(StudyPlanItem.id == item_id, StudyPlan.user_id == current_user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Roadmap item not found")
    item.status = payload.status
    db.flush()
    remaining_session = db.scalar(select(StudyPlanItem.id).where(
        StudyPlanItem.plan_id == item.plan_id,
        StudyPlanItem.concept_id == item.concept_id,
        StudyPlanItem.status != "completed",
    ).limit(1))
    completed_session = db.scalar(select(StudyPlanItem.id).where(
        StudyPlanItem.plan_id == item.plan_id,
        StudyPlanItem.concept_id == item.concept_id,
        StudyPlanItem.status == "completed",
    ).limit(1))
    progress = db.scalar(select(TopicProgress).where(TopicProgress.user_id == current_user.id, TopicProgress.concept_id == item.concept_id))
    if payload.status == "completed" or progress is not None:
        if progress is None:
            progress = TopicProgress(user_id=current_user.id, concept_id=item.concept_id)
            db.add(progress)
        progress.completed = remaining_session is None
        if payload.mastery_score is not None:
            progress.score = payload.mastery_score
        if payload.status == "completed":
            progress.last_studied_at = utc_now()
    concept = db.get(Concept, item.concept_id)
    if concept is not None:
        if remaining_session is None:
            concept.status = "completed"
        elif completed_session is not None:
            concept.status = "in_progress"
        else:
            concept.status = "not_started"
    record_event(db, "roadmap_item_updated", current_user.id, metadata={"plan_id": item.plan_id, "item_id": item.id, "status": payload.status})
    db.commit()
    if item.course_id:
        redis_cache.delete(f"courses:{current_user.id}")
        redis_cache.delete(f"concepts:{current_user.id}:{item.course_id}")
    redis_cache.delete(f"concepts:{current_user.id}:all")
    return {"id": item.id, "status": item.status, "concept_id": item.concept_id, "mastery_score": payload.mastery_score}


def generate_items(
    db: Session,
    user: User,
    course_id: str,
    target_date: date,
    daily_minutes: int,
    revision_minutes: int = 0,
    allow_partial: bool = False,
    *,
    start_date: date | None = None,
    mode: str = "full_term",
    unavailable_weekdays: list[int] | None = None,
) -> list[RoadmapItem]:
    """Generate a backward-compatible course preview using only reviewed profile metadata."""
    course = _owned_course(db, user, course_id)
    demands = _course_demands(db, user, course, mode=mode, revision_minutes=revision_minutes, require_profile_review=False)
    if not demands:
        return []
    beginning = start_date or date.today()
    scheduled = _schedule({course.id: demands}, start_date=beginning, target_date=target_date, daily_minutes=daily_minutes, unavailable_weekdays=unavailable_weekdays or [], allow_partial=allow_partial)
    return _preview_items(scheduled, demands)


def _has_cycle(graph: dict[str, list[str]]) -> bool:
    """Return whether prerequisite edges contain a directed cycle for compatibility callers."""
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        """Detect a back edge while tracking active and fully explored nodes."""
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
