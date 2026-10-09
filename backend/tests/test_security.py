import pytest
from fastapi.testclient import TestClient

from skill_inventory.main import create_app


@pytest.mark.parametrize("host", ["attacker.example", "localhost.attacker.example"])
def test_untrusted_host_cannot_read_management(host):
    with TestClient(create_app(), base_url=f"http://{host}") as client:
        assert client.get("/api/admin/skills").status_code == 400


@pytest.mark.parametrize(
    "origin", ["http://attacker.example", "null", "http://localhost.attacker.example:8080"]
)
@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_untrusted_origin_cannot_mutate_management(origin, method):
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.request(method, "/api/admin/skills", headers={"Origin": origin})
        assert response.status_code == 403


@pytest.mark.parametrize("origin", ["http://localhost:8080", "http://127.0.0.1:5173", None])
def test_local_origin_and_command_line_requests_remain_supported(client, draft, origin):
    headers = {"Origin": origin} if origin is not None else {}
    assert client.post("/api/admin/skills", json=draft, headers=headers).status_code == 201
