from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User as UserModel

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


def test_logout_revokes_existing_token_and_metrics_are_exposed() -> None:
    headers = auth_headers()
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "roadmap_http_requests_total" in metrics.text


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


def instructor_headers() -> dict[str, str]:
    db = SessionLocal()
    try:
        user = db.scalar(select(UserModel).where(UserModel.email == "exam-instructor@example.com"))
        if user is None:
            user = UserModel(email="exam-instructor@example.com", name="Exam Instructor", password_hash=hash_password("instructor-password"), role="instructor")
            db.add(user)
        else:
            user.role = "instructor"
        db.commit()
    finally:
        db.close()
    response = client.post("/api/v1/auth/login", json={"email": "exam-instructor@example.com", "password": "instructor-password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_roles_protect_admin_and_exam_import_is_rankable() -> None:
    student = auth_headers()
    assert client.get("/api/v1/admin/users", headers=student).status_code == 403
    course_id = client.get("/api/v1/courses", headers=student).json()[0]["id"]
    imported = client.post("/api/v1/exams/import", headers=instructor_headers(), json={"course_id": course_id, "source": "fixture-paper", "exam_year": 2025, "text": "1. Explain functions.\n2. Explain control flow."})
    assert imported.status_code == 201
    rankings = client.get("/api/v1/exams/rankings", headers=student, params={"course_id": course_id})
    assert rankings.status_code == 200


def test_admin_can_read_processing_queue_summary() -> None:
    db = SessionLocal()
    try:
        user = db.scalar(select(UserModel).where(UserModel.email == "processing-admin@example.com"))
        if user is None:
            user = UserModel(email="processing-admin@example.com", name="Processing Admin", password_hash=hash_password("admin-password"), role="admin")
            db.add(user)
        else:
            user.role = "admin"
        db.commit()
    finally:
        db.close()
    response = client.post("/api/v1/auth/login", json={"email": "processing-admin@example.com", "password": "admin-password"})
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    summary = client.get("/api/v1/admin/processing", headers=headers)
    assert summary.status_code == 200
    assert "counts" in summary.json()
