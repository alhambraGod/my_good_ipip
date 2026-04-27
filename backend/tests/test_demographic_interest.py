"""tests/test_demographic_interest.py"""
from questions.demographic import DEMOGRAPHIC_QUESTIONS, derive_profile_tags
from questions.interest_pool import INTEREST_POOL
from questions.models import Instrument


def test_demographic_count_and_shape():
    assert len(DEMOGRAPHIC_QUESTIONS) == 5
    for q in DEMOGRAPHIC_QUESTIONS:
        assert q.instrument == Instrument.DEMOGRAPHIC
        assert q.options is not None and len(q.options) >= 3
        assert q.id.startswith("DEM_")


def test_derive_profile_tags_full_paths():
    tags = derive_profile_tags({
        "DEM_STAGE": "experienced",
        "DEM_TOP_PRESSURE": "money",
        "DEM_AGE": "25_29",
    })
    assert "experienced" in tags
    assert "work-stress" in tags
    assert "mid-career" in tags
    assert "EMI" in tags and "money" in tags and "financial-stress" in tags
    assert "millennial-early" in tags


def test_derive_profile_tags_handles_unknowns_and_empty():
    assert derive_profile_tags({}) == []
    assert derive_profile_tags({"DEM_STAGE": "bogus"}) == []
    assert derive_profile_tags({"DEM_TOP_PRESSURE": "curious"}) == []  # by design: no bias for casual visitors


def test_interest_pool_size_and_shape():
    assert len(INTEREST_POOL) >= 30
    by_dim: dict[str, int] = {}
    for q in INTEREST_POOL:
        by_dim[q.dimension] = by_dim.get(q.dimension, 0) + 1
    for d in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
        assert by_dim.get(d, 0) >= 5, f"only {by_dim.get(d, 0)} items for {d}"


def test_interest_pool_field_consistency():
    """Verify every item has consistent metadata + IDs are well-formed."""
    assert all(q.id.startswith("INT_") for q in INTEREST_POOL), "all IDs prefixed"
    assert all(q.tags for q in INTEREST_POOL), "selector relies on non-empty tags"
    assert all(q.role == "scene" for q in INTEREST_POOL), "all role=scene"
    assert all(q.instrument == Instrument.INTEREST for q in INTEREST_POOL)
    reverse_count = sum(1 for q in INTEREST_POOL if q.reverse)
    assert reverse_count >= 5, f"need ≥5 reverse-keyed items, got {reverse_count}"


def test_interest_pool_tags_reachable_from_demographic():
    """Every tag used by INTEREST_POOL items must be producible by some demographic answer set.

    This guards against dead tags (typos or copy-paste leftovers that the selector can never match).
    Phase 2 may add new demographic questions — when it does, extend the candidate set below.
    """
    reachable: set[str] = set()
    stage_values = ["student", "fresher", "experienced", "switcher", "founder"]
    pressure_values = ["career", "family", "money", "self_doubt", "curious"]
    age_values = ["15_19", "20_24", "25_29", "30_34", "35_plus"]
    for s in stage_values:
        for p in pressure_values:
            for a in age_values:
                reachable.update(derive_profile_tags({
                    "DEM_STAGE": s, "DEM_TOP_PRESSURE": p, "DEM_AGE": a,
                }))

    pool_tags: set[str] = set()
    for q in INTEREST_POOL:
        pool_tags.update(q.tags)

    unreachable = pool_tags - reachable
    # Some tags are intentionally never reachable from current demographics
    # (placeholders for future demographic Qs in Phase 2). Whitelist here:
    expected_dead = {"tradition", "self-driven", "remote", "career"}
    surprises = unreachable - expected_dead
    assert not surprises, (
        f"Pool item tags {surprises} aren't reachable from any demographic answer. "
        f"Either fix the typo or add to expected_dead whitelist."
    )
