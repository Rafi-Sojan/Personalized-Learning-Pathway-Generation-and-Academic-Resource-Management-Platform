from fastapi import APIRouter, HTTPException

from app.repositories.in_memory import repository
from app.schemas.course import Course, CourseCreate

router = APIRouter()


@router.get("", response_model=list[Course])
def get_courses() -> list[Course]:
    return repository.clone(repository.courses)


@router.get("/{course_id}", response_model=Course)
def get_course(course_id: str) -> Course:
    course = next((item for item in repository.courses if item["id"] == course_id), None)
    if not course:
        raise HTTPException(404, "Course not found")
    return repository.clone(course)


@router.post("", response_model=Course, status_code=201)
def create_course(payload: CourseCreate) -> Course:
    course = {"id": f"course-{len(repository.courses) + 1}", **payload.model_dump(), "progress": 0, "concept_count": 0}
    repository.courses.append(course)
    return course
