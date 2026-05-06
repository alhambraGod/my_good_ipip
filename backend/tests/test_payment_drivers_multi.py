"""tests/test_payment_drivers_multi.py — pure-logic checks for the new drivers.

These tests exercise hash/sig math, deep-link construction, and the
factory registry **without** any real HTTP calls (which require sandbox
credentials we don't ship).
"""

import base64
import hashlib
import hmac
import importlib

import pytest

import config


# ---------------------------------------------------------------------------
# Factory registry
# ---------------------------------------------------------------------------

def test_factory_default_falls_back_to_payment_mode(monkeypatch):
    monkeypatch.setattr(config.settings, "PAYMENT_MODE", "mock")
    monkeypatch.setattr(config.settings, "PAYMENT_DEFAULT_DRIVER", "")
    monkeypatch.setattr(config.settings, "PAYMENT_DRIVERS_ENABLED", "")
    from services.payment.factory import default_driver_id

    assert default_driver_id() == "mock"


def test_factory_explicit_default_wins(monkeypatch):
    monkeypatch.setattr(config.settings, "PAYMENT_DEFAULT_DRIVER", "razorpay")
    monkeypatch.setattr(config.settings, "PAYMENT_MODE", "mock")
    from services.payment.factory import default_driver_id

    assert default_driver_id() == "razorpay"


def test_list_provider_infos_includes_only_enabled(monkeypatch):
    monkeypatch.setattr(config.settings, "PAYMENT_DRIVERS_ENABLED", "mock")
    monkeypatch.setattr(config.settings, "PAYMENT_DEFAULT_DRIVER", "mock")
    from services.payment.factory import list_provider_infos

    infos = list_provider_infos()
    ids = [p.id for p in infos]
    assert ids == ["mock"]
    assert infos[0].recommended is True


def test_list_provider_infos_skips_unconfigured_driver(monkeypatch):
    """A driver that fails to instantiate (missing creds) is hidden, not crashed."""
    monkeypatch.setattr(config.settings, "PAYMENT_DRIVERS_ENABLED", "mock,razorpay")
    monkeypatch.setattr(config.settings, "RAZORPAY_KEY_ID", "")
    monkeypatch.setattr(config.settings, "RAZORPAY_KEY_SECRET", "")
    from services.payment.factory import list_provider_infos

    ids = [p.id for p in list_provider_infos()]
    assert "mock" in ids
    assert "razorpay" not in ids   # missing creds → hidden


def test_get_payment_driver_unknown_id_raises():
    from services.payment.factory import get_payment_driver

    with pytest.raises(ValueError):
        get_payment_driver("whatever")


# ---------------------------------------------------------------------------
# UPI Intent — pure URL builder
# ---------------------------------------------------------------------------

def test_upi_intent_builds_npci_deeplink(monkeypatch):
    monkeypatch.setattr(config.settings, "UPI_VPA", "mindprism@hdfcbank")
    monkeypatch.setattr(config.settings, "UPI_DISPLAY_NAME", "MindPrism")
    from services.payment.upi_intent_driver import UPIIntentDriver

    intent = UPIIntentDriver().create_payment_intent("a-1234", amount_inr=49)
    assert intent.payment_url.startswith("upi://pay?")
    assert "pa=mindprism%40hdfcbank" in intent.payment_url
    assert "am=49.00" in intent.payment_url
    assert "cu=INR" in intent.payment_url
    assert intent.txn_id and intent.txn_id.startswith("MIND")
    # qr_code_data_url is optional (depends on segno being installed)
    if intent.qr_code_data_url:
        assert intent.qr_code_data_url.startswith("data:image/png;base64,")


def test_upi_intent_verify_payment_returns_false(monkeypatch):
    """No automated reconciliation — verify_payment is always False
    until ops manually marks it via the admin endpoint."""
    monkeypatch.setattr(config.settings, "UPI_VPA", "mindprism@hdfcbank")
    from services.payment.upi_intent_driver import UPIIntentDriver

    assert UPIIntentDriver().verify_payment("MIND12345678") is False
    assert UPIIntentDriver().verify_payment(None) is False


def test_upi_driver_requires_vpa(monkeypatch):
    monkeypatch.setattr(config.settings, "UPI_VPA", "")
    from services.payment.upi_intent_driver import UPIIntentDriver

    with pytest.raises(ValueError):
        UPIIntentDriver()


# ---------------------------------------------------------------------------
# PayU — request hash + response hash + webhook verify
# ---------------------------------------------------------------------------

def _fixture_payu(monkeypatch):
    monkeypatch.setattr(config.settings, "PAYU_MERCHANT_KEY", "PAYUKEY")
    monkeypatch.setattr(config.settings, "PAYU_MERCHANT_SALT", "PAYUSALT")
    monkeypatch.setattr(config.settings, "PAYU_API_BASE", "https://test.payu.in")


def test_payu_request_hash_matches_spec(monkeypatch):
    _fixture_payu(monkeypatch)
    from services.payment.payu_driver import PayUDriver

    drv = PayUDriver()
    h = drv._hash_request(
        txnid="T1", amount="49.00",
        productinfo="MindPrism Report",
        firstname="User", email="user@mindprism.in",
    )
    raw = "PAYUKEY|T1|49.00|MindPrism Report|User|user@mindprism.in|||||||||||PAYUSALT"
    assert h == hashlib.sha512(raw.encode()).hexdigest()


