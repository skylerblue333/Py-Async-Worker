import time

from fastapi.testclient import TestClient

from src.main import app


def wait_for_terminal(client: TestClient, task_id: str) -> dict:
    for _ in range(50):
        response = client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        task = response.json()
        if task["state"] in {"succeeded", "failed"}:
            return task
        time.sleep(0.01)
    raise AssertionError("task did not reach a terminal state")


def test_health_and_readiness() -> None:
    with TestClient(app) as client:
        assert client.get("/healthz").json()["status"] == "ok"
        ready = client.get("/readyz")
        assert ready.status_code == 200
        assert ready.json()["ready"] is True


def test_uppercase_task_runs_to_completion() -> None:
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/tasks",
            json={"operation": "uppercase", "payload": {"text": "sky coin"}},
        )
        assert created.status_code == 202
        task = wait_for_terminal(client, created.json()["task_id"])
        assert task["state"] == "succeeded"
        assert task["result"] == {"text": "SKY COIN"}


def test_sum_task_validates_payload() -> None:
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/tasks",
            json={"operation": "sum", "payload": {"values": [1, 2.5, 3]}},
        )
        task = wait_for_terminal(client, created.json()["task_id"])
        assert task["state"] == "succeeded"
        assert task["result"] == {"sum": 6.5}

        invalid = client.post(
            "/api/v1/tasks",
            json={"operation": "sum", "payload": {"values": [1, "two"]}},
        )
        failed = wait_for_terminal(client, invalid.json()["task_id"])
        assert failed["state"] == "failed"
        assert "numbers" in failed["error"]


def test_rejects_unknown_operation_and_large_payload() -> None:
    with TestClient(app) as client:
        unknown = client.post(
            "/api/v1/tasks",
            json={"operation": "shell", "payload": {"command": "whoami"}},
        )
        assert unknown.status_code == 422

        oversized = client.post(
            "/api/v1/tasks",
            json={"operation": "echo", "payload": {"value": "x" * 20_000}},
        )
        assert oversized.status_code == 413


def test_missing_task_is_404() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/tasks/not-a-real-id").status_code == 404
