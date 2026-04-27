"""tests/test_riasec_static_24.py — verify the curated 24 RIASEC subset."""
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
