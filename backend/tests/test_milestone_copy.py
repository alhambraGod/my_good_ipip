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
    from services.milestone_copy import _COPY_POOL_EN, _COPY_POOL_HI
    for pool in (_COPY_POOL_EN, _COPY_POOL_HI):
        for m in MILESTONE_THRESHOLDS:
            assert m in pool, f"milestone {m} missing from pool"
            assert 4 <= len(pool[m]) <= 6, (
                f"milestone {m} has {len(pool[m])} copy lines; need 4-6 per spec §3.6"
            )


def test_get_copy_hi_locale_returns_hindi_pool_strings():
    """Lang=hi should produce strings from the Hindi pool, never the English pool."""
    from services.milestone_copy import _COPY_POOL_EN, _COPY_POOL_HI
    en_set = set(s for tup in _COPY_POOL_EN.values() for s in tup)
    hi_set = set(s for tup in _COPY_POOL_HI.values() for s in tup)
    assert en_set.isdisjoint(hi_set), "Hindi pool overlaps English pool"

    for milestone in MILESTONE_THRESHOLDS:
        for seed in ("a", "b", "c", "x"):
            copy_hi = get_copy_for_milestone(milestone, seed=seed, lang="hi")
            assert copy_hi in hi_set
            copy_en = get_copy_for_milestone(milestone, seed=seed, lang="en")
            assert copy_en in en_set


def test_get_copy_unknown_lang_falls_back_to_english():
    from services.milestone_copy import _COPY_POOL_EN
    en_set = set(s for tup in _COPY_POOL_EN.values() for s in tup)
    out = get_copy_for_milestone(20, seed="test", lang="ta")  # type: ignore[arg-type]
    assert out in en_set


def test_get_copy_deterministic_within_lang():
    """Same (milestone, seed, lang) repeats; switching lang produces a different deterministic value."""
    a = get_copy_for_milestone(20, seed="X", lang="en")
    b = get_copy_for_milestone(20, seed="X", lang="en")
    c = get_copy_for_milestone(20, seed="X", lang="hi")
    assert a == b
    assert a != c
