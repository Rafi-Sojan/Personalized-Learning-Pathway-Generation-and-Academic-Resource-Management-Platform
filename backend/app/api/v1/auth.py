from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.session import get_db
from app.infrastructure.cache import redis_cache
from app.models import AuditEvent, Concept, ConceptPrerequisite, Course, HistoricalExamQuestion, QuizAttempt, Resource, ResourceConceptMapping, StudyPlan, StudyPlanItem, StudyPlanRevision, SyllabusRecord, SyllabusVersion, TopicProgress, User as UserModel
from app.schemas.auth import DeleteAccountRequest, LoginRequest, LoginResponse, RegisterRequest, User
from app.infrastructure.rate_limiter import enforce_rate_limit, login_limiter
from app.services.storage import storage
from app.services.audit import record_event
from fastapi import Request

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    """Authenticate an account and return a short-lived signed access token."""
    enforce_rate_limit(request, login_limiter)
    user = db.scalar(select(UserModel).where(UserModel.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return LoginResponse(access_token=create_access_token(user.id, user.token_version), user=User.model_validate(user))


@router.post("/register", response_model=LoginResponse, status_code=201)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    """Create a student account after rate limiting and email-uniqueness checks."""
    enforce_rate_limit(request, login_limiter)
    email = str(payload.email).lower()
    if db.scalar(select(UserModel).where(UserModel.email == email)):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = UserModel(email=email, name=payload.name.strip(), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return LoginResponse(access_token=create_access_token(user.id, user.token_version), user=User.model_validate(user))


@router.get("/me", response_model=User)
def me(current_user: UserModel = Depends(get_current_user)) -> User:
    """Return the identity and role resolved from the current access token."""
    return User.model_validate(current_user)


@router.post("/logout", status_code=204)
def logout(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    """Revoke previously issued tokens by incrementing the account token version."""
    current_user.token_version += 1
    record_event(db, "logout", current_user.id)
    db.commit()


@router.get("/export")
def export_account(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> JSONResponse:
    """Export the authenticated user's complete relational learning record as portable JSON."""
    courses = db.scalars(select(Course).where(Course.owner_id == current_user.id)).all()
    course_ids = [course.id for course in courses]
    concepts = db.scalars(select(Concept).where(Concept.course_id.in_(course_ids))).all() if course_ids else []
    concept_ids = [concept.id for concept in concepts]
    prerequisites = db.scalars(select(ConceptPrerequisite).where(ConceptPrerequisite.concept_id.in_(concept_ids))).all() if concept_ids else []
    progress = db.scalars(select(TopicProgress).where(TopicProgress.user_id == current_user.id)).all()
    attempts = db.scalars(select(QuizAttempt).where(QuizAttempt.user_id == current_user.id)).all()
    plans = db.scalars(select(StudyPlan).where(StudyPlan.user_id == current_user.id)).all()
    plan_ids = [plan.id for plan in plans]
    plan_items = db.scalars(select(StudyPlanItem).where(StudyPlanItem.plan_id.in_(plan_ids))).all() if plan_ids else []
    plan_revisions = db.scalars(select(StudyPlanRevision).where(StudyPlanRevision.plan_id.in_(plan_ids))).all() if plan_ids else []
    resources = db.scalars(select(Resource).where(Resource.course_id.in_(course_ids))).all() if course_ids else []
    resource_ids = [resource.id for resource in resources]
    mappings = db.scalars(select(ResourceConceptMapping).where(ResourceConceptMapping.resource_id.in_(resource_ids))).all() if resource_ids else []
    syllabus_versions = db.scalars(select(SyllabusVersion).where(SyllabusVersion.course_id.in_(course_ids))).all() if course_ids else []
    syllabus_records = db.scalars(select(SyllabusRecord).where(SyllabusRecord.course_id.in_(course_ids))).all() if course_ids else []
    historical_questions = db.scalars(select(HistoricalExamQuestion).where(HistoricalExamQuestion.course_id.in_(course_ids))).all() if course_ids else []
    audit_events = db.scalars(select(AuditEvent).where(AuditEvent.actor_id == current_user.id)).all()
    return JSONResponse({
        "user": {"id": current_user.id, "email": current_user.email, "name": current_user.name, "role": current_user.role},
        "courses": [{"id": item.id, "code": item.code, "title": item.title, "description": item.description, "program_code": item.program_code, "scheme_year": item.scheme_year, "semester": item.semester, "origin": item.origin, "catalog_course_id": item.catalog_course_id} for item in courses],
        "concepts": [{"id": item.id, "course_id": item.course_id, "name": item.name, "difficulty": item.difficulty, "status": item.status, "unit_label": item.unit_label, "source_page": item.source_page, "syllabus_version_id": item.syllabus_version_id, "parent_concept_id": item.parent_concept_id, "estimated_minutes": item.estimated_minutes} for item in concepts],
        "concept_prerequisites": [{"concept_id": item.concept_id, "prerequisite_id": item.prerequisite_id, "status": item.status, "source_page": item.source_page, "confidence": item.confidence, "rationale": item.rationale} for item in prerequisites],
        "progress": [{"concept_id": item.concept_id, "completed": item.completed, "score": item.score} for item in progress if item.concept_id in concept_ids],
        "quiz_attempts": [{"concept_id": item.concept_id, "answer_index": item.answer_index, "correct": item.correct, "score": item.score, "created_at": item.created_at.isoformat()} for item in attempts if item.concept_id in concept_ids],
        "study_plans": [{"id": item.id, "course_id": item.course_id, "target_date": item.target_date.isoformat(), "daily_minutes": item.daily_minutes, "status": item.status} for item in plans],
        "study_plan_items": [{"id": item.id, "plan_id": item.plan_id, "concept_id": item.concept_id, "scheduled_date": item.scheduled_date.isoformat(), "minutes": item.minutes, "sequence": item.sequence, "status": item.status, "explanation": item.explanation} for item in plan_items],
        "study_plan_revisions": [{"id": item.id, "plan_id": item.plan_id, "revision_number": item.revision_number, "event": item.event, "snapshot": item.snapshot, "created_at": item.created_at.isoformat()} for item in plan_revisions],
        "resources": [{"id": item.id, "course_id": item.course_id, "concept_id": item.concept_id, "title": item.title, "kind": item.kind, "url": item.url, "checksum": item.checksum, "processing_status": item.processing_status, "created_at": item.created_at.isoformat()} for item in resources],
        "resource_mappings": [{"resource_id": item.resource_id, "concept_id": item.concept_id, "confidence": item.confidence, "status": item.status, "source": item.source} for item in mappings],
        "syllabus_versions": [{"id": item.id, "course_id": item.course_id, "label": item.label, "source_resource_id": item.source_resource_id, "effective_from": item.effective_from.isoformat() if item.effective_from else None, "created_at": item.created_at.isoformat()} for item in syllabus_versions],
        "syllabus_records": [{"id": item.id, "syllabus_version_id": item.syllabus_version_id, "source_resource_id": item.source_resource_id, "course_id": item.course_id, "record_type": item.record_type, "source_page": item.source_page, "source_text": item.source_text, "normalized_text": item.normalized_text, "unit_label": item.unit_label, "parent_label": item.parent_label, "hours": item.hours, "confidence": item.confidence, "review_status": item.review_status, "mapped_concept_id": item.mapped_concept_id} for item in syllabus_records],
        "historical_exam_questions": [{"id": item.id, "course_id": item.course_id, "source": item.source, "source_document": item.source_document, "source_resource_id": item.source_resource_id, "exam_year": item.exam_year, "prompt": item.prompt, "concept_id": item.concept_id, "topic_label": item.topic_label, "difficulty": item.difficulty, "paper_part": item.paper_part, "question_kind": item.question_kind, "question_number": item.question_number, "subpart": item.subpart, "marks": item.marks, "source_page": item.source_page, "assessment_type": item.assessment_type, "question_format": item.question_format, "mapping_confidence": item.mapping_confidence, "review_status": item.review_status, "created_at": item.created_at.isoformat()} for item in historical_questions],
        "audit_events": [{"id": item.id, "event_type": item.event_type, "request_id": item.request_id, "metadata_json": item.metadata_json, "created_at": item.created_at.isoformat()} for item in audit_events],
    })


@router.post("/delete", status_code=204)
def delete_account(payload: DeleteAccountRequest, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    """Delete all confirmed-account records in foreign-key-safe order and remove private files."""
    if str(payload.confirm_email).lower() != current_user.email.lower():
        raise HTTPException(status_code=400, detail="Email confirmation does not match the account")
    user_id = current_user.id
    course_ids = [item.id for item in db.scalars(select(Course).where(Course.owner_id == current_user.id)).all()]
    concept_ids = [item.id for item in db.scalars(select(Concept).where(Concept.course_id.in_(course_ids))).all()] if course_ids else []
    owned_resources = db.scalars(select(Resource).where(Resource.course_id.in_(course_ids))).all() if course_ids else []
    owned_files = [(resource.storage_key, resource.processed_key, resource.id) for resource in owned_resources]
    resource_ids = [item.id for item in owned_resources]
    plan_ids = [item.id for item in db.scalars(select(StudyPlan).where(StudyPlan.user_id == current_user.id)).all()]
    if plan_ids:
        db.execute(delete(StudyPlanItem).where(StudyPlanItem.plan_id.in_(plan_ids)))
        db.execute(delete(StudyPlanRevision).where(StudyPlanRevision.plan_id.in_(plan_ids)))
        db.execute(delete(StudyPlan).where(StudyPlan.id.in_(plan_ids)))
    db.execute(delete(QuizAttempt).where(QuizAttempt.user_id == current_user.id))
    db.execute(delete(TopicProgress).where(TopicProgress.user_id == current_user.id))
    if course_ids:
        db.execute(delete(HistoricalExamQuestion).where(HistoricalExamQuestion.course_id.in_(course_ids)))
        db.execute(delete(SyllabusRecord).where(SyllabusRecord.course_id.in_(course_ids)))
    if resource_ids or concept_ids:
        mapping_scope = []
        if resource_ids:
            mapping_scope.append(ResourceConceptMapping.resource_id.in_(resource_ids))
        if concept_ids:
            mapping_scope.append(ResourceConceptMapping.concept_id.in_(concept_ids))
        db.execute(delete(ResourceConceptMapping).where(or_(*mapping_scope)))
    db.execute(update(ResourceConceptMapping).where(ResourceConceptMapping.reviewed_by == current_user.id).values(reviewed_by=None))
    if concept_ids:
        db.execute(delete(ConceptPrerequisite).where(or_(ConceptPrerequisite.concept_id.in_(concept_ids), ConceptPrerequisite.prerequisite_id.in_(concept_ids))))
    if course_ids:
        db.execute(update(SyllabusVersion).where(SyllabusVersion.course_id.in_(course_ids)).values(source_resource_id=None))
        db.execute(delete(Resource).where(Resource.course_id.in_(course_ids)))
    if concept_ids:
        db.execute(delete(Concept).where(Concept.id.in_(concept_ids)))
    if course_ids:
        db.execute(delete(SyllabusVersion).where(SyllabusVersion.course_id.in_(course_ids)))
        db.execute(delete(Course).where(Course.id.in_(course_ids)))
    db.execute(delete(AuditEvent).where(AuditEvent.actor_id == current_user.id))
    record_event(db, "account_deleted", None, metadata={"account_deleted": True})
    db.delete(current_user)
    db.commit()
    redis_cache.delete(f"courses:{user_id}")
    redis_cache.delete(f"concepts:{user_id}:all")
    for course_id in course_ids:
        redis_cache.delete(f"concepts:{user_id}:{course_id}")
    for storage_key, processed_key, _resource_id in owned_files:
        storage.delete(storage_key)
        storage.delete(processed_key or f"processed/{_resource_id}.txt")
