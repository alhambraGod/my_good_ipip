from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@event.listens_for(engine, "connect")
def _sqlite_enable_fk(dbapi_conn, _):
    """SQLite doesn't enable FK enforcement by default; do it per connection."""
    dbapi_conn.execute("PRAGMA foreign_keys = ON")


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


def _ensure_assessment_indexes() -> None:
    """Create indexes on existing tables if they don't exist (upgrade path).

    `Base.metadata.create_all` only creates indexes for FRESH tables;
    pre-existing tables that gain a new `index=True` column don't get the
    index retro-fitted. We do that explicitly here.
    """
    indexes_sql = {
        "ix_assessments_archetype_cell": "CREATE INDEX ix_assessments_archetype_cell ON assessments(archetype_cell)",
        "ix_assessments_profile_session_token": "CREATE INDEX ix_assessments_profile_session_token ON assessments(profile_session_token)",
        "ix_assessments_share_code": "CREATE UNIQUE INDEX ix_assessments_share_code ON assessments(share_code)",
    }

    with engine.begin() as conn:
        existing_indexes = {row[1] for row in conn.execute(text("PRAGMA index_list(assessments)"))}
        for name, ddl in indexes_sql.items():
            if name in existing_indexes:
                continue
            try:
                conn.execute(text(ddl))
            except Exception as e:
                # SQLite allows multiple NULLs in UNIQUE indexes, so duplicate-NULL is NOT a real risk;
                # the only realistic failures here are concurrent migrations or a real bug.
                # Log and continue rather than abort startup.
                import logging
                logging.getLogger(__name__).warning(
                    "Index creation failed for %s (will retry next startup): %s", name, e,
                )


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
    _ensure_assessment_indexes()
