"""tests/test_archetype.py — 24-cell archetype derivation + MAST trigger."""
from services.scoring.archetype import (
    OPPOSITE_PAIRS,
    VALID_CELLS_24,
    check_mast_trigger,
    derive_archetype_cell,
    is_valid_pair,
)


def test_valid_cells_count():
    assert len(VALID_CELLS_24) == 24


def test_no_opposite_pair_is_valid():
    for pair in OPPOSITE_PAIRS:
        a, b = tuple(pair)
        assert not is_valid_pair(a, b)
        assert not is_valid_pair(b, a)
    assert not is_valid_pair("R", "R")  # same letter not valid


def test_neighbor_pairs_valid():
    assert is_valid_pair("I", "R")
    assert is_valid_pair("I", "A")
    assert is_valid_pair("S", "E")
    assert is_valid_pair("C", "R")
    assert is_valid_pair("R", "I")  # symmetry


def test_derive_cell_simple():
    cell = derive_archetype_cell({"I": 19, "A": 17, "C": 13, "R": 12, "E": 11, "S": 9}, holland_code="IAC")
    assert cell == "IA"


def test_derive_cell_skips_opposite():
    """Top 3 = I, E, A — but IE is forbidden. Should fall through to IA."""
    cell = derive_archetype_cell({"I": 19, "E": 17, "A": 15, "S": 9, "R": 8, "C": 7}, holland_code="IEA")
    assert cell == "IA"


def test_derive_cell_extreme_fallback():
    """Top 3 = R, S, I — but RS forbidden, RI valid → "RI"."""
    cell = derive_archetype_cell({"R": 19, "S": 18, "I": 5, "A": 4, "E": 3, "C": 2}, holland_code="RSI")
    assert cell == "RI"


def test_mast_trigger_positive():
    ocean_pct = {"openness": 92, "conscientiousness": 70, "extraversion": 88, "agreeableness": 86, "neuroticism": 10}
    riasec_scores = {"R": 14, "I": 16, "A": 14, "S": 14, "E": 14, "C": 14}
    assert check_mast_trigger(ocean_pct, riasec_scores) is True


def test_mast_trigger_negative_low_openness():
    ocean_pct = {"openness": 60, "conscientiousness": 70, "extraversion": 88, "agreeableness": 86, "neuroticism": 10}
    riasec_scores = {"R": 14, "I": 16, "A": 14, "S": 14, "E": 14, "C": 14}
    assert check_mast_trigger(ocean_pct, riasec_scores) is False


def test_mast_trigger_negative_high_neuroticism():
    ocean_pct = {"openness": 92, "conscientiousness": 70, "extraversion": 88, "agreeableness": 86, "neuroticism": 30}
    riasec_scores = {"R": 14, "I": 16, "A": 14, "S": 14, "E": 14, "C": 14}
    assert check_mast_trigger(ocean_pct, riasec_scores) is False


def test_mast_trigger_negative_riasec_too_skewed():
    ocean_pct = {"openness": 92, "conscientiousness": 70, "extraversion": 88, "agreeableness": 86, "neuroticism": 10}
    # One RIASEC type below threshold (8 = 40% of max 20) blocks MAST
    riasec_scores = {"R": 14, "I": 16, "A": 14, "S": 14, "E": 14, "C": 6}
    assert check_mast_trigger(ocean_pct, riasec_scores) is False


def test_valid_cells_24_distribution():
    """Each main type should have exactly 4 valid sub types (6 × 4 = 24)."""
    by_main: dict[str, int] = {}
    for cell in VALID_CELLS_24:
        by_main[cell[0]] = by_main.get(cell[0], 0) + 1
    for t in ["R", "I", "A", "S", "E", "C"]:
        assert by_main[t] == 4, f"main type {t} should have 4 sub-types, got {by_main.get(t, 0)}"
