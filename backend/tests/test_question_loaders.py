"""tests/test_question_loaders.py"""
import pytest
from questions.models import Question, Instrument, ResponseType


def test_question_construction():
    q = Question(
        id="RIASEC_R01",
        text_en="I like fixing mechanical problems.",
        instrument=Instrument.RIASEC,
        dimension="R",
        reverse=False,
        response_type=ResponseType.LIKERT_5,
    )
    assert q.id == "RIASEC_R01"
    assert q.dimension == "R"
    assert q.weight == 1.0  # default


from questions.holland_riasec import load_riasec_questions, RIASEC_TYPES


def test_load_riasec_60():
    qs = load_riasec_questions()
    assert len(qs) == 60, f"expected 60 RIASEC items, got {len(qs)}"
    by_dim: dict[str, int] = {}
    for q in qs:
        by_dim[q.dimension] = by_dim.get(q.dimension, 0) + 1
    for t in RIASEC_TYPES:
        assert by_dim[t] == 10, f"expected 10 items for {t}, got {by_dim.get(t, 0)}"
    # all forward-keyed (Holland convention)
    assert all(not q.reverse for q in qs)
    assert all(q.instrument == Instrument.RIASEC for q in qs)
    # ID format: RIASEC_<raw_json_id> e.g. RIASEC_R01
    for q in qs:
        assert q.id.startswith("RIASEC_"), f"id {q.id} should start with RIASEC_"


from questions.ipip_neo import load_ipip_questions, OCEAN_DOMAINS


def test_load_ipip_120():
    qs = load_ipip_questions()
    assert len(qs) == 120
    by_dim: dict[str, int] = {}
    for q in qs:
        by_dim[q.dimension] = by_dim.get(q.dimension, 0) + 1
    for d in OCEAN_DOMAINS:
        assert by_dim[d] == 24, f"expected 24 items for {d}, got {by_dim.get(d, 0)}"
    # mix of forward and reverse keyed
    forward = sum(1 for q in qs if not q.reverse)
    reverse = sum(1 for q in qs if q.reverse)
    assert forward > 0 and reverse > 0
    assert all(q.instrument == Instrument.IPIP for q in qs)
    assert all(q.facet for q in qs), "every IPIP item should have a facet"
    # ID format: IPIP_<raw_json_id> e.g. IPIP_N1_1
    for q in qs:
        assert q.id.startswith("IPIP_"), f"id {q.id} should start with IPIP_"
