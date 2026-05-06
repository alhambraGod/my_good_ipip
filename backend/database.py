"""Database engine + session + idempotent schema migration.

Supports SQLite (dev/CI) and MySQL (stage/prod) via SQLAlchemy URL:

  sqlite:///:memory:                            ← unit tests, CI
  sqlite:///./mindprism_dev.db                  ← dev fallback (no MySQL)
  mysql+pymysql://user:pass@host:3306/dbname    ← stage / prod (Docker or host)

Notable production wiring:
  * MySQL connection pool is recycled every 30 min to avoid stale connections
    going through Cloudflare / managed PG load balancers.
  * SQLite-only `pragma foreign_keys = ON` is registered as a connect listener
    so it's a no-op on MySQL.
  * Schema migrations live in `_ensure_*_columns()` / `_ensure_*_indexes()`
    and are dialect-aware: SQLite uses PRAGMA, MySQL uses INFORMATION_SCHEMA.
"""

from __future__ import annotations

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from config import settings

# ---------------------------------------------------------------------------
# Engine + sessions
# ---------------------------------------------------------------------------

_DATABASE_URL = settings.DATABASE_URL
_IS_SQLITE = _DATABASE_URL.startswith("sqlite")
_IS_MEMORY = _DATABASE_URL.endswith(":memory:")
_IS_MYSQL = _DATABASE_URL.startswith("mysql")


def _build_engine() -> Engine:
    kwargs: dict = {}
    if _IS_SQLITE:
        kwargs["connect_args"] = {"check_same_thread": False}
        if _IS_MEMORY:
            # StaticPool: all threads (incl. TestClient handler thread) share
            # the same in-memory DB. Default SingletonThreadPool gives every
            # thread its own DB → tables vanish for the request thread.
            kwargs["poolclass"] = StaticPool
    elif _IS_MYSQL:
        # 1 day idle disconnects on most managed MySQL; recycle every 30m.
        # pre-ping checks the connection before handing it out — cheap insurance.
        kwargs["pool_pre_ping"] = True
        kwargs["pool_recycle"] = 1800
        kwargs["pool_size"] = 10
        kwargs["max_overflow"] = 20
    return create_engine(_DATABASE_URL, **kwargs)


engine: Engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@event.listens_for(engine, "connect")
def _per_connection_setup(dbapi_conn, _):
    """Run dialect-specific setup on every new connection.

    * SQLite: enable foreign-key enforcement (off by default).
    * MySQL: leave defaults; charset comes from URL (we recommend
      `?charset=utf8mb4`).
    """
    if _IS_SQLITE:
        dbapi_conn.execute("PRAGMA foreign_keys = ON")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Schema migrations (idempotent, dialect-aware)
#
# We don't use Alembic in v1 because the only schema-evolution we do is
# additive (`ADD COLUMN`, `CREATE INDEX`). When the first non-additive
# migration is needed, switch to Alembic — see ROADMAP item 1.3.
# ---------------------------------------------------------------------------

# Column DDL is parameterised on dialect — SQLite doesn't need a length on
# VARCHAR but MySQL requires a finite length on indexable VARCHAR columns.
# All column types here are SQLAlchemy-side: we render real DDL through
# `inspect()` to compare against existing columns.
_ASSESSMENT_COLUMNS: dict[str, dict[str, str]] = {
    # name → {sqlite_type, mysql_type} (pure DDL fragments, no DEFAULT)
    "profile_source":         {"sqlite": "VARCHAR",            "mysql": "VARCHAR(64)"},
    "profile_data":           {"sqlite": "JSON",               "mysql": "JSON"},
    "question_set_version":   {"sqlite": "VARCHAR",            "mysql": "VARCHAR(32)"},
    "question_ids":           {"sqlite": "JSON",               "mysql": "JSON"},
    "selection_seed":         {"sqlite": "VARCHAR",            "mysql": "VARCHAR(64)"},
    "profile_session_token":  {"sqlite": "VARCHAR",            "mysql": "VARCHAR(64)"},
    "ocean_scores":           {"sqlite": "JSON",               "mysql": "JSON"},
    "ocean_percentiles":      {"sqlite": "JSON",               "mysql": "JSON"},
    "riasec_scores":          {"sqlite": "JSON",               "mysql": "JSON"},
    "holland_code":           {"sqlite": "VARCHAR(3)",         "mysql": "VARCHAR(3)"},
    "archetype_cell":         {"sqlite": "VARCHAR(2)",         "mysql": "VARCHAR(2)"},
    "archetype_label_en":     {"sqlite": "VARCHAR(80)",        "mysql": "VARCHAR(80)"},
    "archetype_rarity_pct":   {"sqlite": "FLOAT",              "mysql": "FLOAT"},
    "demographic":            {"sqlite": "JSON",               "mysql": "JSON"},
    "share_code":             {"sqlite": "VARCHAR(8)",         "mysql": "VARCHAR(8)"},
    "payment_provider":       {"sqlite": "VARCHAR",            "mysql": "VARCHAR(32)"},
    "payment_txn_id":         {"sqlite": "VARCHAR",            "mysql": "VARCHAR(128)"},
    "payment_status":         {"sqlite": "VARCHAR",            "mysql": "VARCHAR(16)"},
    "payment_amount_inr":     {"sqlite": "INTEGER",            "mysql": "INT"},
    "report_data":            {"sqlite": "JSON",               "mysql": "JSON"},
    "pdf_path":               {"sqlite": "VARCHAR",            "mysql": "VARCHAR(255)"},
}

