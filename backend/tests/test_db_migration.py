"""tests/test_db_migration.py — verify v3 schema migration adds expected columns/tables."""

from sqlalchemy import inspect

from database import engine, init_db
from models import Assessment, ShortLink


def test_assessment_has_new_columns():
    init_db()
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("assessments")}
    expected_new = {
        "ocean_scores",
        "ocean_percentiles",
        "riasec_scores",
        "holland_code",
        "archetype_cell",
        "archetype_label_en",
        "archetype_rarity_pct",
        "demographic",
        "share_code",
        "payment_provider",
        "payment_txn_id",
        "payment_status",
        "payment_amount_inr",
        "report_data",
        "pdf_path",
    }
    missing = expected_new - cols
    assert not missing, f"missing columns: {missing}"


def test_short_links_table_exists():
    init_db()
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("short_links")}
    expected = {"code", "assessment_id", "target_url", "clicks", "created_at"}
    missing = expected - cols
    assert not missing, f"missing short_links columns: {missing}"


def test_legacy_columns_still_present():
    """Backward compat: legacy columns must still exist (kept nullable until Phase 3)."""
    init_db()
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("assessments")}
    legacy = {"scores", "stripe_session_id", "report_markdown", "report_html", "percentiles"}
    missing = legacy - cols
    assert not missing, f"legacy columns removed prematurely: {missing}"


def test_assessment_default_question_set_version():
    """New assessments should default to v3_45_hybrid."""
    assert Assessment.__table__.c.question_set_version.default.arg == "v3_45_hybrid"


def test_assessment_default_payment_status():
    """New assessments default to payment_status='pending'."""
    assert Assessment.__table__.c.payment_status.default.arg == "pending"


def test_indexed_columns_have_indexes():
    """Verify that columns marked index=True actually have indexes after init_db()."""
    init_db()
    inspector = inspect(engine)
    indexed: set[str] = set()
    for ix in inspector.get_indexes("assessments"):
        # Each index covers a list of column names; we only care about single-column indexes here.
        if len(ix["column_names"]) == 1:
            indexed.add(ix["column_names"][0])
    for col in ("archetype_cell", "share_code", "profile_session_token"):
        assert col in indexed, f"missing index on {col} (column should be indexed via index=True or migration helper)"
