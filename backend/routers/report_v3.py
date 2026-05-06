"""v3 Report router — paid-only deep report, with dev preview gating.

Behaviour matrix:

  ┌────────────────────────┬──────────────────────────┬──────────────────────────┐
  │ assessment.paid        │  ALLOW_FREE_REPORT=False │  ALLOW_FREE_REPORT=True   │
  │                        │  (prod default)          │  (dev default)            │
  ├────────────────────────┼──────────────────────────┼──────────────────────────┤
  │ True                   │  200 + full report       │  200 + full report        │
  │ False                  │  402 Payment Required    │  200 + is_preview=True    │
  │                        │                          │  (no PDF, watermark)      │
  └────────────────────────┴──────────────────────────┴──────────────────────────┘

This lets QA in dev see the report without configuring Razorpay test
creds, while prod always strictly requires payment. Operator override
either way via `ALLOW_FREE_REPORT=true|false` env var.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import config  # late-binding so monkeypatch tests can override `settings`
from content.careers import get_careers_for_cell
from content.cells import get_cell_content
from database import get_db
from models import Assessment
from schemas import V3ReportResponse


router = APIRouter(prefix="/api/v3/report", tags=["report_v3"])


@router.get("/{assessment_id}", response_model=V3ReportResponse)
def get_report(assessment_id: str, db: Session = Depends(get_db)):
    """Full report.

    * If `assessment.paid` is True → real report.
    * Else if `ALLOW_FREE_REPORT` is True → preview with `is_preview=True`,
      `pdf_path=None`, and the rendered cell content (so dev can see the
      experience without paying).
    * Else (prod default) → 402 Payment Required.
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.completed:
        raise HTTPException(status_code=400, detail="Assessment not yet completed")

    if not assessment.paid and not config.settings.ALLOW_FREE_REPORT:
        raise HTTPException(status_code=402, detail="Payment required")

    cell = get_cell_content(assessment.archetype_cell)
    careers_full = get_careers_for_cell(assessment.archetype_cell)
    careers_dump = [
        {
            "career_id": c.career_id,
            "name_en": c.name_en,
            "name_hi": c.name_hi,
            "tagline_en": c.tagline_en,
            "why_match": c.why_match,
            "indian_companies": c.indian_companies,
            "salary_inr": {
                "entry": c.salary_inr.entry,
                "mid": c.salary_inr.mid,
                "senior": c.salary_inr.senior,
            },
            "education_path": c.education_path,
            "city_distribution": c.city_distribution,
        }
        for c in careers_full
    ]

    is_preview = (not assessment.paid) and config.settings.ALLOW_FREE_REPORT

    return V3ReportResponse(
        assessment_id=assessment.id,
        cell_id=assessment.archetype_cell,
        cell_label_en=cell.label_en,
        cell_label_hi=cell.label_hi,
        slogan_en=cell.slogan_en,
        deep_description_en=cell.deep_description_en,
        strengths_en=cell.strengths_en,
        growth_tips_en=cell.growth_tips_en,
        ocean_scores=assessment.ocean_scores or {},
        ocean_percentiles=assessment.ocean_percentiles or {},
        holland_code=assessment.holland_code or "",
        riasec_scores=assessment.riasec_scores or {},
        rarity_pct=cell.rarity_pct,
        is_mast_trigger=False,
        careers=careers_dump,
        pdf_path=None if is_preview else assessment.pdf_path,
        is_preview=is_preview,
    )
