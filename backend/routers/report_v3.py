"""v3 Report router — paid-only full report composing cell + careers + OCEAN."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from content.careers import get_careers_for_cell
from content.cells import get_cell_content
from database import get_db
from models import Assessment
from schemas import V3ReportResponse


router = APIRouter(prefix="/api/v3/report", tags=["report_v3"])


def _require_paid(assessment: Assessment) -> None:
    if not assessment.paid:
        raise HTTPException(status_code=402, detail="Payment required")


@router.get("/{assessment_id}", response_model=V3ReportResponse)
def get_report(assessment_id: str, db: Session = Depends(get_db)):
    """Full paid report: deep description + strengths + growth tips + OCEAN + 5+ careers."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not assessment.completed:
        raise HTTPException(status_code=400, detail="Assessment not yet completed")
    _require_paid(assessment)

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
        is_mast_trigger=False,  # MAST trigger evaluated at submit; future enhancement to persist this on the assessment row
        careers=careers_dump,
        pdf_path=assessment.pdf_path,
    )
