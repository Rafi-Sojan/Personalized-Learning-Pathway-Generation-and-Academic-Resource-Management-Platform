from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models import Concept


def test_login_and_progress_flow() -> None:
    """Register a learner with an owned concept and persist progress without seed data."""
    client = TestClient(app)
    registration = client.post("/api/v1/auth/register", json={"email": "flow@example.com", "name": "Flow Learner", "password": "flow-password"})
    assert registration.status_code == 201
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}
    course = client.post("/api/v1/courses", headers=headers, json={"code": "FLOW1", "title": "Flow Test", "description": ""})
    assert course.status_code == 201
    db = SessionLocal()
    try:
        concept = Concept(course_id=course.json()["id"], name="Functions", difficulty=2)
        db.add(concept)
        db.commit()
        db.refresh(concept)
        concept_id = concept.id
    finally:
        db.close()
    progress = client.post("/api/v1/progress", headers=headers, json={"concept_id": concept_id, "completed": True, "score": 90})
    assert progress.status_code == 200
    assert progress.json()["saved"] is True
