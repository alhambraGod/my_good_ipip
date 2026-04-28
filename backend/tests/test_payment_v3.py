"""tests/test_payment_v3.py — v3 payment endpoints."""
from fastapi.testclient import TestClient

from database import SessionLocal
from main import app
from models import Assessment


client = TestClient(app)


def _create_completed_assessment() -> str:
    """Helper: create a completed assessment in the DB and return its ID."""
    db = SessionLocal()
    a = Assessment(
        completed=True, paid=False, archetype_cell="IA",
        riasec_scores={"R": 10, "I": 18, "A": 15, "S": 8, "E": 11, "C": 13},
        ocean_scores={"openness": 80, "conscientiousness": 70, "extraversion": 50, "agreeableness": 60, "neuroticism": 40},
        ocean_percentiles={"openness": 92, "conscientiousness": 75, "extraversion": 50, "agreeableness": 62, "neuroticism": 35},
        holland_code="IAC",
    )
    db.add(a); db.commit(); db.refresh(a)
    aid = a.id
    db.close()
    return aid


def test_create_payment_intent_mock_mode(monkeypatch):
    monkeypatch.setenv("PAYMENT_MODE", "mock")
    aid = _create_completed_assessment()
    r = client.post("/api/v3/payment/create-intent", json={"assessment_id": aid})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["provider"] == "mock"
    assert "mock=true" in body["payment_url"]
    assert body["amount_inr"] in (49, 99)
    assert body["assessment_id"] == aid


def test_create_payment_intent_unknown_assessment_404():
    r = client.post("/api/v3/payment/create-intent", json={"assessment_id": "nonexistent-xyz"})
    assert r.status_code == 404


def test_create_payment_intent_incomplete_assessment_400():
    db = SessionLocal()
    a = Assessment(completed=False, paid=False)
    db.add(a); db.commit(); db.refresh(a)
    aid = a.id
    db.close()
    r = client.post("/api/v3/payment/create-intent", json={"assessment_id": aid})
    assert r.status_code == 400


def test_create_payment_intent_already_paid_400():
    db = SessionLocal()
    a = Assessment(completed=True, paid=True, archetype_cell="IA")
    db.add(a); db.commit(); db.refresh(a)
    aid = a.id
    db.close()
    r = client.post("/api/v3/payment/create-intent", json={"assessment_id": aid})
    assert r.status_code == 400


def test_promo_pricing_active_for_first_users(monkeypatch):
    """If paid_count < PROMO_MAX_REDEMPTIONS, price is PROMO + promo_active=True."""
    monkeypatch.setenv("PAYMENT_MODE", "mock")
    monkeypatch.setenv("PROMO_MAX_REDEMPTIONS", "1000")
    monkeypatch.setenv("PRICE_PROMO_INR", "49")
    monkeypatch.setenv("PRICE_FULL_INR", "99")
    aid = _create_completed_assessment()
    r = client.post("/api/v3/payment/create-intent", json={"assessment_id": aid}).json()
    assert r["promo_active"] is True
    assert r["amount_inr"] == 49


def test_verify_payment_endpoint_marks_paid_in_mock(monkeypatch):
    """In mock mode, /verify always confirms; assessment.paid flips True."""
    monkeypatch.setenv("PAYMENT_MODE", "mock")
    aid = _create_completed_assessment()
    # First create an intent (which sets payment_txn_id)
    client.post("/api/v3/payment/create-intent", json={"assessment_id": aid})
    # Now verify
    r = client.get(f"/api/v3/payment/verify/{aid}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["paid"] is True
    assert body["status"] == "confirmed"


def test_verify_payment_unknown_assessment_404():
    r = client.get("/api/v3/payment/verify/nonexistent-xyz")
    assert r.status_code == 404


def test_webhook_endpoint_exists():
    """Webhook accepts POST; behavior depends on signature/payload."""
    # In mock mode the driver's verify_webhook_signature returns True, so this should not 404.
    r = client.post(
        "/api/v3/payment/webhook/razorpay",
        json={"event": "payment_link.paid", "payload": {"payment_link": {"entity": {"id": "plink_unknown"}}}},
        headers={"x-razorpay-signature": "any-signature-mock-mode-accepts"},
    )
    # In mock mode signature passes, but plink_unknown won't match any assessment so the webhook just returns 200 with received=true.
    assert r.status_code in (200, 401)
