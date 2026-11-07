from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.infrastructure.cache import get_json, set_json, redis_cache
from app.models import Concept, Course as CourseModel, Resource, TopicProgress, User
from app.models import SyllabusVersion as SyllabusVersionModel
from app.schemas.course import Course, CourseCreate, SyllabusVersion, SyllabusVersionCreate
from app.services.audit import record_event
from app.services.rvce_catalog import get_rvce_catalog

router = APIRouter()


@router.get("", response_model=list[Course])
def get_courses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Course]:
    """List the authenticated user's courses with current mapped-topic counts and short-lived caching."""
    cached = get_json(f"courses:{current_user.id}")
    if isinstance(cached, list):
        return [Course(**item) for item in cached]
    courses = db.scalars(select(CourseModel).where(CourseModel.owner_id == current_user.id)).all()
    result = [Course(**course_dict(course, db, current_user.id)) for course in courses]
    set_json(f"courses:{current_user.id}", [item.model_dump() for item in result], expire=30)
    return result


@router.get("/{course_id}", response_model=Course)
def get_course(course_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Course:
    """Return one owned course or a not-found response when it is outside the user's scope."""
    course = db.scalar(select(CourseModel).where(CourseModel.id == course_id, CourseModel.owner_id == current_user.id))
    if course is None:
        raise HTTPException(404, "Course not found")
    return Course(**course_dict(course, db, current_user.id))


@router.post("", response_model=Course, status_code=201)
def create_course(payload: CourseCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Course:
    """Create a personal subject workspace under an optional validated RVCE academic scope."""
    program_code, scheme_year, semester = _validated_scope(payload)
    code = payload.code.strip().upper()
    existing = db.scalars(select(CourseModel).where(CourseModel.owner_id == current_user.id, CourseModel.code == code)).all()
    if any((item.program_code, item.scheme_year, item.semester) == (program_code, scheme_year, semester) for item in existing):
        raise HTTPException(status_code=409, detail="This subject already exists in the selected branch, scheme, and semester")
    course = CourseModel(
        owner_id=current_user.id,
        code=code,
        title=payload.title.strip(),
        description=payload.description.strip(),
        program_code=program_code,
        scheme_year=scheme_year,
        semester=semester,
        origin="personal",
    )
    db.add(course)
    record_event(db, "personal_course_created", current_user.id, metadata={"course_code": code, "program_code": program_code, "scheme_year": scheme_year, "semester": semester})
    db.commit()
    db.refresh(course)
    redis_cache.delete(f"courses:{current_user.id}")
    return Course(**course_dict(course, db, current_user.id))


def _validated_scope(payload: CourseCreate) -> tuple[str | None, int | None, int | None]:
    """Normalize aliases and reject branch/scheme combinations absent from the RVCE manifest."""
    if payload.program_code is None:
        return None, None, None
    catalog = get_rvce_catalog()
    raw_code = payload.program_code.strip().upper()
    aliases = {alias.upper(): item["code"] for item in catalog["program_schemes"] for alias in item.get("aliases", [])}
    program_code = aliases.get(raw_code, raw_code)
    program = next((item for item in catalog["program_schemes"] if item["code"] == program_code), None)
    if program is None:
        raise HTTPException(status_code=422, detail="Program code is not in the RVCE catalog")
    if payload.scheme_year is None or payload.semester is None:
        raise HTTPException(status_code=422, detail="Program, scheme, and semester must be supplied together")
    allowed_schemes = set(catalog["common_first_year_schemes"] if payload.semester <= 2 else program["schemes"])
    if payload.scheme_year not in allowed_schemes:
        raise HTTPException(status_code=422, detail="Scheme is not catalogued for this RVCE branch and semester")
    return program_code, payload.scheme_year, payload.semester


def course_dict(course: CourseModel, db: Session, user_id: str) -> dict:
    """Build the course response fields from stored data and the owner's progress."""
    mapped_concepts = Concept.syllabus_version_id.is_not(None)
    concept_count = db.scalar(select(func.count(Concept.id)).where(Concept.course_id == course.id, mapped_concepts)) or 0
    completed_count = db.scalar(select(func.count(TopicProgress.id)).join(Concept, Concept.id == TopicProgress.concept_id).where(TopicProgress.user_id == user_id, TopicProgress.completed.is_(True), Concept.course_id == course.id, mapped_concepts)) or 0
    syllabus_source_count = db.scalar(select(func.count(Resource.id)).where(Resource.course_id == course.id, Resource.kind == "syllabus_pdf")) or 0
    syllabus_status = db.scalar(select(Resource.processing_status).where(Resource.course_id == course.id, Resource.kind == "syllabus_pdf").order_by(Resource.created_at.desc()).limit(1)) or "not_uploaded"
    return {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "description": course.description,
        "progress": round((completed_count / concept_count) * 100) if concept_count else 0,
        "concept_count": concept_count,
        "program_code": course.program_code,
        "scheme_year": course.scheme_year,
        "semester": course.semester,
        "origin": course.origin,
        "catalog_course_id": course.catalog_course_id,
        "syllabus_source_count": syllabus_source_count,
        "syllabus_status": syllabus_status,
    }


@router.post("/{course_id}/syllabus-versions", response_model=SyllabusVersion, status_code=201)
def create_syllabus_version(course_id: str, payload: SyllabusVersionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> SyllabusVersion:
    """Add a syllabus version after confirming that the parent course belongs to the caller."""
    course = db.scalar(select(CourseModel).where(CourseModel.id == course_id, CourseModel.owner_id == current_user.id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    version = SyllabusVersionModel(course_id=course_id, label=payload.label, effective_from=payload.effective_from)
    db.add(version)
    db.commit()
    db.refresh(version)
    return SyllabusVersion.model_validate(version)


@router.get("/{course_id}/syllabus-versions", response_model=list[SyllabusVersion])
def list_syllabus_versions(course_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[SyllabusVersion]:
    """List versions only after verifying ownership of the requested course."""
    if db.scalar(select(CourseModel).where(CourseModel.id == course_id, CourseModel.owner_id == current_user.id)) is None:
        raise HTTPException(status_code=404, detail="Course not found")
    versions = db.scalars(select(SyllabusVersionModel).where(SyllabusVersionModel.course_id == course_id)).all()
    return [SyllabusVersion.model_validate(item) for item in versions]
