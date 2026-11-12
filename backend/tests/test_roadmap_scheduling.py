"""Roadmap capacity and multi-day segmentation regression coverage."""

from datetime import date, timedelta
from uuid import uuid4
from typing import TypedDict
from app.api.v1.roadmap import _preview_items, generate_items
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Concept, Course, Resource, SyllabusVersion, User
from ml.scheduling.course_roadmap import ActivityDemand, ScheduledActivity


class SharedActivityFields(TypedDict):
    """Typed fields common to demands and scheduled activities."""

    course_id: str
    course_code: str
    course_title: str
    syllabus_version_id: str | None
    unit_label: str | None
    source_page: int | None
    assessment_scope: str
    activity_type: str
    modality: str
    minutes: int
    reason: str
    evidence_question_ids: tuple[str, ...]


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


def test_preview_discloses_fully_omitted_later_activities() -> None:
    """Report total omitted work even when capacity ends exactly between activity demands."""
    shared: SharedActivityFields = {
        "course_id": "course-1",
        "course_code": "MAP3",
        "course_title": "Preview Disclosure",
        "syllabus_version_id": "version-1",
        "unit_label": "I",
        "source_page": 1,
        "assessment_scope": "both",
        "activity_type": "learn",
        "modality": "lecture",
        "minutes": 60,
        "reason": "source ordered",
        "evidence_question_ids": (),
    }
    first = ActivityDemand(demand_id="first", concept_id="concept-1", concept_name="First", **shared)
    second = ActivityDemand(demand_id="second", concept_id="concept-2", concept_name="Second", **shared)
    scheduled = ScheduledActivity(
        demand_id="first",
        concept_id="concept-1",
        concept_name="First",
        scheduled_date=date.today(),
        **shared,
    )
    items = _preview_items([scheduled], [first, second])
    assert "preview covers 60 of 120 total minutes" in items[-1].reason
