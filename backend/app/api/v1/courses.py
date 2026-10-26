from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Concept, Course as CourseModel, TopicProgress, User
from app.models import SyllabusVersion as SyllabusVersionModel
from app.schemas.course import Course, CourseCreate, SyllabusVersion, SyllabusVersionCreate

router = APIRouter()


@router.get("", response_model=list[Course])
def get_courses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Course]:
    courses = db.scalars(select(CourseModel).where(CourseModel.owner_id == current_user.id)).all()
    return [Course(**course_dict(course, db, current_user.id)) for course in courses]


@router.get("/{course_id}", response_model=Course)
def get_course(course_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Course:
    course = db.scalar(select(CourseModel).where(CourseModel.id == course_id, CourseModel.owner_id == current_user.id))
    if course is None:
        raise HTTPException(404, "Course not found")
    return Course(**course_dict(course, db, current_user.id))


@router.post("", response_model=Course, status_code=201)
def create_course(payload: CourseCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Course:
    course = CourseModel(owner_id=current_user.id, **payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return Course(**course_dict(course, db, current_user.id))


def course_dict(course: CourseModel, db: Session, user_id: str) -> dict:
    concept_count = db.scalar(select(func.count(Concept.id)).where(Concept.course_id == course.id)) or 0
    completed_count = db.scalar(select(func.count(TopicProgress.id)).join(Concept, Concept.id == TopicProgress.concept_id).where(TopicProgress.user_id == user_id, TopicProgress.completed.is_(True), Concept.course_id == course.id)) or 0
    return {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "description": course.description,
        "progress": round((completed_count / concept_count) * 100) if concept_count else 0,
        "concept_count": concept_count,
    }


@router.post("/{course_id}/syllabus-versions", response_model=SyllabusVersion, status_code=201)
def create_syllabus_version(course_id: str, payload: SyllabusVersionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> SyllabusVersion:
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
    if db.scalar(select(CourseModel).where(CourseModel.id == course_id, CourseModel.owner_id == current_user.id)) is None:
        raise HTTPException(status_code=404, detail="Course not found")
    versions = db.scalars(select(SyllabusVersionModel).where(SyllabusVersionModel.course_id == course_id)).all()
    return [SyllabusVersion.model_validate(item) for item in versions]
