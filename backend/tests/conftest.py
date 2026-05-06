"""Shared pytest fixtures."""
import importlib
import os
import sys
import tempfile

# Module-level: runs at conftest load, BEFORE any test module imports.
# Use setdefault so `DATABASE_URL=... pytest` overrides still work.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("PAYMENT_MODE", "mock")
# Logs in CI / local pytest stay in a tmp dir, never touch /var.
os.environ.setdefault(
    "LOG_ROOT",
    tempfile.mkdtemp(prefix="mindprism-test-logs-"),
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import pytest


@pytest.fixture(autouse=True)
def _reset_config_after_test():
    """Some tests `monkeypatch.setenv(...)` then `importlib.reload(config)`.

    monkeypatch's teardown undoes the env var but does NOT re-import config,
    leaving `config.settings` in the wrong state for subsequent tests
    (typically with stale RAZORPAY_KEY_ID and PAYMENT_MODE=razorpay,
    which causes the next test to make a real HTTPS request to Razorpay).
    This fixture forces a clean reload after every test, restoring the
    test-default settings derived from the env vars set above.
    """
    yield
    import config  # late import; module exists by now
    importlib.reload(config)
