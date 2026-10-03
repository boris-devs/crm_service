from httpx import AsyncClient

from app.core.config import Settings, get_settings
from app.main import app


async def _create_tag(client: AsyncClient, name: str) -> int:
    response = await client.post("/api/tags", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


async def test_tags_are_unique_case_insensitive(client: AsyncClient) -> None:
    await _create_tag(client, "VIP")
    response = await client.post("/api/tags", json={"name": "vip"})
    assert response.status_code == 409


async def test_manual_lead_with_tags_and_filters(client: AsyncClient) -> None:
    vip = await _create_tag(client, "VIP")
    await _create_tag(client, "Сайт")

    created = await client.post(
        "/api/leads",
        json={"name": "Анна", "contact": "+79990000000", "request": "Лендинг", "tag_ids": [vip]},
    )
    assert created.status_code == 201
    lead = created.json()
    assert lead["source"] == "manual"
    assert lead["status"] == "new"
    assert [t["name"] for t in lead["tags"]] == ["VIP"]

    await client.post("/api/leads", json={"name": "Борис"})

    assert len((await client.get("/api/leads")).json()) == 2
    by_tag = (await client.get("/api/leads", params={"tag_id": vip})).json()
    assert [item["name"] for item in by_tag] == ["Анна"]
    by_search = (await client.get("/api/leads", params={"q": "Ленд"})).json()
    assert [item["name"] for item in by_search] == ["Анна"]

    tags = {t["name"]: t["lead_count"] for t in (await client.get("/api/tags")).json()}
    assert tags == {"VIP": 1, "Сайт": 0}


async def test_unknown_tag_on_create_is_404(client: AsyncClient) -> None:
    response = await client.post("/api/leads", json={"name": "Анна", "tag_ids": [999]})
    assert response.status_code == 404


async def test_update_tagging_and_delete(client: AsyncClient) -> None:
    tag = await _create_tag(client, "Горячий")
    lead_id = (await client.post("/api/leads", json={"name": "Анна"})).json()["id"]

    patched = await client.patch(f"/api/leads/{lead_id}", json={"status": "in_progress", "name": None})
    assert patched.json()["status"] == "in_progress"
    assert patched.json()["name"] == "Анна"

    tagged = await client.post(f"/api/leads/{lead_id}/tags/{tag}")
    assert [t["id"] for t in tagged.json()["tags"]] == [tag]
    untagged = await client.delete(f"/api/leads/{lead_id}/tags/{tag}")
    assert untagged.json()["tags"] == []

    assert (await client.delete(f"/api/leads/{lead_id}")).status_code == 204
    assert (await client.get(f"/api/leads/{lead_id}")).status_code == 404


async def test_deleting_tag_untags_leads(client: AsyncClient) -> None:
    tag = await _create_tag(client, "Временный")
    lead_id = (await client.post("/api/leads", json={"name": "Анна", "tag_ids": [tag]})).json()["id"]

    assert (await client.delete(f"/api/tags/{tag}")).status_code == 204
    assert (await client.get(f"/api/leads/{lead_id}")).json()["tags"] == []


async def test_basic_auth_when_password_set(client: AsyncClient) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(admin_username="admin", admin_password="secret")
    try:
        assert (await client.get("/api/leads")).status_code == 401
        assert (await client.get("/api/leads", auth=("admin", "wrong"))).status_code == 401
        assert (await client.get("/api/leads", auth=("admin", "secret"))).status_code == 200
        for protected in ("/", "/docs", "/openapi.json"):
            assert (await client.get(protected)).status_code == 401
        assert (await client.get("/openapi.json", auth=("admin", "secret"))).status_code == 200
        assert (await client.get("/health")).status_code == 200
    finally:
        app.dependency_overrides.clear()
