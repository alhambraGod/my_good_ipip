"""tests/test_v3_e2e.py — full v3 backend user journey.

Walks through:
  1. GET /api/v3/assessment/demographic   — fetch Q1-5
  2. POST /api/v3/assessment/start         — submit demographic, get 40 questions
  3. GET /api/v3/assessment/milestone      — fetch progress copy at Q20
  4. POST /api/v3/assessment/submit        — submit answers, get free results
  5. GET /api/v3/report/{id}               — 402 (unpaid)
  6. POST /api/v3/payment/create-intent    — create mock payment intent
  7. GET /api/v3/payment/verify/{id}       — confirm payment (mock auto-pays)
  8. GET /api/v3/report/{id}               — 200 with full report
  9. GET /s/{share_code}                   — 302 redirect to canonical URL
"""
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_full_v3_journey_mock_payment(monkeypatch):
    monkeypatch.setenv("PAYMENT_MODE", "mock")
    import importlib, config
    importlib.reload(config)

    # 1. Get demographic Q1-5
    r = client.get("/api/v3/assessment/demographic")
    assert r.status_code == 200
    demographic_qs = r.json()
    assert len(demographic_qs) == 5
    expected_ids = {"DEM_STAGE", "DEM_AGE", "DEM_GENDER", "DEM_CITY_TIER", "DEM_TOP_PRESSURE"}
    assert {q["id"] for q in demographic_qs} == expected_ids

    # 2. Start assessment with demographic answers
    start_payload = {
        "demographic": {
            "DEM_STAGE": "experienced", "DEM_AGE": "25_29", "DEM_GENDER": "male",
            "DEM_CITY_TIER": "tier1", "DEM_TOP_PRESSURE": "career",
        }
    }
    r = client.post("/api/v3/assessment/start", json=start_payload)
    assert r.status_code == 200, r.text
    start = r.json()
    assessment_id = start["assessment_id"]
    questions = start["questions"]
    seed = start["seed"]
    assert len(questions) == 40

    # 3. Get milestone copy at Q20
    r = client.get(f"/api/v3/assessment/milestone?milestone=20&seed={seed}")
    assert r.status_code == 200
    milestone = r.json()
    assert milestone["milestone"] == 20
    assert isinstance(milestone["text"], str) and len(milestone["text"]) >= 10

    # 4. Submit answers (synthetic 1-5 cycle)
    answers = {q["id"]: ((i % 5) + 1) for i, q in enumerate(questions)}
    r = client.post("/api/v3/assessment/submit", json={"assessment_id": assessment_id, "answers": answers})
    assert r.status_code == 200, r.text
    result = r.json()
    assert result["is_paid"] is False
    assert "share_code" in result and len(result["share_code"]) > 0
    cell_id = result["cell_id"]
    assert len(cell_id) == 2

    # Free preview rules: career #1 unlocked, careers #2+ locked
    careers_preview = result["careers_preview"]
    assert len(careers_preview) >= 3
    assert careers_preview[0]["locked"] is False
    assert careers_preview[0]["tagline_en"] is not None  # career #1 has tagline
    if len(careers_preview) > 1:
        assert careers_preview[1]["locked"] is True
        assert careers_preview[1]["tagline_en"] is None  # locked careers hide tagline

    # 5. Try to fetch report — strict (no dev preview) → 402.
    import config as _cfg
    monkeypatch.setattr(_cfg.settings, "ALLOW_FREE_REPORT", False)
    r = client.get(f"/api/v3/report/{assessment_id}")
    assert r.status_code == 402

    # 6. Create payment intent
    r = client.post("/api/v3/payment/create-intent", json={"assessment_id": assessment_id})
    assert r.status_code == 200, r.text
    intent = r.json()
    assert intent["provider"] == "mock"
    assert "mock=true" in intent["payment_url"]
    assert intent["amount_inr"] in (49, 99)

    # 7. Verify payment (mock auto-confirms)
    r = client.get(f"/api/v3/payment/verify/{assessment_id}")
    assert r.status_code == 200, r.text
    verify = r.json()
    assert verify["paid"] is True
    assert verify["status"] == "confirmed"

    # 8. Now fetch report — should 200 with full content
    r = client.get(f"/api/v3/report/{assessment_id}")
    assert r.status_code == 200, r.text
    report = r.json()
    assert report["cell_id"] == cell_id
    assert len(report["strengths_en"]) == 5
    assert len(report["growth_tips_en"]) == 5
    assert len(report["careers"]) >= 3

    # 9. Resolve share code → 302 redirect
    short = client.get(f"/s/{result['share_code']}", follow_redirects=False)
    assert short.status_code == 302
    assert "/results/" in short.headers.get("location", "")


def test_full_v3_journey_idempotent_results():
    """Submit once; GET /results returns the same shape repeatedly."""
    start_payload = {
        "demographic": {
            "DEM_STAGE": "student", "DEM_AGE": "20_24", "DEM_GENDER": "female",
            "DEM_CITY_TIER": "tier2", "DEM_TOP_PRESSURE": "self_doubt",
        }
    }
    start = client.post("/api/v3/assessment/start", json=start_payload).json()
    assessment_id = start["assessment_id"]
    answers = {q["id"]: ((i % 5) + 1) for i, q in enumerate(start["questions"])}
    submit_response = client.post("/api/v3/assessment/submit", json={"assessment_id": assessment_id, "answers": answers}).json()

    # Re-fetch via /results
    results_response = client.get(f"/api/v3/assessment/{assessment_id}/results").json()

    # Cell ID, slogan, holland_code should match exactly
    assert results_response["cell_id"] == submit_response["cell_id"]
    assert results_response["holland_code"] == submit_response["holland_code"]
    assert results_response["slogan_en"] == submit_response["slogan_en"]
    assert results_response["share_code"] == submit_response["share_code"]


def test_full_v3_journey_demographic_drives_dynamic_picks():
    """Different demographics produce different INT-pool selections (proves the dynamic phase works)."""
    student_start = client.post("/api/v3/assessment/start", json={
        "demographic": {"DEM_STAGE": "student", "DEM_AGE": "20_24", "DEM_GENDER": "female",
                         "DEM_CITY_TIER": "tier2", "DEM_TOP_PRESSURE": "self_doubt"}
    }).json()
    experienced_start = client.post("/api/v3/assessment/start", json={
        "demographic": {"DEM_STAGE": "experienced", "DEM_AGE": "30_34", "DEM_GENDER": "male",
                         "DEM_CITY_TIER": "tier1", "DEM_TOP_PRESSURE": "money"}
    }).json()

    student_int_ids = [q["id"] for q in student_start["questions"] if q["id"].startswith("INT_")]
    experienced_int_ids = [q["id"] for q in experienced_start["questions"] if q["id"].startswith("INT_")]

    # Both should have ~16 INT items
    assert len(student_int_ids) >= 12
    assert len(experienced_int_ids) >= 12
    # Different demographics → different INT picks (at least some divergence)
    assert set(student_int_ids) != set(experienced_int_ids), (
        "Different demographics should drive different dynamic INT picks"
    )
