"""tests/test_archetypes.py — public archetype catalog endpoints."""

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_list_archetypes_returns_24():
    r = client.get("/api/v3/archetypes")
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body) == 24
    for entry in body:
        assert isinstance(entry["cell_id"], str)
        assert len(entry["cell_id"]) == 2
        assert entry["label_en"]
        assert entry["slogan_en"]
        assert isinstance(entry["rarity_pct"], (int, float))
    cell_ids = [e["cell_id"] for e in body]
    assert cell_ids == sorted(cell_ids)


def test_get_single_archetype_detail():
    r = client.get("/api/v3/archetypes/IA")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cell_id"] == "IA"
    assert isinstance(body["strengths_en"], list) and len(body["strengths_en"]) >= 3
    assert isinstance(body["growth_tips_en"], list) and len(body["growth_tips_en"]) >= 3
    assert isinstance(body["career_directions"], list) and len(body["career_directions"]) >= 3
    assert body["deep_description_en"]


def test_get_archetype_unknown_404():
    r = client.get("/api/v3/archetypes/ZZ")
    assert r.status_code == 404


def test_get_archetype_lowercase_normalised():
    r = client.get("/api/v3/archetypes/ia")
    assert r.status_code == 200
    assert r.json()["cell_id"] == "IA"
