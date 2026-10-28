import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.session import get_db
from app.models import RvceSyllabusCourse, User
from app.schemas.rvce import RvceSyllabusCourseCreate, RvceSyllabusCourseResponse
from app.services.rvce_catalog import get_rvce_catalog
from app.services.audit import record_event


router = APIRouter()


@router.get("/rvce")
def get_rvce_catalog_metadata() -> dict:
    """Return provenance-aware RVCE program and scheme metadata."""
    return get_rvce_catalog()


def _response(course: RvceSyllabusCourse) -> RvceSyllabusCourseResponse:
    return RvceSyllabusCourseResponse(
        id=course.id,
        program_code=course.program_code,
        scheme_year=course.scheme_year,
        semester=course.semester,
        course_code=course.course_code,
        title=course.title,
        credits=course.credits,
        category=course.category,
        contact_hours=course.contact_hours,
        prerequisites=json.loads(course.prerequisites_json),
        outcomes=json.loads(course.outcomes_json),
        source_url=course.source_url,
        source_checksum=course.source_checksum,
        verification_status=course.verification_status,
        created_at=course.created_at,
    )


@router.get("/rvce/courses", response_model=list[RvceSyllabusCourseResponse])
def list_rvce_courses(
    program_code: str | None = Query(default=None),
    scheme_year: int | None = Query(default=None, ge=2016, le=2100),
    semester: int | None = Query(default=None, ge=1, le=8),
    db: Session = Depends(get_db),
) -> list[RvceSyllabusCourseResponse]:
    query = select(RvceSyllabusCourse).where(RvceSyllabusCourse.verification_status == "academic_verified")
    if program_code:
        query = query.where(RvceSyllabusCourse.program_code == program_code.upper())
    if scheme_year:
        query = query.where(RvceSyllabusCourse.scheme_year == scheme_year)
    if semester:
        query = query.where(RvceSyllabusCourse.semester == semester)
    return [_response(course) for course in db.scalars(query.order_by(RvceSyllabusCourse.semester, RvceSyllabusCourse.course_code)).all()]


@router.post("/rvce/courses", response_model=RvceSyllabusCourseResponse, status_code=status.HTTP_201_CREATED)
def create_rvce_course(
    payload: RvceSyllabusCourseCreate,
    current_user: User = Depends(require_roles("admin", "instructor")),
    db: Session = Depends(get_db),
) -> RvceSyllabusCourseResponse:
    catalog = get_rvce_catalog()
    program_code = payload.program_code.upper()
    alias_map = {alias: program["code"] for program in catalog["program_schemes"] for alias in program.get("aliases", [])}
    program_code = alias_map.get(program_code, program_code)
    program = next((item for item in catalog["program_schemes"] if item["code"] == program_code), None)
    if program is None:
        raise HTTPException(status_code=422, detail="Program code is not in the RVCE catalog")
    supported_schemes = set(catalog["common_first_year_schemes"] if payload.semester <= 2 else program["schemes"])
    if payload.scheme_year not in supported_schemes:
        raise HTTPException(status_code=422, detail="Scheme is not catalogued for this RVCE program and semester")
    if payload.verification_status == "academic_verified" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can verify RVCE course records")
    course_code = payload.course_code.upper()
    if db.scalar(select(RvceSyllabusCourse).where(
        RvceSyllabusCourse.program_code == program_code,
        RvceSyllabusCourse.scheme_year == payload.scheme_year,
        RvceSyllabusCourse.semester == payload.semester,
        RvceSyllabusCourse.course_code == course_code,
    )):
        raise HTTPException(status_code=409, detail="RVCE course record already exists")
    course = RvceSyllabusCourse(
        program_code=program_code,
        scheme_year=payload.scheme_year,
        semester=payload.semester,
        course_code=course_code,
        title=payload.title.strip(),
        credits=payload.credits,
        category=payload.category.strip(),
        contact_hours=payload.contact_hours,
        prerequisites_json=json.dumps(payload.prerequisites),
        outcomes_json=json.dumps(payload.outcomes),
        source_url=str(payload.source_url),
        source_checksum=payload.source_checksum.lower(),
        verification_status=payload.verification_status,
    )
    db.add(course)
    record_event(db, "rvce_course_created", current_user.id, metadata={"program_code": program_code, "course_code": course_code, "verification_status": payload.verification_status})
    db.commit()
    db.refresh(course)
    return _response(course)
