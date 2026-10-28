import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.infrastructure.rate_limiter import enforce_rate_limit, expensive_limiter
from app.models import Concept, Course, Resource as ResourceModel, ResourceConceptMapping, User
from app.schemas.learning import Resource, ResourceMappingRequest, ResourceMappingResponse
from app.services.document_processing import process_resource_by_id
from app.services.storage import storage

router = APIRouter()


@router.get("", response_model=list[Resource])
def get_resources(concept_id: str | None = Query(default=None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Resource]:
    query = select(ResourceModel).join(Course, Course.id == ResourceModel.course_id, isouter=True).where((ResourceModel.course_id.is_(None)) | (Course.owner_id == current_user.id))
    if concept_id:
        query = query.where(ResourceModel.concept_id == concept_id)
    return [Resource.model_validate(item) for item in db.scalars(query).all()]


@router.post("/upload", response_model=Resource, status_code=201)
async def upload_resource(request: Request, file: UploadFile = File(...), course_id: str = Query(...), concept_id: str | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Resource:
    enforce_rate_limit(request, expensive_limiter)
    if file.content_type != "application/pdf" or Path(file.filename or "").suffix.lower() != ".pdf":
        raise HTTPException(status_code=415, detail="Only PDF uploads are supported")
    course = db.scalar(select(Course).where(Course.id == course_id, Course.owner_id == current_user.id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if concept_id and db.scalar(select(Concept).where(Concept.id == concept_id, Concept.course_id == course_id)) is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the configured upload limit")
    key = f"{uuid.uuid4()}.pdf"
    if not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="Uploaded content is not a valid PDF")
    storage.put_bytes(key, data, content_type="application/pdf")
    safe_title = Path(file.filename or "uploaded.pdf").name[:240]
    resource = ResourceModel(title=safe_title, kind="pdf", course_id=course_id, concept_id=concept_id, storage_key=key, checksum=hashlib.sha256(data).hexdigest(), duration_minutes=0, processing_status="uploaded")
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return Resource.model_validate(resource)


@router.post("/{resource_id}/process", response_model=Resource)
def process_resource(resource_id: str, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Resource:
    resource = db.scalar(select(ResourceModel).join(Course, Course.id == ResourceModel.course_id, isouter=True).where(ResourceModel.id == resource_id, (ResourceModel.course_id.is_(None)) | (Course.owner_id == current_user.id)))
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    if not resource.storage_key:
        resource.processing_status = "ready"
        db.commit()
        return Resource.model_validate(resource)
    resource.processing_status = "queued"
    resource.processing_attempts = 0
    resource.processing_error = None
    resource.processing_started_at = None
    resource.processing_next_attempt_at = None
    resource.processed_at = None
    db.commit()
    db.refresh(resource)
    background_tasks.add_task(_process_resource_in_background, resource.id)
    return Resource.model_validate(resource)


def _process_resource_in_background(resource_id: str) -> None:
    process_resource_by_id(resource_id)


@router.get("/{resource_id}/mappings", response_model=list[ResourceMappingResponse])
def get_resource_mappings(resource_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ResourceMappingResponse]:
    resource = db.scalar(select(ResourceModel).join(Course, Course.id == ResourceModel.course_id, isouter=True).where(ResourceModel.id == resource_id, (ResourceModel.course_id.is_(None)) | (Course.owner_id == current_user.id)))
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    mappings = db.scalars(select(ResourceConceptMapping).where(ResourceConceptMapping.resource_id == resource_id)).all()
    return [ResourceMappingResponse.model_validate(item, from_attributes=True) for item in mappings]


@router.post("/{resource_id}/mappings", response_model=ResourceMappingResponse, status_code=201)
def create_resource_mapping(resource_id: str, payload: ResourceMappingRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ResourceMappingResponse:
    resource = db.scalar(select(ResourceModel).join(Course, Course.id == ResourceModel.course_id, isouter=True).where(ResourceModel.id == resource_id, (ResourceModel.course_id.is_(None)) | (Course.owner_id == current_user.id)))
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    concept = db.scalar(select(Concept).where(Concept.id == payload.concept_id, Concept.course_id == resource.course_id))
    if concept is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    mapping = db.scalar(select(ResourceConceptMapping).where(ResourceConceptMapping.resource_id == resource_id, ResourceConceptMapping.concept_id == payload.concept_id))
    if mapping is None:
        mapping = ResourceConceptMapping(resource_id=resource_id, concept_id=payload.concept_id)
        db.add(mapping)
    mapping.confidence = payload.confidence
    mapping.status = payload.status
    mapping.source = payload.source
    mapping.reviewed_by = current_user.id if payload.status in {"accepted", "rejected"} else None
    db.commit()
    db.refresh(mapping)
    return ResourceMappingResponse.model_validate(mapping, from_attributes=True)
