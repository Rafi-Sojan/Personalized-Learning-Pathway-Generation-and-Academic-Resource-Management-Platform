from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.session import get_db
from app.models import AuditEvent, Concept, ConceptPrerequisite, Course, QuizAttempt, Resource, ResourceConceptMapping, StudyPlan, StudyPlanItem, StudyPlanRevision, SyllabusVersion, TopicProgress, User as UserModel
from app.schemas.auth import DeleteAccountRequest, LoginRequest, LoginResponse, RegisterRequest, User
from app.infrastructure.rate_limiter import enforce_rate_limit, login_limiter
from app.services.storage import storage
from app.services.audit import record_event
from fastapi import Request

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    enforce_rate_limit(request, login_limiter)
    user = db.scalar(select(UserModel).where(UserModel.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return LoginResponse(access_token=create_access_token(user.id), user=User.model_validate(user))


@router.post("/register", response_model=LoginResponse, status_code=201)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    enforce_rate_limit(request, login_limiter)
    email = str(payload.email).lower()
    if db.scalar(select(UserModel).where(UserModel.email == email)):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = UserModel(email=email, name=payload.name.strip(), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return LoginResponse(access_token=create_access_token(user.id), user=User.model_validate(user))


@router.get("/me", response_model=User)
def me(current_user: UserModel = Depends(get_current_user)) -> User:
    return User.model_validate(current_user)


@router.get("/export")
def export_account(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> JSONResponse:
    courses = db.scalars(select(Course).where(Course.owner_id == current_user.id)).all()
    course_ids = [course.id for course in courses]
    concepts = db.scalars(select(Concept).where(Concept.course_id.in_(course_ids))).all() if course_ids else []
    concept_ids = [concept.id for concept in concepts]
    progress = db.scalars(select(TopicProgress).where(TopicProgress.user_id == current_user.id)).all()
    attempts = db.scalars(select(QuizAttempt).where(QuizAttempt.user_id == current_user.id)).all()
    plans = db.scalars(select(StudyPlan).where(StudyPlan.user_id == current_user.id)).all()
    resources = db.scalars(select(Resource).where(Resource.course_id.in_(course_ids))).all() if course_ids else []
    resource_ids = [resource.id for resource in resources]
    mappings = db.scalars(select(ResourceConceptMapping).where(ResourceConceptMapping.resource_id.in_(resource_ids))).all() if resource_ids else []
    return JSONResponse({
        "user": {"id": current_user.id, "email": current_user.email, "name": current_user.name, "role": current_user.role},
        "courses": [{"id": item.id, "code": item.code, "title": item.title, "description": item.description} for item in courses],
        "concepts": [{"id": item.id, "course_id": item.course_id, "name": item.name, "difficulty": item.difficulty, "status": item.status} for item in concepts],
        "progress": [{"concept_id": item.concept_id, "completed": item.completed, "score": item.score} for item in progress if item.concept_id in concept_ids],
        "quiz_attempts": [{"concept_id": item.concept_id, "answer_index": item.answer_index, "correct": item.correct, "score": item.score, "created_at": item.created_at.isoformat()} for item in attempts],
        "study_plans": [{"id": item.id, "course_id": item.course_id, "target_date": item.target_date.isoformat(), "daily_minutes": item.daily_minutes, "status": item.status} for item in plans],
        "resources": [{"id": item.id, "course_id": item.course_id, "concept_id": item.concept_id, "title": item.title, "kind": item.kind, "url": item.url} for item in resources],
        "resource_mappings": [{"resource_id": item.resource_id, "concept_id": item.concept_id, "confidence": item.confidence, "status": item.status, "source": item.source} for item in mappings],
    })


@router.post("/delete", status_code=204)
def delete_account(payload: DeleteAccountRequest, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    if str(payload.confirm_email).lower() != current_user.email.lower():
        raise HTTPException(status_code=400, detail="Email confirmation does not match the account")
    course_ids = [item.id for item in db.scalars(select(Course).where(Course.owner_id == current_user.id)).all()]
    concept_ids = [item.id for item in db.scalars(select(Concept).where(Concept.course_id.in_(course_ids))).all()] if course_ids else []
    owned_resources = db.scalars(select(Resource).where(Resource.course_id.in_(course_ids))).all() if course_ids else []
    owned_files = [(resource.storage_key, resource.processed_key, resource.id) for resource in owned_resources]
    plan_ids = [item.id for item in db.scalars(select(StudyPlan).where(StudyPlan.user_id == current_user.id)).all()]
    if plan_ids:
        db.execute(delete(StudyPlanItem).where(StudyPlanItem.plan_id.in_(plan_ids)))
        db.execute(delete(StudyPlanRevision).where(StudyPlanRevision.plan_id.in_(plan_ids)))
        db.execute(delete(StudyPlan).where(StudyPlan.id.in_(plan_ids)))
    db.execute(delete(QuizAttempt).where(QuizAttempt.user_id == current_user.id))
    db.execute(delete(TopicProgress).where(TopicProgress.user_id == current_user.id))
    if course_ids:
        db.execute(delete(ConceptPrerequisite).where((ConceptPrerequisite.concept_id.in_(concept_ids)) | (ConceptPrerequisite.prerequisite_id.in_(concept_ids))))
        db.execute(delete(SyllabusVersion).where(SyllabusVersion.course_id.in_(course_ids)))
        resource_ids = [item.id for item in owned_resources]
        if resource_ids:
            db.execute(delete(ResourceConceptMapping).where(ResourceConceptMapping.resource_id.in_(resource_ids)))
        db.execute(delete(Resource).where(Resource.course_id.in_(course_ids)))
    if concept_ids:
        db.execute(delete(Concept).where(Concept.id.in_(concept_ids)))
    if course_ids:
        db.execute(delete(Course).where(Course.id.in_(course_ids)))
    db.execute(delete(AuditEvent).where(AuditEvent.actor_id == current_user.id))
    record_event(db, "account_deleted", None, metadata={"account_deleted": True})
    db.delete(current_user)
    db.commit()
    for storage_key, processed_key, _resource_id in owned_files:
        storage.delete(storage_key)
        storage.delete(processed_key or f"processed/{_resource_id}.txt")
