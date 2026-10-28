import hashlib
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy import update

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Resource
from ml.preprocessing.ocr_processor import run_pdf_ocr
from app.services.storage import storage


def process_pdf(upload_path: Path, processed_path: Path) -> int:
    """Validate and extract a bounded amount of text from a private PDF."""
    if not upload_path.is_file() or upload_path.suffix.lower() != ".pdf":
        raise ValueError("Uploaded document is not available")
    if upload_path.stat().st_size > settings.max_upload_bytes:
        raise ValueError("Uploaded document exceeds the configured size limit")
    with upload_path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise ValueError("Uploaded document is not a valid PDF")
    reader = PdfReader(str(upload_path), strict=False)
    if len(reader.pages) > settings.max_pdf_pages:
        raise ValueError("PDF exceeds the configured page limit")
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported")
    chunks: list[str] = []
    total = 0
    for page in reader.pages:
        text = page.extract_text() or ""
        remaining = settings.max_extracted_text_chars - total
        if remaining <= 0:
            break
        chunks.append(text[:remaining])
        total += min(len(text), remaining)
    extracted = "\n".join(chunks)
    if settings.ocr_enabled and len(extracted.strip()) < 20:
        extracted = run_pdf_ocr(upload_path, settings.max_extracted_text_chars)
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    processed_path.write_text(extracted, encoding="utf-8")
    return len(extracted)


def process_resource_by_id(resource_id: str) -> bool:
    """Process one queued resource; safe for a worker retry loop."""
    db = SessionLocal()
    resource = None
    try:
        claimed = db.execute(update(Resource).where(Resource.id == resource_id, Resource.processing_status == "queued").values(processing_status="processing"))
        if claimed.rowcount != 1:
            db.rollback()
            return False
        db.commit()
        resource = db.get(Resource, resource_id)
        if resource is None or not resource.storage_key:
            return False
        with storage.materialize(resource.storage_key) as upload_path:
            if resource.checksum:
                digest = hashlib.sha256()
                with upload_path.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
                if digest.hexdigest() != resource.checksum:
                    raise ValueError("Uploaded document checksum does not match metadata")
            output_key = f"processed/{resource.id}.txt"
            output_path = Path(settings.processed_dir).resolve() / f"{resource.id}.txt"
            process_pdf(upload_path, output_path)
            storage.put_bytes(output_key, output_path.read_bytes(), content_type="text/plain; charset=utf-8")
            resource.processed_key = output_key
            if settings.storage_backend == "s3":
                output_path.unlink(missing_ok=True)
        resource.processing_status = "processed"
        db.commit()
        return True
    except Exception:
        if resource is not None:
            resource.processing_status = "failed"
            db.commit()
        return False
    finally:
        db.close()
