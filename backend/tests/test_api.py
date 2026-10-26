from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def auth_headers() -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": "demo@example.com", "password": "demo-password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_health() -> None:
    assert client.get("/health").json()["status"] == "ok"


def test_private_routes_require_authentication() -> None:
    assert client.get("/api/v1/courses").status_code == 401
    assert client.get("/api/v1/progress").status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "demo@example.com", "password": "wrong-password"}).status_code == 401


def test_courses_and_roadmap() -> None:
    headers = auth_headers()
    assert client.get("/api/v1/courses", headers=headers).status_code == 200
    roadmap = client.get("/api/v1/roadmap", headers=headers).json()
    assert roadmap and "scheduled_date" in roadmap[0]


def test_syllabus_analysis() -> None:
    response = client.post("/api/v1/syllabus/analyze", headers=auth_headers(), json={"text": "# Variables\n- Functions"})
    assert response.json()["count"] == 2
