"""Shared pytest fixtures."""
import os
import sys

# Module-level: runs at conftest load, BEFORE any test module imports.
# Use setdefault so `DATABASE_URL=... pytest` overrides still work.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("PAYMENT_MODE", "mock")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
