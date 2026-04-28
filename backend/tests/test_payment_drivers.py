"""tests/test_payment_drivers.py — payment driver abstraction + implementations."""
import pytest

from services.payment.base import PaymentDriver, PaymentIntent
from services.payment.mock import MockDriver


def test_payment_intent_dataclass():
    intent = PaymentIntent(
        provider="mock",
        assessment_id="abc-123",
        payment_url="https://example.com/mock",
        amount_inr=49,
    )
    assert intent.provider == "mock"
    assert intent.amount_inr == 49


def test_mock_driver_creates_intent():
    driver = MockDriver()
    intent = driver.create_payment_intent("test-assessment-id", amount_inr=49)
    assert isinstance(intent, PaymentIntent)
    assert "mock=true" in intent.payment_url
    assert intent.provider == "mock"
    assert intent.amount_inr == 49


def test_mock_driver_verifies_always_paid():
    driver = MockDriver()
    assert driver.verify_payment("any-txn-id") is True


def test_mock_driver_webhook_signature_always_ok():
    driver = MockDriver()
    assert driver.verify_webhook_signature(b"any payload", "any sig") is True


def test_mock_driver_provider_name():
    driver = MockDriver()
    assert driver.provider_name == "mock"


def test_payment_driver_protocol_runtime_check():
    """All drivers conform to the PaymentDriver protocol."""
    driver: PaymentDriver = MockDriver()
    assert hasattr(driver, "create_payment_intent")
    assert hasattr(driver, "verify_payment")
    assert hasattr(driver, "verify_webhook_signature")


def test_factory_returns_mock_in_mock_mode(monkeypatch):
    monkeypatch.setenv("PAYMENT_MODE", "mock")
    import importlib
    import config
    importlib.reload(config)
    from services.payment.factory import get_payment_driver
    driver = get_payment_driver()
    assert isinstance(driver, MockDriver)


def test_razorpay_driver_init_requires_credentials(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_ID", "")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "")
    import importlib
    import config
    importlib.reload(config)
    from services.payment.razorpay_driver import RazorpayDriver
    with pytest.raises(ValueError, match="RAZORPAY"):
        RazorpayDriver()


def test_razorpay_signature_verification(monkeypatch):
    """Razorpay driver verifies HMAC-SHA256 signatures correctly."""
    monkeypatch.setenv("RAZORPAY_KEY_ID", "test_key")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "test_secret")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "webhook_secret_123")
    import importlib
    import config
    importlib.reload(config)
    from services.payment.razorpay_driver import RazorpayDriver
    import hmac, hashlib

    driver = RazorpayDriver()
    payload = b'{"event":"test"}'
    expected_sig = hmac.new(b"webhook_secret_123", payload, hashlib.sha256).hexdigest()
    assert driver.verify_webhook_signature(payload, expected_sig) is True
    assert driver.verify_webhook_signature(payload, "wrong_sig") is False
