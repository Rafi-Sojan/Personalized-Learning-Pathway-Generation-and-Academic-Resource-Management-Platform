from fastapi.testclient import TestClient

from app.main import app


def test_login_and_progress_flow() -> None:
    client = TestClient(app)
    login = client.post("/api/v1/auth/login", json={"email": "demo@example.com", "password": "demo-password"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    progress = client.post("/api/v1/progress", headers=headers, json={"concept_id": "functions", "completed": True, "score": 90})
    assert progress.json()["saved"] is True
