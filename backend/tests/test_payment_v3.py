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


def test_get_price_public_endpoint():
    r = client.get("/api/v3/payment/price")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["amount_inr"] in (49, 99)
    assert body["price_full_inr"] == 99
    assert body["price_promo_inr"] == 49
    assert isinstance(body["promo_active"], bool)
    assert body["promo_remaining"] >= 0
    assert body["promo_cap"] >= 1
    if body["promo_active"]:
        assert body["amount_inr"] == body["price_promo_inr"]
    else:
        assert body["amount_inr"] == body["price_full_inr"]


def test_razorpay_order_in_mock_mode_returns_fallback(monkeypatch):
    """When PAYMENT_MODE=mock, /razorpay/order falls back to mock redirect URL."""
    monkeypatch.setenv("PAYMENT_MODE", "mock")
    import importlib, config
    importlib.reload(config)
    aid = _create_completed_assessment()
    r = client.post("/api/v3/payment/razorpay/order", json={"assessment_id": aid})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["provider"] == "mock"
    assert body["order_id"] is None
    assert body["mock_redirect_url"] and "mock=true" in body["mock_redirect_url"]
    assert body["amount_paise"] == body["amount_inr"] * 100


def test_razorpay_verify_signature_rejects_bogus(monkeypatch):
    """Mock mode rejects /razorpay/verify because assessment.payment_provider != razorpay."""
    monkeypatch.setenv("PAYMENT_MODE", "mock")
    import importlib, config
    importlib.reload(config)
    aid = _create_completed_assessment()
    client.post("/api/v3/payment/razorpay/order", json={"assessment_id": aid})
    r = client.post(
        "/api/v3/payment/razorpay/verify",
        json={
            "assessment_id": aid,
            "razorpay_order_id": "order_X",
            "razorpay_payment_id": "pay_X",
            "razorpay_signature": "deadbeef",
        },
    )
    assert r.status_code == 400


def test_razorpay_signature_acceptance_with_real_secret(monkeypatch):
    """Direct unit-style: valid HMAC against RAZORPAY_KEY_SECRET passes."""
    import hashlib
    import hmac
    import importlib

    monkeypatch.setenv("PAYMENT_MODE", "razorpay")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_xyz")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "test_secret_abc")
    import config
    importlib.reload(config)

    from services.payment.razorpay_driver import RazorpayDriver

    driver = RazorpayDriver()
    order_id, payment_id = "order_TEST", "pay_TEST"
    body = f"{order_id}|{payment_id}".encode()
    sig = hmac.new(b"test_secret_abc", body, hashlib.sha256).hexdigest()
    assert driver.verify_checkout_signature(order_id, payment_id, sig)
    assert not driver.verify_checkout_signature(order_id, payment_id, "wrong")


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
