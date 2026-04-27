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
    """Reverse-keyed items must flip 1↔5, so forward=5 + reverse=1 both contribute as 5."""
    from questions.ipip_neo import load_ipip_questions
    ipip = [q for q in load_ipip_questions() if q.dimension == "openness"]
    answers = {q.id: (1 if q.reverse else 5) for q in ipip}
    scores = compute_ocean_scores(answers)
    assert scores["openness"] == 100.0  # all flips agree on max


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
    answers = {
        "INT_E_01": 5,  # forward-keyed extraversion
        "INT_E_03": 5,  # forward-keyed extraversion
        "INT_E_06": 5,  # forward-keyed extraversion
    }
    scores = compute_ocean_scores(answers)
    # 3 forward-keyed items at 5 → mean 5.0 → score 100.0
    assert scores["extraversion"] == 100.0


def test_compute_ocean_percentiles_maps_all_dims():
    pct = compute_ocean_percentiles({
        "openness": 95.0,
        "conscientiousness": 50.0,
        "extraversion": 25.0,
        "agreeableness": 70.0,
        "neuroticism": 15.0,
    })
    assert pct["openness"] == 99
    # 25.0 falls in (20.0, 30.0) bucket → percentile = 8
    assert pct["extraversion"] == 8
    assert pct["conscientiousness"] == 58
    assert 75 <= pct["agreeableness"] <= 88
    # 15.0 falls in (0.0, 20.0) bucket → percentile = 2
    assert pct["neuroticism"] == 2
