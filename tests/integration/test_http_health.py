"""Integration-level HTTP test stubs."""

from fastapi.testclient import TestClient

from loans.main import create_app


def test_healthcheck_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/loans/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
