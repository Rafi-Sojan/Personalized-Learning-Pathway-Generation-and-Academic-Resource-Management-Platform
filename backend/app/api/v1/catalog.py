import json
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.session import get_db
from app.models import Course, RvceSyllabusCourse, SyllabusVersion, User
from app.schemas.rvce import RvceEnrollmentRequest, RvceEnrollmentResponse, RvceSyllabusCourseCreate, RvceSyllabusCourseResponse
from app.services.rvce_catalog import get_rvce_catalog
from app.services.audit import record_event


router = APIRouter()


def _validate_source_provenance(source_filename: str, source_page: int, source_checksum: str, source_url: str) -> None:
    """Require an import to identify a page in an inventoried, unchanged RVCE PDF."""
    manifest_path = Path(__file__).resolve().parents[4] / "database" / "rvce_source_documents.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = next((item for item in manifest["documents"] if item["relative_path"] == source_filename), None)
    official_url = manifest["source_url"]
    if source is None or source["sha256"].lower() != source_checksum.lower():
        raise HTTPException(status_code=422, detail="Source file and checksum are not in the RVCE provenance manifest")
    if source_page < 1 or source_page > source["pages"]:
        raise HTTPException(status_code=422, detail="Source page is outside the inventoried PDF")
    if source_url != official_url:
        raise HTTPException(status_code=422, detail="Source URL must match the official RVCE syllabus index")


@router.get("/rvce")
def get_rvce_catalog_metadata() -> dict:
    """Return provenance-aware RVCE program and scheme metadata."""
    return get_rvce_catalog()


def _response(course: RvceSyllabusCourse) -> RvceSyllabusCourseResponse:
    """Convert a persisted RVCE row and its JSON fields into the public response schema."""
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
        source_filename=course.source_filename,
        source_page=course.source_page,
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
    """Return only academically approved, branch-mapped courses matching the filters."""
    query = select(RvceSyllabusCourse).where(
        RvceSyllabusCourse.verification_status == "academic_verified",
        RvceSyllabusCourse.program_code != "BE-UNMAPPED",
    )
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
    """Create a source-validated course record while enforcing RVCE scheme and role rules."""
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
    _validate_source_provenance(payload.source_filename, payload.source_page, payload.source_checksum, str(payload.source_url))
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
        source_filename=payload.source_filename,
        source_page=payload.source_page,
        verification_status=payload.verification_status,
    )
    db.add(course)
    record_event(db, "rvce_course_created", current_user.id, metadata={"program_code": program_code, "course_code": course_code, "verification_status": payload.verification_status})
    db.commit()
    db.refresh(course)
    return _response(course)


