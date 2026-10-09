import pytest


def test_draft_lifecycle_and_slug_conflict(client, draft):
    created = client.post("/api/admin/skills", json=draft)
    assert created.status_code == 201
    skill_id = created.json()["id"]
    assert created.json()["content"] == draft["content"]
    assert client.post("/api/admin/skills", json=draft).status_code == 409
    listing = client.get("/api/admin/skills").json()
    assert listing["total"] == 1
    assert "content" not in listing["items"][0]
    update = {key: draft[key] for key in ("name", "description", "content")}
    assert (
        client.put(f"/api/admin/skills/{skill_id}", json={**update, "slug": "other"}).status_code
        == 422
    )
    update["content"] = "---\nname: kept\n---\n<script>text</script>\r\n"
    assert (
        client.put(f"/api/admin/skills/{skill_id}", json=update).json()["content"]
        == update["content"]
    )
    assert client.delete(f"/api/admin/skills/{skill_id}").status_code == 204
    assert client.get(f"/api/admin/skills/{skill_id}").status_code == 404


@pytest.mark.parametrize(
    "field,value",
    [
        ("slug", "Bad"),
        ("slug", "a" * 65),
        ("slug", "-bad"),
        ("slug", "bad-"),
        ("name", " "),
        ("name", "x" * 121),
        ("content", "\n "),
        ("description", "x" * 1001),
        ("content", "😀" * 65536 + "x"),
    ],
    ids=[
        "uppercase",
        "long-slug",
        "leading-dash",
        "trailing-dash",
        "blank-name",
        "long-name",
        "blank-content",
        "long-description",
        "utf8-over-limit",
    ],
)
def test_invalid_inputs(client, draft, field, value):
    assert client.post("/api/admin/skills", json={**draft, field: value}).status_code == 422


def test_utf8_limit_and_search_literals(client, draft):
    text = "😀" * 65536
    assert (
        client.post("/api/admin/skills", json={**draft, "content": text}).json()["content"] == text
    )
    for index, symbol in enumerate(["%", "_", "'"]):
        assert (
            client.post(
                "/api/admin/skills",
                json={**draft, "slug": f"literal-{index}", "name": f"Name {symbol}"},
            ).status_code
            == 201
        )
        result = client.get("/api/admin/skills", params={"q": symbol}).json()
        assert result["total"] == 1
        assert result["items"][0]["name"] == f"Name {symbol}"
    for query in ("limit=101", "offset=-1", "status=unknown"):
        assert client.get(f"/api/admin/skills?{query}").status_code == 422
    assert client.get("/api/admin/skills?limit=2&offset=1").json()["total"] == 4
