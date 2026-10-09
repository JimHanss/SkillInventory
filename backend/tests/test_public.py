def test_only_published_metadata_and_literal_search(client, draft):
    for slug, name in [("one", "Name %"), ("two", "Name ordinary")]:
        item = client.post("/api/admin/skills", json={**draft, "slug": slug, "name": name}).json()
        assert client.post(f"/api/admin/skills/{item['id']}/publish").status_code == 200
    client.post("/api/admin/skills", json={**draft, "slug": "hidden"})
    result = client.get("/api/v1/skills?limit=1&offset=1").json()
    assert result["total"] == 2
    assert len(result["items"]) == 1
    assert "content" not in result["items"][0]
    assert "id" not in result["items"][0]
    assert client.get("/api/v1/skills", params={"q": "%"}).json()["total"] == 1
    assert client.get("/api/admin/skills?status=draft").json()["total"] == 1
    assert client.get("/api/admin/skills?status=published").json()["total"] == 2
    assert client.get("/api/v1/skills?limit=101").status_code == 422
