"""MindIQ Backend — FastAPI Application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from routers import assessment, auth, payment, report

app = FastAPI(
    title="MindIQ API",
    description="Big Five Personality Assessment API for the Indian Market",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assessment.router)
app.include_router(auth.router)
app.include_router(payment.router)
app.include_router(report.router)


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    if settings.is_prod and settings.DEV_ACCOUNT_ENABLED:
        raise RuntimeError("DEV_ACCOUNT_ENABLED must be false in production")
    init_db()
    yield

app.router.lifespan_context = lifespan

# Also init eagerly for TestClient compatibility
init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "mindiq"}


@app.get("/api/stats")
def stats():
    """Return mock stats for social proof."""
    from database import SessionLocal
    from models import Assessment

    db = SessionLocal()
    try:
        total = db.query(Assessment).count()
        return {"total_assessments": max(total, 1247), "today_assessments": max(total % 100, 47)}
    finally:
        db.close()