def test_payu_response_hash_matches_spec(monkeypatch):
    _fixture_payu(monkeypatch)
    from services.payment.payu_driver import PayUDriver

    drv = PayUDriver()
    h = drv.hash_response(
        txnid="T1", amount="49.00", productinfo="X",
        firstname="User", email="user@mindprism.in", status="success",
    )
    raw = "PAYUSALT|success||||||||||user@mindprism.in|User|X|49.00|T1|PAYUKEY"
    assert h == hashlib.sha512(raw.encode()).hexdigest()


def test_payu_webhook_verifies_form_post(monkeypatch):
    _fixture_payu(monkeypatch)
    from services.payment.payu_driver import PayUDriver

    drv = PayUDriver()
    # Build a body that PayU would POST back as the merchant callback.
    h = drv.hash_response(
        txnid="T1", amount="49.00", productinfo="X",
        firstname="User", email="u@m.in", status="success",
    )
    body = (
        "txnid=T1&amount=49.00&productinfo=X&firstname=User&"
        "email=u%40m.in&status=success&hash=" + h
    ).encode()
    assert drv.verify_webhook_signature(body, "ignored") is True

    # Tampered hash → False
    tampered = body.replace(h.encode(), b"deadbeef")
    assert drv.verify_webhook_signature(tampered, "") is False


def test_payu_create_intent_returns_form_url(monkeypatch):
    _fixture_payu(monkeypatch)
    from services.payment.payu_driver import PayUDriver

    drv = PayUDriver()
    intent = drv.create_payment_intent("aid-001", amount_inr=49)
    assert intent.provider == "payu"
    assert intent.payment_url.endswith("/_payment")
    assert intent.client_payload["method"] == "POST"
    assert intent.client_payload["fields"]["amount"] == "49.00"
    assert intent.client_payload["fields"]["udf1"] == "aid-001"
    # Hash matches spec (we round-trip)
    expected = drv._hash_request(
        txnid=intent.client_payload["fields"]["txnid"],
        amount="49.00", productinfo="MindPrism Report",
        firstname="User", email="user@mindprism.in",
    )
    assert intent.client_payload["fields"]["hash"] == expected


# ---------------------------------------------------------------------------
# Cashfree — webhook signature math
# ---------------------------------------------------------------------------

def test_cashfree_webhook_signature_round_trip(monkeypatch):
    monkeypatch.setattr(config.settings, "CASHFREE_CLIENT_ID", "cf-id")
    monkeypatch.setattr(config.settings, "CASHFREE_CLIENT_SECRET", "cf-sec")
    monkeypatch.setattr(config.settings, "CASHFREE_WEBHOOK_SECRET", "cf-wb-secret")
    from services.payment.cashfree_driver import CashfreeDriver

    drv = CashfreeDriver()
    body = b'{"type":"PAYMENT_SUCCESS_WEBHOOK","data":{"order":{"order_id":"X"}}}'
    ts = "1715000000"
    sig = base64.b64encode(
        hmac.new(b"cf-wb-secret", (ts + body.decode()).encode(), hashlib.sha256).digest()
    ).decode()

    assert drv.verify_webhook_signature(body, f"{ts}:{sig}") is True
    assert drv.verify_webhook_signature(body, f"{ts}:wrong") is False
    assert drv.verify_webhook_signature(body, "no-colon") is False


def test_cashfree_requires_creds(monkeypatch):
    monkeypatch.setattr(config.settings, "CASHFREE_CLIENT_ID", "")
    monkeypatch.setattr(config.settings, "CASHFREE_CLIENT_SECRET", "")
    from services.payment.cashfree_driver import CashfreeDriver

    with pytest.raises(ValueError):
        CashfreeDriver()


# ---------------------------------------------------------------------------
# /api/v3/payment/providers endpoint
# ---------------------------------------------------------------------------

def test_providers_endpoint_lists_only_enabled(monkeypatch):
    monkeypatch.setattr(config.settings, "PAYMENT_DRIVERS_ENABLED", "mock")
    monkeypatch.setattr(config.settings, "PAYMENT_DEFAULT_DRIVER", "mock")
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    r = client.get("/api/v3/payment/providers")
    assert r.status_code == 200
    body = r.json()
    assert body["default"] == "mock"
    assert [p["id"] for p in body["providers"]] == ["mock"]
    assert body["providers"][0]["recommended"] is True


def test_providers_endpoint_with_upi_only(monkeypatch):
    monkeypatch.setattr(config.settings, "PAYMENT_DRIVERS_ENABLED", "upi,mock")
    monkeypatch.setattr(config.settings, "PAYMENT_DEFAULT_DRIVER", "upi")
    monkeypatch.setattr(config.settings, "UPI_VPA", "mindprism@hdfcbank")
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    body = client.get("/api/v3/payment/providers").json()
    ids = [p["id"] for p in body["providers"]]
    assert "upi" in ids and "mock" in ids
    assert body["default"] == "upi"