@router.post("/rvce/courses/import", response_model=list[RvceSyllabusCourseResponse], status_code=status.HTTP_201_CREATED)
def import_rvce_courses(
    payload: list[RvceSyllabusCourseCreate] = Body(min_length=1, max_length=500),
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> list[RvceSyllabusCourseResponse]:
    """Bulk load source-backed candidates; approval status is always pending."""
    catalog = get_rvce_catalog()
    programs = {entry["code"]: entry for entry in catalog["program_schemes"]}
    aliases = {alias: entry["code"] for entry in catalog["program_schemes"] for alias in entry.get("aliases", [])}
    new_rows: list[RvceSyllabusCourse] = []
    identities: set[tuple[str, int, int, str]] = set()
    for item in payload:
        _validate_source_provenance(item.source_filename, item.source_page, item.source_checksum, str(item.source_url))
        code = item.program_code.upper()
        code = aliases.get(code, code)
        if code != "BE-UNMAPPED":
            program = programs.get(code)
            if program is None:
                raise HTTPException(status_code=422, detail=f"Unknown RVCE program code: {code}")
            allowed = set(catalog["common_first_year_schemes"] if item.semester <= 2 else program["schemes"])
        else:
            allowed = set(catalog["common_first_year_schemes"])
            if item.semester > 2:
                raise HTTPException(status_code=422, detail="BE-UNMAPPED imports are limited to semesters 1 and 2")
        if item.scheme_year not in allowed:
            raise HTTPException(status_code=422, detail=f"Scheme {item.scheme_year} is not valid for {code}")
        if item.verification_status != "pending_review":
            raise HTTPException(status_code=422, detail="Bulk imports must remain pending_review")
        identity = (code, item.scheme_year, item.semester, item.course_code.upper())
        if identity in identities or db.scalar(select(RvceSyllabusCourse.id).where(
            RvceSyllabusCourse.program_code == code,
            RvceSyllabusCourse.scheme_year == item.scheme_year,
            RvceSyllabusCourse.semester == item.semester,
            RvceSyllabusCourse.course_code == item.course_code.upper(),
        )):
            raise HTTPException(status_code=409, detail=f"Duplicate RVCE course identity: {identity}")
        identities.add(identity)
        new_rows.append(RvceSyllabusCourse(
            program_code=code,
            scheme_year=item.scheme_year,
            semester=item.semester,
            course_code=item.course_code.upper(),
            title=item.title.strip(),
            credits=item.credits,
            category=item.category.strip(),
            contact_hours=item.contact_hours,
            prerequisites_json=json.dumps(item.prerequisites),
            outcomes_json=json.dumps(item.outcomes),
            source_url=str(item.source_url),
            source_checksum=item.source_checksum.lower(),
            source_filename=item.source_filename,
            source_page=item.source_page,
            verification_status="pending_review",
        ))
    db.add_all(new_rows)
    record_event(db, "rvce_course_batch_imported", current_user.id, metadata={"record_count": len(new_rows)})
    db.commit()
    for row in new_rows:
        db.refresh(row)
    return [_response(row) for row in new_rows]


class VerificationUpdate(BaseModel):
    verification_status: str = Field(pattern="^(academic_verified|rejected|pending_review)$")
    program_code: str | None = Field(default=None, min_length=2, max_length=20)


@router.get("/rvce/courses/review", response_model=list[RvceSyllabusCourseResponse])
def review_rvce_courses(_: User = Depends(require_roles("admin", "instructor")), db: Session = Depends(get_db)) -> list[RvceSyllabusCourseResponse]:
    """Return pending course records with provenance for instructor and administrator review."""
    records = db.scalars(select(RvceSyllabusCourse).where(RvceSyllabusCourse.verification_status == "pending_review").order_by(RvceSyllabusCourse.scheme_year, RvceSyllabusCourse.program_code, RvceSyllabusCourse.semester, RvceSyllabusCourse.course_code)).all()
    return [_response(item) for item in records]


@router.patch("/rvce/courses/{course_id}/verification", response_model=RvceSyllabusCourseResponse)
def update_rvce_course_verification(
    course_id: str,
    payload: VerificationUpdate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> RvceSyllabusCourseResponse:
    """Approve, reject, or return a candidate to review, mapping first-year scope when required."""
    course = db.get(RvceSyllabusCourse, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="RVCE course record not found")
    if course.program_code == "BE-UNMAPPED" and payload.verification_status == "academic_verified":
        if payload.program_code is None:
            raise HTTPException(status_code=422, detail="Map the first-year record to a branch before approving it")
        catalog = get_rvce_catalog()
        aliases = {alias: entry["code"] for entry in catalog["program_schemes"] for alias in entry.get("aliases", [])}
        mapped_code = aliases.get(payload.program_code.upper(), payload.program_code.upper())
        program = next((entry for entry in catalog["program_schemes"] if entry["code"] == mapped_code), None)
        allowed_schemes = set(catalog["common_first_year_schemes"])
        if program is None or course.scheme_year not in allowed_schemes:
            raise HTTPException(status_code=422, detail="The first-year record must map to a catalogued RVCE program and scheme")
        duplicate = db.scalar(select(RvceSyllabusCourse.id).where(
            RvceSyllabusCourse.program_code == mapped_code,
            RvceSyllabusCourse.scheme_year == course.scheme_year,
            RvceSyllabusCourse.semester == course.semester,
            RvceSyllabusCourse.course_code == course.course_code,
            RvceSyllabusCourse.id != course.id,
        ))
        if duplicate:
            raise HTTPException(status_code=409, detail="A course with this branch, scheme, semester, and code already exists")
        course.program_code = mapped_code
    elif payload.program_code is not None:
        raise HTTPException(status_code=422, detail="Program mapping is only accepted for unresolved first-year records")
    course.verification_status = payload.verification_status
    record_event(db, "rvce_course_verification_changed", current_user.id, metadata={"course_id": course.id, "status": payload.verification_status, "program_code": course.program_code})
    db.commit()
    db.refresh(course)
    return _response(course)


@router.post("/rvce/enroll", response_model=RvceEnrollmentResponse)
def enroll_rvce_semester(
    payload: RvceEnrollmentRequest,
    current_user: User = Depends(require_roles("student", "instructor", "admin")),
    db: Session = Depends(get_db),
) -> RvceEnrollmentResponse:
    """Create learner-owned courses from verified rows without placeholder concepts."""
    catalog = get_rvce_catalog()
    program_code = payload.program_code.upper()
    alias_map = {alias: entry["code"] for entry in catalog["program_schemes"] for alias in entry.get("aliases", [])}
    program_code = alias_map.get(program_code, program_code)
    program = next((entry for entry in catalog["program_schemes"] if entry["code"] == program_code), None)
    if program is None:
        raise HTTPException(status_code=422, detail="Program code is not in the RVCE catalog")
    allowed_schemes = set(catalog["common_first_year_schemes"] if payload.semester <= 2 else program["schemes"])
    if payload.scheme_year not in allowed_schemes:
        raise HTTPException(status_code=422, detail="Scheme is not catalogued for this RVCE program and semester")
    rows = db.scalars(select(RvceSyllabusCourse).where(
        RvceSyllabusCourse.verification_status == "academic_verified",
        RvceSyllabusCourse.scheme_year == payload.scheme_year,
        RvceSyllabusCourse.semester == payload.semester,
        RvceSyllabusCourse.program_code == program_code,
    ).order_by(RvceSyllabusCourse.course_code)).all()
    created = 0
    existing = 0
    course_ids: list[str] = []
    for row in rows:
        course_scope = f"RVCE {program_code} | {payload.scheme_year} scheme | Semester {payload.semester}"
        course = db.scalar(select(Course).where(
            Course.owner_id == current_user.id,
            Course.code == row.course_code,
            Course.description.like(f"{course_scope}%"),
        ))
        if course is not None:
            existing += 1
            course_ids.append(course.id)
            continue
        course = Course(
            owner_id=current_user.id,
            code=row.course_code,
            title=row.title,
            description=f"{course_scope} | {row.credits:g} credits | syllabus record {row.id}",
        )
        db.add(course)
        db.flush()
        # Course enrollment creates no placeholder concept; topics must come from a stored syllabus copy.
        db.add(SyllabusVersion(course_id=course.id, label=f"RVCE {payload.scheme_year} scheme, semester {payload.semester}"))
        created += 1
        course_ids.append(course.id)
    if created:
        record_event(db, "rvce_semester_enrolled", current_user.id, metadata={"program_code": program_code, "scheme_year": payload.scheme_year, "semester": payload.semester, "created": created})
        db.commit()
    return RvceEnrollmentResponse(created=created, existing=existing, course_ids=course_ids)
