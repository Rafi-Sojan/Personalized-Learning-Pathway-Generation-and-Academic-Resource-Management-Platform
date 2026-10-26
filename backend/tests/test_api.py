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


def test_account_export_and_roadmap_history() -> None:
    headers = auth_headers()
    exported = client.get("/api/v1/auth/export", headers=headers)
    assert exported.status_code == 200
    assert {"user", "courses", "progress", "study_plans"}.issubset(exported.json())
    course_id = client.get("/api/v1/courses", headers=headers).json()[0]["id"]
    generated = client.post("/api/v1/roadmap/generate", headers=headers, json={"course_id": course_id, "target_date": "2099-01-01", "daily_minutes": 60})
    assert generated.status_code == 201
    history = client.get("/api/v1/roadmap/history", headers=headers)
    assert history.status_code == 200
    assert history.json()


def test_upload_rejects_pdf_with_invalid_magic_bytes() -> None:
    course_id = client.get("/api/v1/courses", headers=auth_headers()).json()[0]["id"]
    response = client.post("/api/v1/resources/upload", headers=auth_headers(), params={"course_id": course_id}, files={"file": ("document.pdf", b"not-a-pdf", "application/pdf")})
    assert response.status_code == 415
