"""Shared pytest fixtures."""
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
