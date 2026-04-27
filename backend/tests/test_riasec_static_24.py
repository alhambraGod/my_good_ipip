"""tests/test_riasec_static_24.py — verify the curated 24 RIASEC subset."""
import pytest

from questions.holland_riasec import RIASEC_TYPES, load_riasec_questions
from questions.riasec_static_24 import get_riasec_static_24


def test_static_24_size_and_coverage():
    selected = get_riasec_static_24()
    assert len(selected) == 24, f"expected 24, got {len(selected)}"

    by_dim: dict[str, int] = {}
    for q in selected:
        by_dim[q.dimension] = by_dim.get(q.dimension, 0) + 1

    for t in RIASEC_TYPES:
        assert by_dim[t] == 4, f"expected 4 for {t}, got {by_dim.get(t, 0)}"


def test_static_24_is_deterministic():
    a = get_riasec_static_24()
    b = get_riasec_static_24()
    assert [q.id for q in a] == [q.id for q in b]


def test_static_24_subset_of_60():
    selected = get_riasec_static_24()
    full_60 = load_riasec_questions()
    full_ids = {q.id for q in full_60}
    for q in selected:
        assert q.id in full_ids, f"{q.id} not in 60-bank"


def test_static_24_unique_ids():
    """No duplicate IDs in the curated set."""
    selected = get_riasec_static_24()
    ids = [q.id for q in selected]
    assert len(ids) == len(set(ids)), f"duplicate IDs detected: {ids}"


def test_static_24_grouped_by_riasec_order():
    """Lock the R-I-A-S-E-C ordering — Task 5 selector relies on this implicit contract."""
    selected = get_riasec_static_24()
    dims_in_order = [q.dimension for q in selected]
    assert dims_in_order == ["R"]*4 + ["I"]*4 + ["A"]*4 + ["S"]*4 + ["E"]*4 + ["C"]*4


def test_static_24_raises_on_missing_curated_id(monkeypatch):
    """Defensive check: if a curated ID disappears from the 60-bank, raise loudly."""
    from questions import riasec_static_24

    riasec_static_24.get_riasec_static_24.cache_clear()
    monkeypatch.setitem(
        riasec_static_24.STATIC_24_ITEM_IDS, "R",
        ("RIASEC_R01", "RIASEC_R03", "RIASEC_R05", "RIASEC_R99"),
    )
    with pytest.raises(ValueError, match="RIASEC_R99"):
        riasec_static_24.get_riasec_static_24()
    riasec_static_24.get_riasec_static_24.cache_clear()
