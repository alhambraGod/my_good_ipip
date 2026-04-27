"""OCEAN scoring with reverse-key handling and percentile mapping.

OCEAN items come from BOTH the IPIP-NEO 120 bank and the curated INTEREST_POOL —
both are factored into a domain's average score.
"""

from __future__ import annotations

from collections import defaultdict

from questions.interest_pool import INTEREST_POOL
from questions.ipip_neo import OCEAN_DOMAINS, load_ipip_questions

# Approximate IPIP-NEO percentile lookup (kept from legacy scoring; later replaced by IRT calibration).
PERCENTILE_TABLE: dict[tuple[float, float], int] = {
    (0.0, 20.0): 2,
    (20.0, 30.0): 8,
    (30.0, 35.0): 15,
    (35.0, 40.0): 25,
    (40.0, 45.0): 35,
    (45.0, 50.0): 50,
    (50.0, 55.0): 58,
    (55.0, 60.0): 68,
    (60.0, 65.0): 75,
    (65.0, 70.0): 82,
    (70.0, 75.0): 88,
    (75.0, 80.0): 93,
    (80.0, 85.0): 96,
    (85.0, 90.0): 98,
    (90.0, 101.0): 99,
}


def score_to_percentile(score: float) -> int:
    """Map a 0-100 OCEAN score to an approximate population percentile (1-99)."""
    for (lo, hi), pct in PERCENTILE_TABLE.items():
        if lo <= score < hi:
            return pct
    return 50


def _build_question_index() -> dict:
    """Combined index of {id: Question} for all OCEAN-scoring items (IPIP + INTEREST_POOL)."""
    index: dict = {}
    for q in load_ipip_questions():
        index[q.id] = q
    for q in INTEREST_POOL:
        index[q.id] = q
    return index


def compute_ocean_scores(answers: dict[str, int]) -> dict[str, float]:
    """Compute OCEAN domain scores (0-100 scale).

    Args:
      answers: {question_id: 1-5 likert}. Mix of IPIP_* and INT_* IDs accepted.

    Returns:
      {"openness": 0-100, "conscientiousness": 0-100, ...}.
      Domains with zero answers default to 50.0 (neutral).
    """
    qindex = _build_question_index()
    sums: dict[str, list[float]] = defaultdict(list)

    for qid, value in answers.items():
        q = qindex.get(qid)
        if q is None or q.dimension not in OCEAN_DOMAINS:
            continue
        if not (1 <= value <= 5):
            raise ValueError(f"OCEAN answer for {qid} must be 1-5, got {value}")
        scored = (6 - value) if q.reverse else value
        sums[q.dimension].append(scored)

    scores: dict[str, float] = {}
    for dim in OCEAN_DOMAINS:
        vals = sums.get(dim, [])
        if not vals:
            scores[dim] = 50.0
        else:
            mean = sum(vals) / len(vals)
            scores[dim] = round(mean * 20, 1)  # scale 1-5 → 0-100

    return scores


def compute_ocean_percentiles(scores: dict[str, float]) -> dict[str, int]:
    """Map a {dim: score} dict to {dim: percentile}."""
    return {dim: score_to_percentile(s) for dim, s in scores.items()}
