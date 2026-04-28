"""tests/test_assessment_v3.py — v3 assessment endpoints."""
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_get_demographic_questions():
    r = client.get("/api/v3/assessment/demographic")
    assert r.status_code == 200
    questions = r.json()
    assert len(questions) == 5
    for q in questions:
        assert q["id"].startswith("DEM_")
        assert q["instrument"] == "demographic"
        assert q["response_type"] == "single_choice"
        assert isinstance(q["options"], list)
        assert len(q["options"]) >= 3


def test_start_v3_assessment():
    payload = {
        "demographic": {
            "DEM_STAGE": "experienced",
            "DEM_AGE": "25_29",
            "DEM_GENDER": "male",
            "DEM_CITY_TIER": "tier1",
            "DEM_TOP_PRESSURE": "career",
        }
    }
    r = client.post("/api/v3/assessment/start", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "assessment_id" in body
    assert "questions" in body
    # 45 - 5 demographic = 40 returned
    assert len(body["questions"]) == 40
    assert "seed" in body


def test_submit_v3_assessment():
    """Full submit flow: start → simulate answers → submit → results."""
    start_payload = {
        "demographic": {
            "DEM_STAGE": "student", "DEM_AGE": "20_24", "DEM_GENDER": "female",
            "DEM_CITY_TIER": "tier1", "DEM_TOP_PRESSURE": "self_doubt",
        }
    }
    start = client.post("/api/v3/assessment/start", json=start_payload).json()
    assessment_id = start["assessment_id"]
    questions = start["questions"]

    answers = {q["id"]: ((i % 5) + 1) for i, q in enumerate(questions)}
    submit_payload = {"assessment_id": assessment_id, "answers": answers}
    r = client.post("/api/v3/assessment/submit", json=submit_payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["assessment_id"] == assessment_id
    assert "cell_id" in body
    assert len(body["cell_id"]) == 2  # 2-letter Holland cell
    assert "holland_code" in body
    assert len(body["holland_code"]) == 3
    assert "share_code" in body
    assert "careers_preview" in body
    assert len(body["careers_preview"]) >= 3
    # First career fully visible (locked: false), rest locked
    assert body["careers_preview"][0]["locked"] is False
    assert body["is_paid"] is False


def test_submit_already_completed_rejects():
    """Re-submitting an already-completed assessment returns 400."""
    start_payload = {
        "demographic": {
            "DEM_STAGE": "founder", "DEM_AGE": "30_34", "DEM_GENDER": "male",
            "DEM_CITY_TIER": "tier1", "DEM_TOP_PRESSURE": "career",
        }
    }
    start = client.post("/api/v3/assessment/start", json=start_payload).json()
    answers = {q["id"]: ((i % 5) + 1) for i, q in enumerate(start["questions"])}
    submit_payload = {"assessment_id": start["assessment_id"], "answers": answers}
    client.post("/api/v3/assessment/submit", json=submit_payload)
    # Second submit
    r = client.post("/api/v3/assessment/submit", json=submit_payload)
    assert r.status_code == 400


def test_get_results_after_submit():
    """GET /results returns the same shape as POST /submit response (idempotent)."""
    start_payload = {
        "demographic": {
            "DEM_STAGE": "switcher", "DEM_AGE": "30_34", "DEM_GENDER": "female",
            "DEM_CITY_TIER": "tier2", "DEM_TOP_PRESSURE": "money",
        }
    }
    start = client.post("/api/v3/assessment/start", json=start_payload).json()
    assessment_id = start["assessment_id"]
    answers = {q["id"]: ((i % 5) + 1) for i, q in enumerate(start["questions"])}
    client.post("/api/v3/assessment/submit", json={"assessment_id": assessment_id, "answers": answers})

    r = client.get(f"/api/v3/assessment/{assessment_id}/results")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["assessment_id"] == assessment_id
    assert body["is_paid"] is False


def test_get_results_unsubmitted_400():
    """GET /results before submit returns 400."""
    start_payload = {
        "demographic": {
            "DEM_STAGE": "fresher", "DEM_AGE": "20_24", "DEM_GENDER": "male",
            "DEM_CITY_TIER": "tier3", "DEM_TOP_PRESSURE": "curious",
        }
    }
    start = client.post("/api/v3/assessment/start", json=start_payload).json()
    r = client.get(f"/api/v3/assessment/{start['assessment_id']}/results")
    assert r.status_code == 400


def test_milestone_copy_endpoint():
    r = client.get("/api/v3/assessment/milestone?milestone=20&seed=test-seed")
    assert r.status_code == 200
    body = r.json()
    assert body["milestone"] == 20
    assert isinstance(body["text"], str) and len(body["text"]) >= 10


def test_milestone_copy_invalid_milestone_400():
    r = client.get("/api/v3/assessment/milestone?milestone=15&seed=x")
    assert r.status_code == 400


def test_attach_profile_with_jwt():
    import uuid

    email = f"u{uuid.uuid4().hex[:10]}@attach.example"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": "secret12", "name": "T"},
    )
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]
    start = client.post(
        "/api/v3/assessment/start",
        json={
            "demographic": {
                "DEM_STAGE": "student",
                "DEM_AGE": "20_24",
                "DEM_GENDER": "female",
                "DEM_CITY_TIER": "tier1",
                "DEM_TOP_PRESSURE": "self_doubt",
            }
        },
    ).json()
    aid = start["assessment_id"]
    r = client.post(
        f"/api/v3/assessment/{aid}/attach-profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True


def test_attach_profile_requires_auth():
    start = client.post(
        "/api/v3/assessment/start",
        json={
            "demographic": {
                "DEM_STAGE": "student",
                "DEM_AGE": "20_24",
                "DEM_GENDER": "female",
                "DEM_CITY_TIER": "tier1",
                "DEM_TOP_PRESSURE": "self_doubt",
            }
        },
    ).json()
    aid = start["assessment_id"]
    r = client.post(f"/api/v3/assessment/{aid}/attach-profile")
    assert r.status_code == 401
