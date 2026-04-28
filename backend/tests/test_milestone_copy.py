"""tests/test_milestone_copy.py — milestone progress screen copy."""
import pytest

from services.milestone_copy import (
    MILESTONE_THRESHOLDS,
    get_copy_for_milestone,
    get_milestone_at,
)


def test_thresholds_match_design():
    assert MILESTONE_THRESHOLDS == (10, 20, 30, 40)


def test_milestone_at_returns_threshold_or_none():
    assert get_milestone_at(10) == 10
    assert get_milestone_at(20) == 20
    assert get_milestone_at(40) == 40
    assert get_milestone_at(15) is None
    assert get_milestone_at(45) is None
    assert get_milestone_at(0) is None


def test_get_copy_for_each_milestone():
    for m in MILESTONE_THRESHOLDS:
        copy = get_copy_for_milestone(m, seed="test-seed")
        assert isinstance(copy, str)
        assert len(copy) >= 10
        assert len(copy) <= 200


def test_get_copy_deterministic_per_seed():
    a = get_copy_for_milestone(20, seed="X")
    b = get_copy_for_milestone(20, seed="X")
    assert a == b


def test_get_copy_varies_across_seeds():
    """Different seeds should usually produce different copy (proves seed is being used)."""
    seeds = [f"seed-{i}" for i in range(20)]
    copies = {get_copy_for_milestone(20, seed=s) for s in seeds}
    assert len(copies) >= 2, "20 different seeds produced same copy; seed isn't being used"


def test_get_copy_unknown_milestone_raises():
    with pytest.raises(ValueError):
        get_copy_for_milestone(15, seed="X")


def test_get_copy_negative_milestone_raises():
    with pytest.raises(ValueError):
        get_copy_for_milestone(-1, seed="X")


def test_each_milestone_has_pool_of_at_least_three():
    """Each milestone needs a pool of multiple lines so test_get_copy_varies_across_seeds passes."""
    from services.milestone_copy import _COPY_POOL
    for m in MILESTONE_THRESHOLDS:
        assert m in _COPY_POOL, f"milestone {m} missing from _COPY_POOL"
        assert len(_COPY_POOL[m]) >= 3, f"milestone {m} has only {len(_COPY_POOL[m])} copy lines; need >=3 for variety"
