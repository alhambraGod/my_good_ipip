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


def test_derive_profile_tags():
    answers = {"DEM_STAGE": "experienced", "DEM_TOP_PRESSURE": "money"}
    tags = derive_profile_tags(answers)
    assert "experienced" in tags
    assert "EMI" in tags or "money" in tags


def test_interest_pool_size_and_shape():
    assert len(INTEREST_POOL) >= 30
    by_dim: dict[str, int] = {}
    for q in INTEREST_POOL:
        by_dim[q.dimension] = by_dim.get(q.dimension, 0) + 1
    for d in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
        assert by_dim.get(d, 0) >= 5, f"only {by_dim.get(d, 0)} items for {d}"
