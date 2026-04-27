import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Integer, Float, ForeignKey

from database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String, primary_key=True, default=gen_uuid)
    created_at = Column(DateTime, default=now_utc)
    answers = Column(JSON, nullable=True)
    completed = Column(Boolean, default=False)
    paid = Column(Boolean, default=False)

    # NEW v3 scoring fields (Task 8)
    ocean_scores = Column(JSON, nullable=True)            # {"openness": 0-100, ...}
    ocean_percentiles = Column(JSON, nullable=True)       # {"openness": 0-99, ...}
    riasec_scores = Column(JSON, nullable=True)           # {"R": 4-20, ...}
    holland_code = Column(String(3), nullable=True)       # "IRC"
    archetype_cell = Column(String(2), nullable=True, index=True)
    archetype_label_en = Column(String(80), nullable=True)
    archetype_rarity_pct = Column(Float, nullable=True)

    # NEW v3 demographic
    demographic = Column(JSON, nullable=True)

    # NEW v3 short link / share
    share_code = Column(String(8), unique=True, nullable=True, index=True)

    # NEW v3 payment fields
    payment_provider = Column(String, nullable=True)      # razorpay | mock | wechat | stripe
    payment_txn_id = Column(String, nullable=True)
    payment_status = Column(String, default="pending")    # pending | confirmed | failed | refunded
    payment_amount_inr = Column(Integer, nullable=True)

    # NEW v3 report (replaces report_markdown/html, but those kept nullable)
    report_data = Column(JSON, nullable=True)
    pdf_path = Column(String, nullable=True)

    # LEGACY (kept nullable for ≥1 release backward compat — TODO(phase-3): drop)
    scores = Column(JSON, nullable=True)
    percentiles = Column(JSON, nullable=True)
    stripe_session_id = Column(String, nullable=True)
    report_markdown = Column(Text, nullable=True)
    report_html = Column(Text, nullable=True)

    profile_source = Column(String, nullable=True)
    profile_data = Column(JSON, nullable=True)
    question_set_version = Column(String, nullable=False, default="v3_45_hybrid")
    question_ids = Column(JSON, nullable=True)
    selection_seed = Column(String, nullable=True)
    profile_session_token = Column(String, nullable=True, index=True)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, default=gen_uuid)
    session_token = Column(String, unique=True, index=True, nullable=False, default=gen_uuid)
    provider = Column(String, nullable=False, default="manual")
    external_id = Column(String, nullable=True, index=True)
    external_handle = Column(String, nullable=True)
    external_public_data = Column(JSON, nullable=True)
    manual_answers = Column(JSON, nullable=True)
    profile_vector = Column(JSON, nullable=True)
    is_dev_account = Column(Boolean, default=False, nullable=False)
    email = Column(String, nullable=True, unique=True, index=True)
    password_hash = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)


class ShortLink(Base):
    __tablename__ = "short_links"

    code = Column(String(8), primary_key=True)
    assessment_id = Column(String, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    target_url = Column(String, nullable=False)
    clicks = Column(Integer, default=0)
    created_at = Column(DateTime, default=now_utc)
