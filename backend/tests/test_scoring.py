"""tests/test_scoring.py — RIASEC + OCEAN + Holland code scoring math."""
from services.scoring.holland_code import compute_holland_code
from services.scoring.ocean import compute_ocean_percentiles, compute_ocean_scores, score_to_percentile
from services.scoring.riasec import compute_riasec_scores


def test_compute_riasec_all_max():
    answers = {f"RIASEC_{t}{i:02d}": 5 for t in ["R", "I", "A", "S", "E", "C"] for i in (1, 3, 6, 9)}
    scores = compute_riasec_scores(answers)
    for t in ["R", "I", "A", "S", "E", "C"]:
        assert scores[t] == 20, f"{t} should be 20, got {scores[t]}"


def test_compute_riasec_partial():
    answers = {"RIASEC_I01": 5, "RIASEC_I03": 5, "RIASEC_I06": 4, "RIASEC_I09": 4}
    scores = compute_riasec_scores(answers)
    assert scores["I"] == 18  # 5+5+4+4
    assert scores["R"] == 0   # not answered


def test_compute_ocean_with_reverse():
    """Forward-keyed items with all 3s yield 60.0; reverse-keyed flip 1↔5, 2↔4."""
    from questions.ipip_neo import load_ipip_questions
    ipip = {q.id: q for q in load_ipip_questions()}
    answers = {q.id: 3 for q in ipip.values() if q.dimension == "openness"}
    scores = compute_ocean_scores(answers)
    assert scores["openness"] == 60.0  # mean = 3.0 * 20 = 60.0


def test_score_to_percentile_boundaries():
    assert 50 <= score_to_percentile(50.0) <= 60
    assert score_to_percentile(95.0) >= 98
    assert score_to_percentile(15.0) <= 5


def test_holland_code_basic():
    riasec_scores = {"R": 5, "I": 19, "A": 17, "S": 9, "E": 11, "C": 13}
    code = compute_holland_code(riasec_scores)
    assert code == "IAC"


def test_holland_code_tiebreak_alphabetical():
    riasec_scores = {"R": 10, "I": 10, "A": 10, "S": 5, "E": 5, "C": 5}
    code = compute_holland_code(riasec_scores)
    # A, I, R all tied at 10. Tiebreak: alphabetical → A, I, R
    assert code == "AIR"


def test_compute_ocean_includes_interest_pool():
    """OCEAN scoring should consider INTEREST_POOL items in addition to IPIP_NEO 120."""
    from questions.interest_pool import INTEREST_POOL
    ext_items = [q for q in INTEREST_POOL if q.dimension == "extraversion"]
    answers = {q.id: 5 for q in ext_items[:3]}
    scores = compute_ocean_scores(answers)
    # 3 items at 5 each, but reverse-keyed items will flip
    assert scores["extraversion"] > 50.0  # forward items contribute high; even with some reverse, expect > mid


# `compute_ocean_percentiles` is exported at the package level; it is verified end-to-end in Task 7
# (archetype derivation tests). The import above keeps the public-API surface visible here.
_ = compute_ocean_percentiles
