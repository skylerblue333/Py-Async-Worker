from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_and_get_task():
    r1 = client.post("/api/v1/tasks", json={"name": "email", "payload": {"to": "a@b.com"}})
    assert r1.status_code == 200
    tid = r1.json()["task_id"]
    r2 = client.get(f"/api/v1/tasks/{tid}")
    assert r2.status_code == 200
    assert r2.json()["name"] == "email"

