"""DEPRECATED: legacy 100-item Big-Five-only question bank.

This module is kept as a compat shim during the v2 → v3 transition.
Phase 3 of the redesign will remove all callers; Phase 4 will delete this file.

For new code, use:
  - questions.holland_riasec.load_riasec_questions
  - questions.ipip_neo.load_ipip_questions
  - questions.demographic.DEMOGRAPHIC_QUESTIONS
  - questions.interest_pool.INTEREST_POOL
  - questions.selector.select_45_questions
"""

from __future__ import annotations

import warnings

from questions.ipip_neo import OCEAN_DOMAINS as DIMENSIONS  # re-export

_DEPRECATION_NOTICE = (
    "questions.question_bank.* is deprecated. "
    "Use questions.{holland_riasec, ipip_neo, demographic, interest_pool, selector} instead."
)


def get_question_pool(version: str | None = None) -> list[dict]:
    """DEPRECATED. Returns IPIP-NEO 120 in legacy dict shape."""
    warnings.warn(_DEPRECATION_NOTICE, DeprecationWarning, stacklevel=2)
    return _build_legacy_dict_pool()


def get_question_map() -> dict[str, dict]:
    """DEPRECATED. Returns {id: legacy_dict} keyed by IPIP question ID."""
    warnings.warn(_DEPRECATION_NOTICE, DeprecationWarning, stacklevel=2)
    return {q["id"]: q for q in _build_legacy_dict_pool()}


def get_question_by_ids(ids: list[str]) -> list[dict]:
    """DEPRECATED. Resolves IDs against the legacy IPIP pool."""
    warnings.warn(_DEPRECATION_NOTICE, DeprecationWarning, stacklevel=2)
    qmap = get_question_map()
    return [qmap[qid] for qid in ids if qid in qmap]


def get_all_questions() -> list[dict]:
    """DEPRECATED. Returns the full IPIP 120 pool."""
    warnings.warn(_DEPRECATION_NOTICE, DeprecationWarning, stacklevel=2)
    return _build_legacy_dict_pool()


def _build_legacy_dict_pool() -> list[dict]:
    """Map IPIP-NEO 120 → legacy dict shape used by personalization.py / scoring_legacy.py.

    Legacy shape per item:
      {"id", "text", "dimension", "reverse", "facet", "scenes", "role", "difficulty", "tags", "language"}
    """
    from questions.ipip_neo import load_ipip_questions

    out: list[dict] = []
    for q in load_ipip_questions():
        out.append({
            "id": q.id,
            "text": q.text_en,
            "dimension": q.dimension,
            "reverse": q.reverse,
            "facet": q.facet or q.id,
            "scenes": q.scenes,
            "role": q.role,
            "difficulty": q.difficulty,
            "tags": q.tags,
            "language": "en",
        })
    return out
