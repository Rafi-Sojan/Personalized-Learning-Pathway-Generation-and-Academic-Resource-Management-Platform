"""Roadmap capacity and multi-day segmentation regression coverage."""

from datetime import date, timedelta
from uuid import uuid4

from app.api.v1.roadmap import generate_items
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Concept, Course, Resource, SyllabusVersion, User


def test_large_concept_is_split_across_daily_capacity() -> None:
    """Schedule a full 150-minute concept as bounded 60, 60, and 30 minute segments."""
    db = SessionLocal()
    try:
        user = User(email=f"roadmap-{uuid4().hex}@example.test", name="Roadmap Learner", password_hash=hash_password("roadmap-password"))
        db.add(user)
        db.flush()
        course = Course(owner_id=user.id, code="MAP1", title="Roadmap Course", description="")
        db.add(course)
        db.flush()
        resource = Resource(course_id=course.id, title="roadmap.pdf", kind="syllabus_pdf", processing_status="processed")
        db.add(resource)
        db.flush()
        version = SyllabusVersion(course_id=course.id, label="Roadmap syllabus", source_resource_id=resource.id)
        db.add(version)
        db.flush()
        concept = Concept(course_id=course.id, name="Long Topic", difficulty=3, syllabus_version_id=version.id, estimated_minutes=150)
        db.add(concept)
        db.commit()
        items = generate_items(db, user, course.id, date.today() + timedelta(days=2), daily_minutes=60)
        assert [item.minutes for item in items] == [60, 60, 30]
        assert [item.scheduled_date for item in items] == [date.today(), date.today() + timedelta(days=1), date.today() + timedelta(days=2)]
        assert {item.concept_id for item in items} == {concept.id}
    finally:
        db.close()


def test_preview_reports_partial_segment_without_truncating_estimate() -> None:
    """Use all preview capacity while explaining that the concept still needs more time."""
    db = SessionLocal()
    try:
        user = User(email=f"preview-{uuid4().hex}@example.test", name="Preview Learner", password_hash=hash_password("preview-password"))
        db.add(user)
        db.flush()
        course = Course(owner_id=user.id, code="MAP2", title="Preview Course", description="")
        db.add(course)
        db.flush()
        resource = Resource(course_id=course.id, title="preview.pdf", kind="syllabus_pdf", processing_status="processed")
        db.add(resource)
        db.flush()
        version = SyllabusVersion(course_id=course.id, label="Preview syllabus", source_resource_id=resource.id)
        db.add(version)
        db.flush()
        concept = Concept(course_id=course.id, name="Extended Topic", difficulty=3, syllabus_version_id=version.id, estimated_minutes=150)
        db.add(concept)
        db.commit()
        items = generate_items(db, user, course.id, date.today() + timedelta(days=1), daily_minutes=60, allow_partial=True)
        assert [item.minutes for item in items] == [60, 60]
        assert sum(item.minutes for item in items) == 120
        assert "preview schedules 120 of 150 minutes" in items[0].reason
    finally:
        db.close()
