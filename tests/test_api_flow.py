from fastapi.testclient import TestClient

from app.main import app


def test_login_and_progress_flow() -> None:
    client = TestClient(app)
    login = client.post("/api/v1/auth/login", json={"email": "student@example.com", "password": "demo"})
    assert login.status_code == 200
    progress = client.post("/api/v1/progress", json={"concept_id": "functions", "completed": True, "score": 90})
    assert progress.json()["saved"] is True
