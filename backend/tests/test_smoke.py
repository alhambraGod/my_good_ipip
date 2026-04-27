"""tests/test_smoke.py — verify pytest setup works."""

def test_pytest_runs():
    assert True

def test_imports_work():
    from config import settings
    assert settings is not None
