import hashlib
import logging
from datetime import timedelta
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy import or_, select, update

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Resource
from ml.preprocessing.ocr_processor import run_pdf_ocr_pages
from app.services.storage import storage
from app.core.metrics import metrics


logger = logging.getLogger(__name__)


def recover_stale_resources() -> int:
    """Release worker leases that exceeded the configured processing timeout."""
    db = SessionLocal()
    try:
        from app.models import utc_now

        now = utc_now()
        cutoff = now - timedelta(seconds=settings.worker_timeout_seconds)
        stale = db.scalars(
            select(Resource).where(
                Resource.processing_status == "processing",
                Resource.processing_started_at.is_not(None),
                Resource.processing_started_at < cutoff,
            )
        ).all()
        for resource in stale:
            terminal = resource.processing_attempts >= settings.max_processing_attempts
            resource.processing_status = "failed" if terminal else "retryable"
            resource.processing_error = "Worker lease expired before processing completed"
            resource.processing_next_attempt_at = None if terminal else now + timedelta(seconds=settings.document_retry_delay_seconds)
        if stale:
            db.commit()
            metrics.observe_worker("lease_expired")
            logger.warning("Recovered %s stale document-processing lease(s)", len(stale))
        return len(stale)
    finally:
        db.close()



def process_pdf(upload_path: Path, processed_path: Path) -> int:
    """Extract digital and scanned PDF pages with bounded output."""

    if not upload_path.is_file() or upload_path.suffix.lower() != ".pdf":
        raise ValueError("Uploaded document is not available")

    if upload_path.stat().st_size > settings.max_upload_bytes:
        raise ValueError("Uploaded document exceeds the size limit")

    with upload_path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise ValueError("Uploaded document is not a valid PDF")

    reader = PdfReader(str(upload_path), strict=False)

    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported")

    if len(reader.pages) > settings.max_pdf_pages:
        raise ValueError("PDF exceeds the configured page limit")

    page_texts: dict[int, str] = {}
    ocr_candidates: list[int] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        page_texts[page_number] = text[
            :settings.max_extracted_text_chars
        ]

        if settings.ocr_enabled and len(text.strip()) < 20:
            ocr_candidates.append(page_number)

    # OCR only pages whose digital extraction was insufficient.
    if ocr_candidates:
        ocr_results = run_pdf_ocr_pages(
            str(upload_path),
            ocr_candidates,
            settings.max_extracted_text_chars,
        )

        for page_number, ocr_text in ocr_results.items():
            if ocr_text.strip():
                page_texts[page_number] = ocr_text

    chunks: list[str] = []
    total = 0
    max_chars = settings.max_extracted_text_chars

    for page_number in sorted(page_texts):
        marker = f"[[PAGE {page_number}]]\n"

        separator_length = 1 if chunks else 0

        remaining = (
            max_chars
            - total
            - len(marker)
            - separator_length
        )

        if remaining <= 0:
            break

        text = page_texts[page_number][:remaining]

        chunks.append(f"{marker}{text}")

        total += (
            len(marker)
            + len(text)
            + separator_length
        )

    extracted = "\n".join(chunks)

    processed_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    processed_path.write_text(
        extracted,
        encoding="utf-8",
    )

    return len(extracted)


def process_resource_by_id(resource_id: str) -> bool:
    """Process one resource with durable retry and dead-letter state."""
    db = SessionLocal()
    try:
        from app.models import utc_now

        claimed_at = utc_now()
        claimed = db.execute(
            update(Resource)
            .where(
                Resource.id == resource_id,
                Resource.processing_status.in_(["queued", "retryable"]),
                or_(Resource.processing_next_attempt_at.is_(None), Resource.processing_next_attempt_at <= claimed_at),
            )
            .values(
                processing_status="processing",
                processing_attempts=Resource.processing_attempts + 1,
                processing_started_at=claimed_at,
                processing_next_attempt_at=None,
                processing_error=None,
            )
        )
        if claimed.rowcount != 1:
            db.rollback()
            return False
        db.commit()
        resource = db.get(Resource, resource_id)
        if resource is None or not resource.storage_key:
            raise ValueError("Queued resource has no storage key")
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
        resource.processing_error = None
        resource.processing_next_attempt_at = None
        resource.processed_at = utc_now()
        db.commit()
        metrics.observe_worker("processed")
        return True
    except Exception as exc:
        db.rollback()
        resource = db.scalar(select(Resource).where(Resource.id == resource_id))
        if resource is not None:
            terminal = resource.processing_attempts >= settings.max_processing_attempts
            resource.processing_status = "failed" if terminal else "retryable"
            resource.processing_error = str(exc)[:1000]
            resource.processing_next_attempt_at = None if terminal else utc_now() + timedelta(seconds=settings.document_retry_delay_seconds)
            db.commit()
            metrics.observe_worker("failed" if terminal else "retryable")
            logger.exception("Document processing failed resource_id=%s terminal=%s", resource_id, terminal)
        return False
    finally:
        db.close()
