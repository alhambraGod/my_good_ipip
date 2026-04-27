"""tests/test_selector.py — verify L1.5 selector composes the right 45-item test."""
from questions.riasec_static_24 import get_riasec_static_24
from questions.selector import select_45_questions


def test_select_45_returns_exactly_45():
    answers = {"DEM_STAGE": "experienced", "DEM_TOP_PRESSURE": "money", "DEM_AGE": "25_29"}
    qs = select_45_questions(demographic_answers=answers, seed="test-seed-1")
    assert len(qs) == 45


def test_select_45_includes_all_demographic():
    qs = select_45_questions(demographic_answers={}, seed="test-seed-2")
    dem_ids = [q.id for q in qs if q.id.startswith("DEM_")]
    assert len(dem_ids) == 5


def test_select_45_includes_all_static_24_riasec():
    static_ids = {q.id for q in get_riasec_static_24()}
    qs = select_45_questions(demographic_answers={}, seed="test-seed-3")
    selected_ids = {q.id for q in qs}
    assert static_ids.issubset(selected_ids)


def test_select_45_has_16_dynamic_picks():
    qs = select_45_questions(demographic_answers={"DEM_STAGE": "student"}, seed="test-seed-4")
    interest_picks = [q for q in qs if q.id.startswith("INT_")]
    assert len(interest_picks) == 16


def test_select_45_ocean_coverage():
    qs = select_45_questions(demographic_answers={"DEM_STAGE": "founder"}, seed="test-seed-5")
    interest_picks = [q for q in qs if q.id.startswith("INT_")]
    by_dim: dict[str, int] = {}
    for q in interest_picks:
        by_dim[q.dimension] = by_dim.get(q.dimension, 0) + 1
    for d in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
        assert by_dim.get(d, 0) >= 3, f"{d} has {by_dim.get(d, 0)} items, need >=3"


def test_select_45_deterministic_per_seed():
    a = select_45_questions(demographic_answers={"DEM_STAGE": "student"}, seed="seed-X")
    b = select_45_questions(demographic_answers={"DEM_STAGE": "student"}, seed="seed-X")
    assert [q.id for q in a] == [q.id for q in b]


def test_demographic_first_then_interleaved():
    qs = select_45_questions(demographic_answers={}, seed="test-seed-7")
    # First 5 are demographic
    for i in range(5):
        assert qs[i].id.startswith("DEM_"), f"Q{i+1} should be demographic, got {qs[i].id}"
    # Last 40 should NOT be all RIASEC then all interest — must be interleaved
    last_40 = qs[5:]
    riasec_idx = [i for i, q in enumerate(last_40) if q.id.startswith("RIASEC_")]
    interest_idx = [i for i, q in enumerate(last_40) if q.id.startswith("INT_")]
    assert riasec_idx, "must have RIASEC items in last 40"
    assert interest_idx, "must have interest items in last 40"
    # Interleaved means at least one interest item appears before some RIASEC item AND vice versa
    assert max(riasec_idx) > min(interest_idx), "RIASEC and interest items should be interleaved"


def test_select_45_ocean_dims_dispersed_not_clustered():
    """Different seeds should produce different OCEAN orders within the interest block.

    Guards against accidentally removing the per-seed shuffle of the interest block
    (which prevents Neuroticism items always landing at end-of-test).
    """
    a = select_45_questions(demographic_answers={"DEM_STAGE": "experienced"}, seed="seed-A")
    b = select_45_questions(demographic_answers={"DEM_STAGE": "experienced"}, seed="seed-B")

    a_dims = [q.dimension for q in a if q.id.startswith("INT_")]
    b_dims = [q.dimension for q in b if q.id.startswith("INT_")]

    assert a_dims != b_dims, "different seeds must produce different INT-dim orders (OCEAN dispersion)"
