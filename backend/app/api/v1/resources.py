import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.infrastructure.rate_limiter import enforce_rate_limit, expensive_limiter
from app.models import Concept, Course, Resource as ResourceModel, User
from app.schemas.learning import Resource

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
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    (upload_path / key).write_bytes(data)
    resource = ResourceModel(title=file.filename or "uploaded.pdf", kind="pdf", course_id=course_id, concept_id=concept_id, storage_key=key, checksum=hashlib.sha256(data).hexdigest(), duration_minutes=0, processing_status="uploaded")
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return Resource.model_validate(resource)


@router.post("/{resource_id}/process", response_model=Resource)
def process_resource(resource_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Resource:
    resource = db.scalar(select(ResourceModel).join(Course, Course.id == ResourceModel.course_id, isouter=True).where(ResourceModel.id == resource_id, (ResourceModel.course_id.is_(None)) | (Course.owner_id == current_user.id)))
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    if not resource.storage_key:
        resource.processing_status = "ready"
        db.commit()
        return Resource.model_validate(resource)
    try:
        from pypdf import PdfReader
        path = Path(settings.upload_dir) / resource.storage_key
        reader = PdfReader(str(path))
        extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        processed_path = Path(settings.processed_dir)
        processed_path.mkdir(parents=True, exist_ok=True)
        (processed_path / f"{resource.id}.txt").write_text(extracted_text, encoding="utf-8")
        resource.processing_status = "processed"
    except Exception:
        resource.processing_status = "failed"
    db.commit()
    db.refresh(resource)
    return Resource.model_validate(resource)
