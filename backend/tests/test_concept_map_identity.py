"""End-to-end coverage for source-aware repeated syllabus labels."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models import Concept, Resource
from app.services.storage import storage


client = TestClient(app)


def test_same_topic_label_in_different_units_creates_distinct_nodes() -> None:
    """Keep repeated child labels attached to their own unit and parent concept."""
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"identity-{uuid4().hex}@example.com",
            "name": "Identity Learner",
            "password": "identity-password",
        },
    )
    assert registration.status_code == 201
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}
    course_response = client.post(
        "/api/v1/courses",
        headers=headers,
        json={"code": "IDENT1", "title": "Identity Course", "description": ""},
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]
    processed_key = f"processed/identity-{uuid4().hex}.txt"
    storage.put_bytes(
        processed_key,
        b"[[PAGE 1]]\nUNIT I\nGraphs: Applications\n[[PAGE 2]]\nUNIT II\nNeural Networks: Applications",
        content_type="text/plain",
    )
    db = SessionLocal()
    try:
        source = Resource(
            course_id=course_id,
            title="identity-syllabus.pdf",
            kind="syllabus_pdf",
            processed_key=processed_key,
            processing_status="processed",
        )
        db.add(source)
        db.commit()
        source_id = source.id
    finally:
        db.close()

    generated = client.post(f"/api/v1/syllabus/sources/{source_id}/generate-map", headers=headers)
    assert generated.status_code == 200, generated.text
    db = SessionLocal()
    try:
        applications = list(
            db.scalars(
                select(Concept).where(Concept.course_id == course_id, Concept.name == "Applications")
            ).all()
        )
        assert len(applications) == 2
        assert {concept.unit_label for concept in applications} == {"I", "II"}
        assert len({concept.parent_concept_id for concept in applications}) == 2
        assert all(concept.parent_concept_id is not None for concept in applications)
    finally:
        db.close()
