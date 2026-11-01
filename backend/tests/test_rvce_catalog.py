"""API and provenance checks for the RVCE syllabus onboarding flow."""

import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.api.v1.catalog import _validate_source_provenance
from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models import AuditEvent, Concept, ConceptPrerequisite, Course, RvceSyllabusCourse, SyllabusVersion, User


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def _create_user_headers(role: str) -> tuple[dict[str, str], str]:
    """Create an isolated API principal and return its bearer header and database ID."""
    db = SessionLocal()
    user = User(email=f"rvce-{role}-{uuid4().hex}@example.test", name=f"RVCE {role}", password_hash=hash_password("test-password"), role=role)
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(user.id, user.token_version)
        return {"Authorization": f"Bearer {token}"}, user.id
    finally:
        db.close()


def _remove_test_records(course_ids: list[str], rvce_ids: list[str], user_ids: list[str]) -> None:
    """Remove test-created syllabus, learner, audit, and dependent course records."""
    db = SessionLocal()
    try:
        concept_ids = list(db.scalars(select(Concept.id).where(Concept.course_id.in_(course_ids))).all()) if course_ids else []
        if concept_ids:
            db.execute(delete(ConceptPrerequisite).where((ConceptPrerequisite.concept_id.in_(concept_ids)) | (ConceptPrerequisite.prerequisite_id.in_(concept_ids))))
        if course_ids:
            db.execute(delete(SyllabusVersion).where(SyllabusVersion.course_id.in_(course_ids)))
            db.execute(delete(Concept).where(Concept.course_id.in_(course_ids)))
            db.execute(delete(Course).where(Course.id.in_(course_ids)))
        if rvce_ids:
            db.execute(delete(RvceSyllabusCourse).where(RvceSyllabusCourse.id.in_(rvce_ids)))
        if user_ids:
            db.execute(delete(AuditEvent).where(AuditEvent.actor_id.in_(user_ids)))
            db.execute(delete(User).where(User.id.in_(user_ids)))
        db.commit()
    finally:
        db.close()


def test_rvce_source_provenance_requires_known_file_checksum_and_page() -> None:
    """Accept a manifest-backed source page and reject altered or out-of-range evidence."""
    manifest = json.loads((ROOT / "database" / "rvce_source_documents.json").read_text(encoding="utf-8"))
    source = manifest["documents"][0]
    _validate_source_provenance(source["relative_path"], 1, source["sha256"], manifest["source_url"])

    with pytest.raises(HTTPException) as invalid_checksum:
        _validate_source_provenance(source["relative_path"], 1, "0" * 64, manifest["source_url"])
    assert invalid_checksum.value.status_code == 422

    with pytest.raises(HTTPException) as invalid_page:
        _validate_source_provenance(source["relative_path"], source["pages"] + 1, source["sha256"], manifest["source_url"])
    assert invalid_page.value.status_code == 422


def test_rvce_unmapped_first_year_course_requires_branch_review_and_enrolls_idempotently() -> None:
    """Exercise admin import, mandatory branch mapping, publication, and repeated enrollment."""
    admin_headers, admin_id = _create_user_headers("admin")
    student_headers, student_id = _create_user_headers("student")
    manifest = json.loads((ROOT / "database" / "rvce_source_documents.json").read_text(encoding="utf-8"))
    first_year = next(item for item in manifest["documents"] if item["relative_path"].startswith("First Year/Scheme/2025/"))
    identity = uuid4().hex[:8].upper()
    imported_ids: list[str] = []
    course_ids: list[str] = []
    try:
        imported = client.post("/api/v1/catalog/rvce/courses/import", headers=admin_headers, json=[{
            "program_code": "BE-UNMAPPED",
            "scheme_year": 2025,
            "semester": 1,
            "course_code": f"T{identity}",
            "title": "Reviewed first-year fixture",
            "credits": 3,
            "category": "TEST FIXTURE",
            "contact_hours": 30,
            "prerequisites": [],
            "outcomes": [],
            "source_url": manifest["source_url"],
            "source_checksum": first_year["sha256"],
            "source_filename": first_year["relative_path"],
            "source_page": 1,
            "verification_status": "pending_review",
        }])
        assert imported.status_code == 201, imported.text
        record = imported.json()[0]
        imported_ids.append(record["id"])
        assert record["verification_status"] == "pending_review"

        missing_mapping = client.patch(
            f"/api/v1/catalog/rvce/courses/{record['id']}/verification",
            headers=admin_headers,
            json={"verification_status": "academic_verified"},
        )
        assert missing_mapping.status_code == 422

        approved = client.patch(
            f"/api/v1/catalog/rvce/courses/{record['id']}/verification",
            headers=admin_headers,
            json={"verification_status": "academic_verified", "program_code": "AS"},
        )
        assert approved.status_code == 200, approved.text
        assert approved.json()["program_code"] == "AS"

        visible = client.get("/api/v1/catalog/rvce/courses", params={"program_code": "AS", "scheme_year": 2025, "semester": 1})
        assert any(item["id"] == record["id"] for item in visible.json())

        enrollment = {"program_code": "AS", "scheme_year": 2025, "semester": 1}
        first_enrollment = client.post("/api/v1/catalog/rvce/enroll", headers=student_headers, json=enrollment)
        assert first_enrollment.status_code == 200, first_enrollment.text
        course_ids.extend(first_enrollment.json()["course_ids"])
        assert first_enrollment.json()["created"] == 1
        repeated_enrollment = client.post("/api/v1/catalog/rvce/enroll", headers=student_headers, json=enrollment)
        assert repeated_enrollment.status_code == 200, repeated_enrollment.text
        assert repeated_enrollment.json()["created"] == 0
        assert repeated_enrollment.json()["existing"] == 1
    finally:
        _remove_test_records(course_ids, imported_ids, [admin_id, student_id])
