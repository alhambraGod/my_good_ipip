"""tests/test_question_bank_shim.py — verify legacy compat shim contract."""
import warnings

from questions.question_bank import (
    DIMENSIONS,
    get_all_questions,
    get_question_by_ids,
    get_question_map,
    get_question_pool,
)


def test_shim_emits_deprecation_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        get_all_questions()
        assert any(issubclass(w.category, DeprecationWarning) for w in caught), (
            "shim should emit DeprecationWarning on call"
        )


def test_shim_returns_legacy_dict_shape():
    pool = get_question_pool()
    assert len(pool) == 120  # IPIP-NEO 120
    required_keys = {"id", "text", "dimension", "reverse", "facet",
                     "scenes", "role", "difficulty", "tags", "language"}
    for q in pool:
        assert required_keys <= q.keys(), f"missing keys in {q['id']}: {required_keys - q.keys()}"
        assert q["dimension"] in DIMENSIONS, f"unknown dimension {q['dimension']!r}"


def test_shim_get_question_by_ids_resolves_subset():
    qmap = get_question_map()
    sample_ids = list(qmap.keys())[:3]
    resolved = get_question_by_ids(sample_ids)
    assert [q["id"] for q in resolved] == sample_ids