_USER_PROFILE_COLUMNS: dict[str, dict[str, str]] = {
    "external_id":   {"sqlite": "VARCHAR",            "mysql": "VARCHAR(128)"},
    "is_dev_account":{"sqlite": "BOOLEAN DEFAULT 0",  "mysql": "TINYINT(1) DEFAULT 0"},
    "email":         {"sqlite": "VARCHAR",            "mysql": "VARCHAR(255)"},
    "password_hash": {"sqlite": "VARCHAR",            "mysql": "VARCHAR(255)"},
    "display_name":  {"sqlite": "VARCHAR",            "mysql": "VARCHAR(128)"},
}

_ASSESSMENT_INDEXES: dict[str, str] = {
    # name → "(column [, column …])"
    "ix_assessments_archetype_cell":         "(archetype_cell)",
    "ix_assessments_profile_session_token":  "(profile_session_token)",
    "ix_assessments_share_code":             "(share_code) UNIQUE",
}


def _existing_columns(table: str) -> set[str]:
    insp = inspect(engine)
    return {c["name"] for c in insp.get_columns(table)}


def _existing_indexes(table: str) -> set[str]:
    insp = inspect(engine)
    return {ix["name"] for ix in insp.get_indexes(table)}


def _dialect_type(spec: dict[str, str]) -> str:
    return spec["mysql"] if _IS_MYSQL else spec["sqlite"]


def _ensure_columns(table: str, spec: dict[str, dict[str, str]]) -> None:
    existing = _existing_columns(table)
    with engine.begin() as conn:
        for col, types in spec.items():
            if col in existing:
                continue
            ddl = f"ALTER TABLE {table} ADD COLUMN {col} {_dialect_type(types)}"
            try:
                conn.execute(text(ddl))
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    "ADD COLUMN %s.%s failed (continuing): %s", table, col, e,
                )


def _ensure_indexes(table: str, spec: dict[str, str]) -> None:
    existing = _existing_indexes(table)
    with engine.begin() as conn:
        for name, columns in spec.items():
            if name in existing:
                continue
            unique = " UNIQUE" if columns.endswith("UNIQUE") else ""
            cols = columns.replace(" UNIQUE", "")
            ddl = f"CREATE{unique} INDEX {name} ON {table} {cols}"
            try:
                conn.execute(text(ddl))
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    "CREATE INDEX %s on %s failed (continuing): %s", name, table, e,
                )


def init_db():
    """Create tables + apply additive migrations. Safe to call repeatedly."""
    Base.metadata.create_all(bind=engine)
    _ensure_columns("assessments", _ASSESSMENT_COLUMNS)
    _ensure_columns("user_profiles", _USER_PROFILE_COLUMNS)
    _ensure_indexes("assessments", _ASSESSMENT_INDEXES)


# ---------------------------------------------------------------------------
# Backwards-compat shims for existing callers that imported the underscored
# helpers directly. New code should call init_db() only.
# ---------------------------------------------------------------------------

def _ensure_assessment_columns() -> None:
    _ensure_columns("assessments", _ASSESSMENT_COLUMNS)


def _ensure_user_profile_columns() -> None:
    _ensure_columns("user_profiles", _USER_PROFILE_COLUMNS)


def _ensure_assessment_indexes() -> None:
    _ensure_indexes("assessments", _ASSESSMENT_INDEXES)
