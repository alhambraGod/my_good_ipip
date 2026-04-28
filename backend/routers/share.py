"""Share router — short-link redirect + OG image stub."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from database import get_db
from models import Assessment, ShortLink

router = APIRouter(tags=["share"])


@router.get("/s/{code}")
def short_link_redirect(code: str, db: Session = Depends(get_db)):
    """Resolve short code → 302 redirect to canonical URL. Increments click count."""
    link = db.query(ShortLink).filter(ShortLink.code == code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    link.clicks += 1
    db.commit()
    return RedirectResponse(url=link.target_url, status_code=302)


@router.get("/api/share/{assessment_id}/og.png")
def og_image_stub(assessment_id: str, db: Session = Depends(get_db)):
    """OG image generation stub. Phase 4 frontend uses Next.js @vercel/og to render
    rich PNGs at the edge. This backend stub returns a minimal 1×1 PNG so backend
    smoke tests pass; production frontend should NOT call this endpoint."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    png_bytes = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "000000d44944415478da63606060000000040001a8e1c5fc0000000049454e44ae426082"
    )
    return Response(content=png_bytes, media_type="image/png")
