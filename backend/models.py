import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean

from database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String, primary_key=True, default=gen_uuid)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    answers = Column(JSON, nullable=True)
    scores = Column(JSON, nullable=True)  # {dimension: score}
    percentiles = Column(JSON, nullable=True)
    completed = Column(Boolean, default=False)
    paid = Column(Boolean, default=False)
    stripe_session_id = Column(String, nullable=True)
    report_markdown = Column(Text, nullable=True)
    report_html = Column(Text, nullable=True)

    profile_source = Column(String, nullable=True)
    profile_data = Column(JSON, nullable=True)
    question_set_version = Column(String, nullable=False, default="v2_100")
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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
