"""tests/test_share.py — short link + OG image stub."""
from fastapi.testclient import TestClient

from database import SessionLocal
from main import app
from models import Assessment, ShortLink


client = TestClient(app)


def test_short_link_redirects():
    db = SessionLocal()
    a = Assessment(completed=True)
    db.add(a); db.commit(); db.refresh(a)
    link = ShortLink(
        code="abc12345",
        assessment_id=a.id,
        target_url="https://careerdna.in/results/abc",
    )
    db.add(link); db.commit()
    aid = a.id
    db.close()

    r = client.get("/s/abc12345", follow_redirects=False)
    assert r.status_code == 302
    assert "https://careerdna.in" in r.headers.get("location", "")


def test_short_link_unknown_404():
    r = client.get("/s/nonexistent")
    assert r.status_code == 404


def test_short_link_increments_clicks():
    db = SessionLocal()
    a = Assessment(completed=True)
    db.add(a); db.commit(); db.refresh(a)
    link = ShortLink(
        code="clicked12",
        assessment_id=a.id,
        target_url="https://careerdna.in/results/abc",
    )
    db.add(link); db.commit()
    db.close()

    client.get("/s/clicked12", follow_redirects=False)
    client.get("/s/clicked12", follow_redirects=False)

    db = SessionLocal()
    refreshed = db.query(ShortLink).filter(ShortLink.code == "clicked12").first()
    assert refreshed.clicks == 2
    db.close()


def test_og_stub_returns_png():
    db = SessionLocal()
    a = Assessment(completed=True)
    db.add(a); db.commit(); db.refresh(a)
    aid = a.id
    db.close()

    r = client.get(f"/api/share/{aid}/og.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert len(r.content) > 0


def test_og_stub_unknown_assessment_404():
    r = client.get("/api/share/nonexistent-xyz/og.png")
    assert r.status_code == 404


def test_facebook_start_unconfigured_400():
    """Without FACEBOOK_APP_ID, /auth/facebook/start returns 400."""
    r = client.get("/api/auth/facebook/start")
    assert r.status_code == 400


def test_facebook_callback_invalid_code_400():
    """Invalid auth code returns 400 (no real Facebook call in tests)."""
    r = client.post("/api/auth/facebook/callback", json={"code": "fake-code"})
    assert r.status_code == 400
