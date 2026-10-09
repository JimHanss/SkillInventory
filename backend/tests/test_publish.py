from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4


def test_publish_saves_submitted_form_instead_of_other_draft(client, draft):
    skill_id = client.post("/api/admin/skills", json=draft).json()["id"]
    form = {"name": "My form", "description": "My description", "content": "# My content"}
    other = {"name": "Other tab", "description": "", "content": "# Other content"}
    client.put(f"/api/admin/skills/{skill_id}", json=other)
    response = client.post(f"/api/admin/skills/{skill_id}/publish", json=form)
    assert response.status_code == 200
    assert response.json()["name"] == "My form"
    detail = client.get(f"/api/admin/skills/{skill_id}").json()
    assert detail["content"] == "# My content"
    assert detail["published"]["content"] == "# My content"
    assert client.get(f"/api/v1/skills/{draft['slug']}/content").text == "# My content"


def test_publish_rejects_invalid_form_without_changing_draft(client, draft):
    skill_id = client.post("/api/admin/skills", json=draft).json()["id"]
    response = client.post(
        f"/api/admin/skills/{skill_id}/publish",
        json={"name": "New name", "description": "", "content": " "},
    )
    assert response.status_code == 422
    detail = client.get(f"/api/admin/skills/{skill_id}").json()
    assert detail["name"] == draft["name"]
    assert detail["published"] is None


def test_concurrent_form_publishes_keep_each_submitted_snapshot(client, draft):
    skill_id = client.post("/api/admin/skills", json=draft).json()["id"]
    barrier = Barrier(2)

    def publish(name):
        barrier.wait(timeout=5)
        response = client.post(
            f"/api/admin/skills/{skill_id}/publish",
            json={"name": name, "description": name, "content": f"# {name}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == name
        return response.json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(publish, ["Tab A", "Tab B"]))
    assert {response["revision"] for response in responses} == {1, 2}
    latest = max(responses, key=lambda response: response["revision"])
    detail = client.get(f"/api/admin/skills/{skill_id}").json()
    assert detail["content"] == f"# {latest['name']}"
    assert detail["published"]["content"] == f"# {latest['name']}"


def test_publish_snapshot_lifecycle(client, draft):
    skill_id = client.post("/api/admin/skills", json=draft).json()["id"]
    content_path = f"/api/v1/skills/{draft['slug']}/content"
    assert client.get(content_path).status_code == 404
    assert client.get("/api/v1/skills").json()["total"] == 0
    assert client.post(f"/api/admin/skills/{skill_id}/publish").json()["revision"] == 1
    update = {key: draft[key] for key in ("name", "description", "content")}
    update["content"] = "# 新内容\r\n😀\n"
    client.put(f"/api/admin/skills/{skill_id}", json=update)
    assert client.get(content_path).text == draft["content"]
    assert client.post(f"/api/admin/skills/{skill_id}/publish").json()["revision"] == 2
    response = client.get(content_path)
    assert response.text == update["content"]
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert (
        client.get(f"/api/admin/skills/{skill_id}").json()["published"]["content"]
        == update["content"]
    )
    client.delete(f"/api/admin/skills/{skill_id}")
    assert client.get(content_path).status_code == 404
    assert client.get(f"/api/v1/skills/{draft['slug']}").status_code == 404
    assert client.get("/api/v1/skills").json()["total"] == 0
    assert client.post(f"/api/admin/skills/{uuid4()}/publish").status_code == 404


def test_simultaneous_first_publish_increments_revision(client, draft):
    skill_id = client.post("/api/admin/skills", json=draft).json()["id"]
    barrier = Barrier(2)

    def publish():
        barrier.wait(timeout=5)
        return client.post(f"/api/admin/skills/{skill_id}/publish")

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: publish(), range(2)))
    assert [response.status_code for response in responses] == [200, 200]
    assert {response.json()["revision"] for response in responses} == {1, 2}
    assert client.get(f"/api/v1/skills/{draft['slug']}").json()["revision"] == 2
