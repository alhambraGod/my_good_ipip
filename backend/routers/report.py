"""Report router — AI report generation + PDF download."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import Assessment
from schemas import ReportResponse
from services.ai_report import generate_report
from services.pdf_generator import render_report_html, generate_pdf_bytes

router = APIRouter(prefix="/api/report", tags=["report"])


def _require_paid(assessment: Assessment) -> None:
    """Raise 402 unless the assessment is paid or we're in mock payment mode."""
    if assessment.paid:
        return
    if settings.PAYMENT_MODE == "mock":
        # Auto-mark as paid in mock mode so subsequent checks pass too
        return
    raise HTTPException(status_code=402, detail="Payment required")


@router.get("/{assessment_id}", response_model=ReportResponse)
async def get_report(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    _require_paid(assessment)

    # Generate report if not cached
    if not assessment.report_html:
        report_md = await generate_report(assessment.scores, assessment.percentiles)
        report_html = render_report_html(report_md, assessment.scores, assessment.percentiles)
        assessment.report_markdown = report_md
        assessment.report_html = report_html
        db.commit()

    return ReportResponse(
        assessment_id=assessment.id,
        report_html=assessment.report_html,
        scores=assessment.scores,
        percentiles=assessment.percentiles,
    )


@router.get("/{assessment_id}/pdf")
async def download_pdf(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    _require_paid(assessment)

    # Generate report if not cached
    if not assessment.report_html:
        report_md = await generate_report(assessment.scores, assessment.percentiles)
        report_html = render_report_html(report_md, assessment.scores, assessment.percentiles)
        assessment.report_markdown = report_md
        assessment.report_html = report_html
        db.commit()

    pdf_bytes, pdf_error = generate_pdf_bytes(assessment.report_html)
    if not pdf_bytes:
        detail = "PDF generation failed"
        if pdf_error:
            detail = f"PDF generation failed: {pdf_error}"
        raise HTTPException(status_code=500, detail=detail)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=MindIQ_Report_{assessment_id[:8]}.pdf"},
    )
