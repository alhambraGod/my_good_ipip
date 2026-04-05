from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_assessment_columns() -> None:
    columns_sql = {
        "profile_source": "ALTER TABLE assessments ADD COLUMN profile_source VARCHAR",
        "profile_data": "ALTER TABLE assessments ADD COLUMN profile_data JSON",
        "question_set_version": "ALTER TABLE assessments ADD COLUMN question_set_version VARCHAR",
        "question_ids": "ALTER TABLE assessments ADD COLUMN question_ids JSON",
        "selection_seed": "ALTER TABLE assessments ADD COLUMN selection_seed VARCHAR",
        "profile_session_token": "ALTER TABLE assessments ADD COLUMN profile_session_token VARCHAR",
    }

    with engine.begin() as conn:
        existing_rows = conn.execute(text("PRAGMA table_info(assessments)"))
        existing = {row[1] for row in existing_rows}

        for col, ddl in columns_sql.items():
            if col not in existing:
                conn.execute(text(ddl))


def _ensure_user_profile_columns() -> None:
    columns_sql = {
        "external_id": "ALTER TABLE user_profiles ADD COLUMN external_id VARCHAR",
        "is_dev_account": "ALTER TABLE user_profiles ADD COLUMN is_dev_account BOOLEAN DEFAULT 0",
        "email": "ALTER TABLE user_profiles ADD COLUMN email VARCHAR",
        "password_hash": "ALTER TABLE user_profiles ADD COLUMN password_hash VARCHAR",
        "display_name": "ALTER TABLE user_profiles ADD COLUMN display_name VARCHAR",
    }

    with engine.begin() as conn:
        existing_rows = conn.execute(text("PRAGMA table_info(user_profiles)"))
        existing = {row[1] for row in existing_rows}

        for col, ddl in columns_sql.items():
            if col not in existing:
                conn.execute(text(ddl))


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_assessment_columns()
    _ensure_user_profile_columns()
