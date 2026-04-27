"""Shared pytest fixtures."""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session", autouse=True)
def _set_test_env():
    os.environ["APP_ENV"] = "test"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["PAYMENT_MODE"] = "mock"
    yield
