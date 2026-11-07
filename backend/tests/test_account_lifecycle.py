"""Account portability and deletion regression coverage."""

from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models import AuditEvent, Concept, Course, HistoricalExamQuestion, QuizAttempt, Resource, ResourceConceptMapping, StudyPlan, StudyPlanItem, StudyPlanRevision, SyllabusRecord, SyllabusVersion, TopicProgress, User
from app.services.storage import storage


client = TestClient(app)


def test_account_export_and_deletion_cover_ingestion_and_plan_records() -> None:
    """Export and delete every owned record while anonymizing external review references."""
    email = f"lifecycle-{uuid4().hex}@example.com"
    registration = client.post("/api/v1/auth/register", json={"email": email, "name": "Lifecycle Learner", "password": "lifecycle-password"})
    assert registration.status_code == 201
    user_id = registration.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}
    storage_key = f"account-{uuid4().hex}.pdf"
    processed_key = f"processed/account-{uuid4().hex}.txt"
    storage.put_bytes(storage_key, b"private syllabus", content_type="application/pdf")
    storage.put_bytes(processed_key, b"private extracted text", content_type="text/plain")

    db = SessionLocal()
    try:
        owner = db.get(User, user_id)
        assert owner is not None
        course = Course(owner_id=user_id, code="LIFE1", title="Lifecycle Course", description="")
        db.add(course)
        db.flush()
        resource = Resource(course_id=course.id, title="syllabus.pdf", kind="syllabus_pdf", storage_key=storage_key, processed_key=processed_key, processing_status="processed")
        db.add(resource)
        db.flush()
        version = SyllabusVersion(course_id=course.id, label="Lifecycle syllabus", source_resource_id=resource.id)
        db.add(version)
        db.flush()
        concept = Concept(course_id=course.id, name="Lifecycle Concept", difficulty=2, syllabus_version_id=version.id, estimated_minutes=90)
        db.add(concept)
        db.flush()
        resource.concept_id = concept.id
        db.add(SyllabusRecord(syllabus_version_id=version.id, source_resource_id=resource.id, course_id=course.id, source_text="Lifecycle Concept", normalized_text="lifecycle concept", mapped_concept_id=concept.id, review_status="verified"))
        db.add(HistoricalExamQuestion(course_id=course.id, source="CIE", source_document="cie.pdf", source_resource_id=resource.id, exam_year=2026, prompt="Explain the lifecycle concept.", concept_id=concept.id, topic_label="Lifecycle Concept", question_kind="main", review_status="verified"))
        db.add(TopicProgress(user_id=user_id, concept_id=concept.id, completed=True, score=92))
        db.add(QuizAttempt(user_id=user_id, concept_id=concept.id, answer_index=0, correct=True, score=100))
        plan = StudyPlan(user_id=user_id, course_id=course.id, target_date=date.today(), daily_minutes=60)
        db.add(plan)
        db.flush()
        db.add(StudyPlanItem(plan_id=plan.id, concept_id=concept.id, scheduled_date=date.today(), minutes=60, sequence=0, explanation="fixture"))
        db.add(StudyPlanRevision(plan_id=plan.id, revision_number=1, event="generated", snapshot="[]"))
        db.add(ResourceConceptMapping(resource_id=resource.id, concept_id=concept.id, status="accepted", source="test", reviewed_by=user_id))
        db.add(AuditEvent(actor_id=user_id, event_type="fixture_created"))

        other_user = User(email=f"other-{uuid4().hex}@example.test", name="Other Learner", password_hash=hash_password("other-password"))
        db.add(other_user)
        db.flush()
        other_course = Course(owner_id=other_user.id, code="OTHER1", title="Other Course", description="")
        db.add(other_course)
        db.flush()
        other_concept = Concept(course_id=other_course.id, name="Other Concept", difficulty=1)
        other_resource = Resource(course_id=other_course.id, title="other.pdf", kind="document")
        db.add_all([other_concept, other_resource])
        db.flush()
        external_mapping = ResourceConceptMapping(resource_id=other_resource.id, concept_id=other_concept.id, status="accepted", source="test", reviewed_by=user_id)
        db.add(external_mapping)
        db.commit()
        course_id = course.id
        external_mapping_id = external_mapping.id
    finally:
        db.close()

    exported = client.get("/api/v1/auth/export", headers=headers)
    assert exported.status_code == 200
    payload = exported.json()
    assert {"syllabus_versions", "syllabus_records", "historical_exam_questions", "study_plan_items", "study_plan_revisions", "audit_events"}.issubset(payload)
    assert payload["syllabus_records"][0]["source_text"] == "Lifecycle Concept"
    assert payload["historical_exam_questions"][0]["source_document"] == "cie.pdf"

    deleted = client.post("/api/v1/auth/delete", headers=headers, json={"confirm_email": email})
    assert deleted.status_code == 204, deleted.text

    db = SessionLocal()
    try:
        assert db.get(User, user_id) is None
        assert db.scalar(select(func.count()).select_from(Course).where(Course.id == course_id)) == 0
        assert db.scalar(select(func.count()).select_from(SyllabusRecord).where(SyllabusRecord.course_id == course_id)) == 0
        assert db.scalar(select(func.count()).select_from(HistoricalExamQuestion).where(HistoricalExamQuestion.course_id == course_id)) == 0
        surviving_mapping = db.get(ResourceConceptMapping, external_mapping_id)
        assert surviving_mapping is not None
        assert surviving_mapping.reviewed_by is None
    finally:
        db.close()
    with pytest.raises(FileNotFoundError):
        storage.read_bytes(storage_key)
    with pytest.raises(FileNotFoundError):
        storage.read_bytes(processed_key)
