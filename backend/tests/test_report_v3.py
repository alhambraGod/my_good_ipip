"""tests/test_report_v3.py — v3 report endpoints (paid-only + dev preview)."""
from copy import copy

from fastapi.testclient import TestClient

import config
from database import SessionLocal
from main import app
from models import Assessment


client = TestClient(app)


def _override_settings(**fields):
    """Return a shallow copy of `config.settings` with the given fields overridden."""
    s = copy(config.settings)
    for k, v in fields.items():
        object.__setattr__(s, k, v)
    return s


def _create_assessment(*, paid: bool, completed: bool = True, cell: str = "IA") -> str:
    db = SessionLocal()
    a = Assessment(
        completed=completed, paid=paid, archetype_cell=cell,
        riasec_scores={"R": 10, "I": 18, "A": 15, "S": 8, "E": 11, "C": 13},
        ocean_scores={"openness": 80, "conscientiousness": 70, "extraversion": 50, "agreeableness": 60, "neuroticism": 40},
        ocean_percentiles={"openness": 92, "conscientiousness": 75, "extraversion": 50, "agreeableness": 62, "neuroticism": 35},
        holland_code="IAC",
    )
    db.add(a); db.commit(); db.refresh(a)
    aid = a.id
    db.close()
    return aid


def test_report_unpaid_blocked_when_strict(monkeypatch):
    """In prod (ALLOW_FREE_REPORT=False), unpaid → 402."""
    monkeypatch.setattr(config.settings, "ALLOW_FREE_REPORT", False)
    aid = _create_assessment(paid=False)
    r = client.get(f"/api/v3/report/{aid}")
    assert r.status_code == 402


def test_report_unpaid_allowed_in_dev(monkeypatch):
    """In dev (ALLOW_FREE_REPORT=True), unpaid → 200 with is_preview=True."""
    monkeypatch.setattr(config.settings, "ALLOW_FREE_REPORT", True)
    aid = _create_assessment(paid=False)
    r = client.get(f"/api/v3/report/{aid}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["is_preview"] is True
    assert body["pdf_path"] is None
    assert body["cell_id"] == "IA"


def test_report_paid_never_preview(monkeypatch):
    """Paid → real report, is_preview=False even in dev."""
    monkeypatch.setattr(config.settings, "ALLOW_FREE_REPORT", True)
    aid = _create_assessment(paid=True)
    r = client.get(f"/api/v3/report/{aid}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["is_preview"] is False
    assert body["cell_id"] == "IA"


def test_report_paid_returns_full():
    aid = _create_assessment(paid=True)
    r = client.get(f"/api/v3/report/{aid}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cell_id"] == "IA"
    assert body["assessment_id"] == aid
    assert "deep_description_en" in body
    assert "PLACEHOLDER" not in body["deep_description_en"]  # IA is exemplar
    assert len(body["strengths_en"]) == 5
    assert len(body["growth_tips_en"]) == 5
    assert len(body["careers"]) >= 3
    # Each career has full shape
    for c in body["careers"]:
        assert "career_id" in c
        assert "indian_companies" in c
        assert "salary_inr" in c
        assert "entry" in c["salary_inr"] and "mid" in c["salary_inr"] and "senior" in c["salary_inr"]


def test_report_unknown_assessment_404():
    r = client.get("/api/v3/report/nonexistent-xyz")
    assert r.status_code == 404


def test_report_incomplete_assessment_400():
    aid = _create_assessment(paid=True, completed=False)
    r = client.get(f"/api/v3/report/{aid}")
    assert r.status_code == 400


def test_report_returns_holland_and_ocean():
    aid = _create_assessment(paid=True)
    r = client.get(f"/api/v3/report/{aid}").json()
    assert r["holland_code"] == "IAC"
    assert r["ocean_scores"]["openness"] == 80
    assert r["ocean_percentiles"]["openness"] == 92
    assert r["riasec_scores"]["I"] == 18
