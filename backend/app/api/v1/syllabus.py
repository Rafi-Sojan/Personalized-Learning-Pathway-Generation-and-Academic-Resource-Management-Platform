import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.infrastructure.cache import redis_cache
from app.infrastructure.rate_limiter import enforce_rate_limit, expensive_limiter
from app.models import Concept, ConceptPrerequisite, Course, Resource as ResourceModel, SyllabusRecord, SyllabusVersion, User
from app.schemas.learning import Resource
from app.services.document_processing import process_resource_by_id
from app.services.storage import storage
from app.services.syllabus_service import extract_prerequisite_candidates, extract_syllabus_facts, extract_syllabus_topics, select_syllabus_course_section
from ml.concept_mapping.text_cleaner import clean_text

router = APIRouter()


class SyllabusRequest(BaseModel):
    """Bound the text accepted by the lightweight syllabus analysis endpoint."""

    text: str = Field(min_length=3, max_length=200_000)


def _owned_course(course_id: str, user: User, db: Session) -> Course:
    """Resolve a course owned by the authenticated learner."""
    course = db.scalar(select(Course).where(Course.id == course_id, Course.owner_id == user.id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def _owned_syllabus(resource_id: str, user: User, db: Session) -> ResourceModel:
    """Resolve an uploaded syllabus copy inside a course owned by the caller."""
    resource = db.scalar(
        select(ResourceModel)
        .join(Course, Course.id == ResourceModel.course_id)
        .where(
            ResourceModel.id == resource_id,
            ResourceModel.kind == "syllabus_pdf",
            Course.owner_id == user.id,
        )
    )
    if resource is None:
        raise HTTPException(status_code=404, detail="Syllabus copy not found")
    return resource


@router.post("/analyze")
def analyze_syllabus(payload: SyllabusRequest, _: User = Depends(get_current_user)) -> dict:
    """Extract syllabus topic candidates from submitted text without persisting it."""
    topics = extract_syllabus_topics(payload.text, limit=100)
    return {
        "topics": [topic.name for topic in topics],
        "topic_details": [
            {"name": topic.name, "unit_label": topic.unit_label, "source_page": topic.source_page}
            for topic in topics
        ],
        "count": len(topics),
        "status": "completed",
    }


@router.get("/sources", response_model=list[Resource])
def list_syllabus_sources(
    course_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Resource]:
    """List stored syllabus PDF copies for one learner-owned course."""
    _owned_course(course_id, current_user, db)
    sources = db.scalars(
        select(ResourceModel)
        .where(ResourceModel.course_id == course_id, ResourceModel.kind == "syllabus_pdf")
        .order_by(ResourceModel.created_at.desc())
    ).all()
    return [Resource.model_validate(source) for source in sources]


@router.post("/sources/upload", response_model=Resource, status_code=201)
async def upload_syllabus_source(
    request: Request,
    course_id: str = Query(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Resource:
    """Store a size-bounded PDF syllabus copy as the course's source document."""
    enforce_rate_limit(request, expensive_limiter)
    _owned_course(course_id, current_user, db)
    if file.content_type != "application/pdf" or Path(file.filename or "").suffix.lower() != ".pdf":
        raise HTTPException(status_code=415, detail="Only PDF syllabus copies are supported")
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Syllabus PDF exceeds the configured upload limit")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="Uploaded content is not a valid PDF")
    source_key = f"syllabus-{uuid.uuid4()}.pdf"
    storage.put_bytes(source_key, data, content_type="application/pdf")
    resource = ResourceModel(
        course_id=course_id,
        title=Path(file.filename or "syllabus.pdf").name[:240],
        kind="syllabus_pdf",
        storage_key=source_key,
        checksum=hashlib.sha256(data).hexdigest(),
        processing_status="uploaded",
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    redis_cache.delete(f"courses:{current_user.id}")
    return Resource.model_validate(resource)


@router.post("/sources/{resource_id}/process", response_model=Resource)
def process_syllabus_source(
    resource_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Resource:
    """Extract text from one stored syllabus PDF using the existing document worker."""
    resource = _owned_syllabus(resource_id, current_user, db)
    if not resource.storage_key:
        raise HTTPException(status_code=422, detail="Syllabus PDF storage is unavailable")
    resource.processing_status = "queued"
    resource.processing_attempts = 0
    resource.processing_error = None
    resource.processing_started_at = None
    resource.processing_next_attempt_at = None
    resource.processed_at = None
    db.commit()
    db.refresh(resource)
    redis_cache.delete(f"courses:{current_user.id}")
    background_tasks.add_task(process_resource_by_id, resource.id)
    return Resource.model_validate(resource)


@router.post("/sources/{resource_id}/generate-map")
def generate_concept_map_from_syllabus(
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Create missing course concepts from extracted syllabus topics and record a version."""
    source = _owned_syllabus(resource_id, current_user, db)
    if source.processing_status != "processed" or not source.processed_key:
        raise HTTPException(status_code=409, detail="Process this syllabus copy before generating its concept map")
    if source.course_id is None:
        raise HTTPException(status_code=422, detail="Syllabus copy is not attached to a course")
    text = storage.read_bytes(source.processed_key).decode("utf-8", errors="replace")
    course = _owned_course(source.course_id, current_user, db)
    course_text = select_syllabus_course_section(text, course.code)
    if course_text == "":
        raise HTTPException(status_code=422, detail=f"This multi-course syllabus does not contain course code {course.code}")
    syllabus_text = course_text if course_text is not None else text
    topics = extract_syllabus_topics(syllabus_text)
    if not topics:
        raise HTTPException(status_code=422, detail="No syllabus topics could be extracted from this PDF")

    version = db.scalar(select(SyllabusVersion).where(SyllabusVersion.source_resource_id == source.id))
    if version is None:
        version = SyllabusVersion(course_id=source.course_id, label=source.title[:120], source_resource_id=source.id)
        db.add(version)
        db.flush()

    existing = db.scalars(select(Concept).where(Concept.course_id == source.course_id)).all()
    # This course has one current map: older mapped topics stay stored for references
    # such as prior plans, but only concepts in this source version remain current.
    for concept in existing:
        if concept.syllabus_version_id is not None:
            concept.syllabus_version_id = None
            concept.unit_label = None
            concept.source_page = None
    concepts_by_name = {clean_text(concept.name): concept for concept in existing}
    topics_per_unit: dict[str, int] = {}
    for topic in topics:
        if topic.unit_label:
            topics_per_unit[topic.unit_label] = topics_per_unit.get(topic.unit_label, 0) + 1
    added = []
    reused = []
    for topic in topics:
        normalized = clean_text(topic.name)
        if not normalized:
            continue
        if normalized in concepts_by_name:
            concept = concepts_by_name[normalized]
            concept.unit_label = topic.unit_label
            concept.source_page = topic.source_page
            concept.syllabus_version_id = version.id
            reused.append(concept)
        else:
            concept = Concept(course_id=source.course_id, name=topic.name[:200], difficulty=1, status="not_started", unit_label=topic.unit_label, source_page=topic.source_page, syllabus_version_id=version.id)
            db.add(concept)
            concepts_by_name[normalized] = concept
            added.append(concept)
        db.flush()
        parent = concepts_by_name.get(clean_text(topic.parent_label)) if topic.parent_label else None
        concept.parent_concept_id = parent.id if parent and parent.id != concept.id else None
        count_in_unit = topics_per_unit.get(topic.unit_label or "", 0)
        concept.estimated_minutes = max(10, round(topic.unit_hours * 60 / count_in_unit)) if topic.unit_hours and count_in_unit else None
        prior_record = db.scalar(select(SyllabusRecord).where(
            SyllabusRecord.syllabus_version_id == version.id,
            SyllabusRecord.record_type == topic.record_type,
            SyllabusRecord.normalized_text == normalized,
            SyllabusRecord.unit_label == topic.unit_label,
            SyllabusRecord.parent_label == topic.parent_label,
            SyllabusRecord.source_page == topic.source_page,
        ))
        confidence = 0.82 if topic.unit_label and topic.source_page else 0.58
        if prior_record is None:
            db.add(SyllabusRecord(
                syllabus_version_id=version.id, source_resource_id=source.id, course_id=source.course_id,
                record_type=topic.record_type, source_page=topic.source_page, source_text=topic.name,
                normalized_text=normalized[:500], unit_label=topic.unit_label,
                parent_label=topic.parent_label, hours=topic.unit_hours, confidence=confidence,
                review_status="pending_review", mapped_concept_id=concept.id,
            ))
    # Preserve labeled syllabus outcomes, labs, assessment rules, and metadata as
    # page-linked facts without creating misleading concept-map nodes from them.
    for fact in extract_syllabus_facts(syllabus_text):
        normalized = clean_text(fact.source_text)
        prior_fact = db.scalar(select(SyllabusRecord).where(
            SyllabusRecord.syllabus_version_id == version.id,
            SyllabusRecord.record_type == fact.record_type,
            SyllabusRecord.normalized_text == normalized,
        ))
        if prior_fact is None:
            db.add(SyllabusRecord(
                syllabus_version_id=version.id, source_resource_id=source.id, course_id=source.course_id,
                record_type=fact.record_type, source_page=fact.source_page, source_text=fact.source_text,
                normalized_text=normalized[:500], unit_label=fact.unit_label, hours=fact.hours,
                confidence=0.58, review_status="pending_review",
            ))
    suggested_edges = 0
    for candidate in extract_prerequisite_candidates(syllabus_text):
        child = concepts_by_name.get(clean_text(candidate.concept_name))
        prerequisite = concepts_by_name.get(clean_text(candidate.prerequisite_name))
        if child is None or prerequisite is None or child.id == prerequisite.id:
            continue
        existing_edge = db.get(ConceptPrerequisite, (child.id, prerequisite.id))
        if existing_edge is None:
            db.add(ConceptPrerequisite(concept_id=child.id, prerequisite_id=prerequisite.id, status="proposed", source_page=candidate.source_page, confidence=0.78, rationale=candidate.source_text))
            suggested_edges += 1
    db.commit()
    redis_cache.delete(f"concepts:{current_user.id}:all")
    redis_cache.delete(f"concepts:{current_user.id}:{source.course_id}")
    redis_cache.delete(f"concepts:{current_user.id}:all:all-sources")
    redis_cache.delete(f"concepts:{current_user.id}:{source.course_id}:all-sources")
    redis_cache.delete(f"concepts:{current_user.id}:all:syllabus")
    redis_cache.delete(f"concepts:{current_user.id}:{source.course_id}:syllabus")
    redis_cache.delete(f"courses:{current_user.id}")
    for concept in [*added, *reused]:
        db.refresh(concept)
    return {
        "source_resource_id": source.id,
        "course_code": course.code,
        "syllabus_version_id": version.id,
        "topics_found": len(topics),
        "concepts_added": len(added),
        "concepts_reused": len(reused),
        "prerequisite_suggestions": suggested_edges,
        "concepts": [
            {"id": concept.id, "name": concept.name, "course_id": concept.course_id, "unit_label": concept.unit_label, "source_page": concept.source_page, "parent_concept_id": concept.parent_concept_id, "estimated_minutes": concept.estimated_minutes}
            for concept in [*added, *reused]
        ],
    }


@router.get("/records")
def list_syllabus_records(
    course_id: str = Query(...),
    syllabus_version_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """List parsed syllabus content and its version, page, confidence, and review state."""
    _owned_course(course_id, current_user, db)
    query = select(SyllabusRecord).where(SyllabusRecord.course_id == course_id)
    if syllabus_version_id:
        query = query.where(SyllabusRecord.syllabus_version_id == syllabus_version_id)
    return [
        {"id": row.id, "syllabus_version_id": row.syllabus_version_id, "source_resource_id": row.source_resource_id,
         "record_type": row.record_type, "source_page": row.source_page, "source_text": row.source_text,
         "normalized_text": row.normalized_text, "unit_label": row.unit_label, "parent_label": row.parent_label,
         "hours": row.hours, "confidence": row.confidence,
         "review_status": row.review_status, "mapped_concept_id": row.mapped_concept_id}
        for row in db.scalars(query.order_by(SyllabusRecord.source_page, SyllabusRecord.id)).all()
    ]


@router.post("/records/{record_id}/review")
def review_syllabus_record(
    record_id: str,
    status: str = Query(..., pattern="^(verified|rejected|pending_review)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Allow the owning learner to verify or reject an extracted topic record."""
    record = db.scalar(select(SyllabusRecord).join(Course, Course.id == SyllabusRecord.course_id).where(
        SyllabusRecord.id == record_id, Course.owner_id == current_user.id,
    ))
    if record is None:
        raise HTTPException(status_code=404, detail="Syllabus record not found")
    record.review_status = status
    db.commit()
    redis_cache.delete(f"concepts:{current_user.id}:all:all-sources")
    redis_cache.delete(f"concepts:{current_user.id}:{record.course_id}:all-sources")
    redis_cache.delete(f"concepts:{current_user.id}:all:syllabus")
    redis_cache.delete(f"concepts:{current_user.id}:{record.course_id}:syllabus")
    return {"id": record.id, "review_status": record.review_status}
