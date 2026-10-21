from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    assert client.get("/health").json()["status"] == "ok"


def test_courses_and_roadmap() -> None:
    assert client.get("/api/v1/courses").status_code == 200
    roadmap = client.get("/api/v1/roadmap").json()
    assert roadmap and "scheduled_date" in roadmap[0]


def test_syllabus_analysis() -> None:
    response = client.post("/api/v1/syllabus/analyze", json={"text": "# Variables\n- Functions"})
    assert response.json()["count"] == 2
