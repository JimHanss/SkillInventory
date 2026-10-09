from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from skill_inventory.main import create_app


def test_health_checks_database():
    calls = []

    def check():
        calls.append(True)

    with TestClient(create_app(health_check=check), base_url="http://localhost") as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert calls


def test_health_hides_connection_failure():
    def check():
        raise OperationalError("secret-password", None, Exception("private host"))

    with TestClient(create_app(health_check=check), base_url="http://localhost") as client:
        response = client.get("/healthz")
    assert response.status_code == 503
    assert "secret-password" not in response.text
    assert "private host" not in response.text
