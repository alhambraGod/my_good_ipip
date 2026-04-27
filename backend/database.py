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
        # Pre-existing v2
        "profile_source": "ALTER TABLE assessments ADD COLUMN profile_source VARCHAR",
        "profile_data": "ALTER TABLE assessments ADD COLUMN profile_data JSON",
        "question_set_version": "ALTER TABLE assessments ADD COLUMN question_set_version VARCHAR DEFAULT 'v3_45_hybrid'",
        "question_ids": "ALTER TABLE assessments ADD COLUMN question_ids JSON",
        "selection_seed": "ALTER TABLE assessments ADD COLUMN selection_seed VARCHAR",
        "profile_session_token": "ALTER TABLE assessments ADD COLUMN profile_session_token VARCHAR",
        # NEW v3 (Task 8)
        "ocean_scores": "ALTER TABLE assessments ADD COLUMN ocean_scores JSON",
        "ocean_percentiles": "ALTER TABLE assessments ADD COLUMN ocean_percentiles JSON",
        "riasec_scores": "ALTER TABLE assessments ADD COLUMN riasec_scores JSON",
        "holland_code": "ALTER TABLE assessments ADD COLUMN holland_code VARCHAR(3)",
        "archetype_cell": "ALTER TABLE assessments ADD COLUMN archetype_cell VARCHAR(2)",
        "archetype_label_en": "ALTER TABLE assessments ADD COLUMN archetype_label_en VARCHAR(80)",
        "archetype_rarity_pct": "ALTER TABLE assessments ADD COLUMN archetype_rarity_pct FLOAT",
        "demographic": "ALTER TABLE assessments ADD COLUMN demographic JSON",
        "share_code": "ALTER TABLE assessments ADD COLUMN share_code VARCHAR(8)",
        "payment_provider": "ALTER TABLE assessments ADD COLUMN payment_provider VARCHAR",
        "payment_txn_id": "ALTER TABLE assessments ADD COLUMN payment_txn_id VARCHAR",
        "payment_status": "ALTER TABLE assessments ADD COLUMN payment_status VARCHAR DEFAULT 'pending'",
        "payment_amount_inr": "ALTER TABLE assessments ADD COLUMN payment_amount_inr INTEGER",
        "report_data": "ALTER TABLE assessments ADD COLUMN report_data JSON",
        "pdf_path": "ALTER TABLE assessments ADD COLUMN pdf_path VARCHAR",
    }

    with engine.begin() as conn:
        existing_rows = conn.execute(text("PRAGMA table_info(assessments)"))
        existing = {row[1] for row in existing_rows}

        for col, ddl in columns_sql.items():
            if col not in existing:
                conn.execute(text(ddl))

        # Idempotent unique index for share_code (only if not already present)
        existing_indexes = conn.execute(text("PRAGMA index_list(assessments)"))
        index_names = {row[1] for row in existing_indexes}
        if "ix_assessments_share_code" not in index_names:
            try:
                conn.execute(text("CREATE UNIQUE INDEX ix_assessments_share_code ON assessments(share_code)"))
            except Exception:
                pass  # may fail if existing duplicate NULLs in old data; safe to skip until v3 data lands


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
